#!/usr/bin/env python3
"""
CS153 Lab 3 Autograder — Shared Memory + Memory Translation Syscall
====================================================================
Grades an xv6 repo on three items (30 points total):

  * shm_open()       ... 15 pts  (shm_cnt: two forked processes share a page,
                                  final counter must reach 20000)
  * shm_close()      ...  5 pts  (grader test: open -> write pattern -> close ->
                                  reopen must yield a FRESH page, and the kernel
                                  must not panic when the process exits)
  * check_address()  ... 10 pts  (grader test: mapped user address prints
                                  physical addr / user-kernel / read-write info;
                                  unmapped address returns 1)

Usage:
    python3 autograder.py [path-to-xv6-repo]      # default: current directory
    python3 autograder.py --keep                  # keep grader files after run
    python3 autograder.py --qemu qemu-system-i386 # override qemu binary

The grader injects its own test programs (_gr_close, _gr_addr) into the build,
boots xv6 in QEMU (no graphics), drives the shell, parses the output, and then
restores the repo to its original state.

Requirements: python3, make, gcc (32-bit capable), qemu-system-i386.
No third-party Python packages needed.
"""

import argparse
import os
import re
import select
import shutil
import subprocess
import sys
import time

# ---------------------------------------------------------------------------
# Points
# ---------------------------------------------------------------------------
PTS_SHM_OPEN = 15
PTS_SHM_CLOSE = 5
PTS_CHECK_ADDR = 10
PTS_TOTAL = PTS_SHM_OPEN + PTS_SHM_CLOSE + PTS_CHECK_ADDR

# CFLAGS fallback used only if the stock build fails (modern gcc trips
# -Werror on pre-existing xv6 warnings that have nothing to do with the lab).
FALLBACK_CFLAGS = ("-fno-pic -static -fno-builtin -fno-strict-aliasing -O2 "
                   "-Wall -MD -ggdb -m32 -fno-omit-frame-pointer "
                   "-fno-stack-protector -fno-pie -no-pie")

# ---------------------------------------------------------------------------
# Grader-owned test programs (injected into the student's build)
# ---------------------------------------------------------------------------
GR_CLOSE_C = r"""
// Autograder test for shm_close(). Do not modify — this file is regenerated.
#include "types.h"
#include "stat.h"
#include "user.h"

#define SEG_ID 7
#define PAT 0x5A

int
main(void)
{
  char *p1 = 0, *p2 = 0;
  int i, survivors = 0;

  if (shm_open(SEG_ID, &p1) < 0 || p1 == 0) {
    printf(1, "GR_CLOSE: OPEN_FAIL\n");
    exit();
  }
  for (i = 0; i < 128; i++)
    p1[i] = PAT;

  // refcnt should drop to 0 here and the table entry must be cleared.
  shm_close(SEG_ID);

  // Reopening the same id must now create a brand-new segment. If the table
  // entry was not cleared, we get mapped back to the old frame and the
  // pattern survives.
  if (shm_open(SEG_ID, &p2) < 0 || p2 == 0) {
    printf(1, "GR_CLOSE: REOPEN_FAIL\n");
    exit();
  }
  for (i = 0; i < 128; i++)
    if (p2[i] == PAT)
      survivors++;

  if (survivors == 128)
    printf(1, "GR_CLOSE: STALE_ENTRY\n");   // close() did not clear the table
  else
    printf(1, "GR_CLOSE: OK\n");

  shm_close(SEG_ID);
  // exit() must not panic (a kfree inside shm_close typically double-frees
  // the frame when freevm runs here).
  exit();
}
"""

GR_ADDR_C = r"""
// Autograder test for check_address(). Do not modify — this file is regenerated.
#include "types.h"
#include "stat.h"
#include "user.h"

int gr_global = 123;

int
main(void)
{
  int rmapped, runmapped;

  printf(1, "GR_ADDR: BEGIN_MAPPED\n");
  rmapped = check_address((int)&gr_global);   // a mapped, writable user page
  printf(1, "GR_ADDR: END_MAPPED ret=%d\n", rmapped);

  printf(1, "GR_ADDR: BEGIN_UNMAPPED\n");
  runmapped = check_address(0x30000000);      // far beyond any mapping
  printf(1, "GR_ADDR: END_UNMAPPED ret=%d\n", runmapped);

  exit();
}
"""


# ---------------------------------------------------------------------------
# Minimal expect-style driver for qemu -nographic over pipes
# ---------------------------------------------------------------------------
class QemuSession:
    def __init__(self, repo, qemu_bin, boot_timeout=30):
        self.log = ""
        cmd = [
            qemu_bin, "-nographic",
            "-drive", "file=fs.img,index=1,media=disk,format=raw",
            "-drive", "file=xv6.img,index=0,media=disk,format=raw",
            "-smp", "2", "-m", "512",
        ]
        self.proc = subprocess.Popen(
            cmd, cwd=repo,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        os.set_blocking(self.proc.stdout.fileno(), False)
        self.boot_timeout = boot_timeout

    def _read_available(self):
        try:
            chunk = self.proc.stdout.read()
            if chunk:
                self.log += chunk.decode("utf-8", errors="replace")
        except (BlockingIOError, TypeError):
            pass

    def expect(self, pattern, timeout, start=0):
        """Wait until regex `pattern` appears in output AFTER offset `start`."""
        deadline = time.time() + timeout
        rx = re.compile(pattern)
        while time.time() < deadline:
            if rx.search(self.log, start):
                return True
            if self.proc.poll() is not None:
                self._read_available()
                return bool(rx.search(self.log, start))
            select.select([self.proc.stdout], [], [], 0.2)
            self._read_available()
        return bool(rx.search(self.log, start))

    def wait_for_shell(self):
        return self.expect(r"init: starting sh", self.boot_timeout) and \
               self.expect(r"\$ ", 10)

    def run(self, command, done_pattern, timeout):
        """Send a shell command; wait for done_pattern; return captured text."""
        start = len(self.log)
        self.proc.stdin.write((command + "\n").encode())
        self.proc.stdin.flush()
        self.expect(done_pattern, timeout, start=start)
        # Give trailing output (e.g. a panic right after) a moment to arrive.
        time.sleep(0.5)
        self._read_available()
        return self.log[start:]

    def close(self):
        try:
            self.proc.kill()
            self.proc.wait(timeout=5)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Build management
# ---------------------------------------------------------------------------
def patch_makefile(repo, include_addr_test):
    """Backup the Makefile and register the grader programs in it."""
    mk = os.path.join(repo, "Makefile")
    shutil.copy2(mk, mk + ".gradebak")
    with open(mk) as f:
        text = f.read()

    progs = "\t_gr_close\\\n" + ("\t_gr_addr\\\n" if include_addr_test else "")
    extra = " gr_close.c" + (" gr_addr.c" if include_addr_test else "")

    # Add to UPROGS (anchor on _shm_cnt which the starter Makefile ships with).
    text, n1 = re.subn(r"(\t_shm_cnt\\\n)", r"\1" + progs, text, count=1)
    # Add sources to EXTRA so `make clean`/dist targets stay coherent.
    text, n2 = re.subn(r"(uspinlock\.c shm_cnt\.c)", r"\1" + extra, text, count=1)
    if n1 != 1:
        raise RuntimeError("Could not find _shm_cnt in Makefile UPROGS; "
                           "is this the Lab 3 starter repo?")
    with open(mk, "w") as f:
        f.write(text)


def restore_repo(repo, keep):
    mk = os.path.join(repo, "Makefile")
    if os.path.exists(mk + ".gradebak"):
        shutil.move(mk + ".gradebak", mk)
    if not keep:
        for fn in ("gr_close.c", "gr_addr.c"):
            p = os.path.join(repo, fn)
            if os.path.exists(p):
                os.remove(p)


def try_build(repo):
    """make; on failure retry once with -Werror-free CFLAGS. Returns (ok, log)."""
    for args in (["make"], ["make", "CFLAGS=" + FALLBACK_CFLAGS]):
        subprocess.run(["make", "clean"], cwd=repo,
                       capture_output=True, text=True)
        r = subprocess.run(args, cwd=repo, capture_output=True, text=True,
                           timeout=300)
        imgs = all(os.path.exists(os.path.join(repo, i))
                   for i in ("xv6.img", "fs.img"))
        if r.returncode == 0 and imgs:
            note = "" if args == ["make"] else \
                "(built with -Werror disabled: stock xv6 warnings on modern gcc)"
            return True, note
        last = (r.stdout + r.stderr)
    return False, last[-3000:]


def build(repo):
    """
    Build with both grader tests. If that fails (e.g. check_address is not
    implemented / not declared), fall back to Part-1-only so Part 1 can
    still be graded. Returns (ok, part2_buildable, message).
    """
    patch_makefile(repo, include_addr_test=True)
    ok, msg = try_build(repo)
    if ok:
        return True, True, msg

    # Retry without the Part 2 test program.
    mk = os.path.join(repo, "Makefile")
    shutil.copy2(mk + ".gradebak", mk)
    patch_makefile(repo, include_addr_test=False)
    # (backup of the backup was just overwritten by copy2 target; re-backup)
    ok2, msg2 = try_build(repo)
    if ok2:
        return True, False, ("Part 2 test failed to compile — is "
                             "check_address declared in user.h/usys.S?\n"
                             "Compiler output tail:\n" + msg)
    return False, False, msg2


# ---------------------------------------------------------------------------
# Individual tests — each boots a fresh QEMU so a panic can't poison others
# ---------------------------------------------------------------------------
def fresh_session(repo, qemu_bin):
    s = QemuSession(repo, qemu_bin)
    if not s.wait_for_shell():
        s.close()
        return None
    return s


def test_shm_open(repo, qemu_bin):
    """15 pts: shm_cnt must end with a counter of 20000."""
    s = fresh_session(repo, qemu_bin)
    if s is None:
        return 0, "xv6 failed to boot to a shell"
    # Final (lowercase) summary lines are printed by both processes; wait for
    # the shell prompt that follows them. Loop lines say "Parent"/"Child"
    # (capitalized) so the lowercase regex below only matches the summaries.
    out = s.run("shm_cnt",
            r"(?s)panic|Counter in (?:parent|child) is \d+.*"
            r"Counter in (?:parent|child) is \d+", timeout=90)
    s.close()

    if "panic" in out:
        return 0, "kernel panic while running shm_cnt"
    finals = [int(x) for x in
              re.findall(r"Counter in (?:parent|child) is (\d+)", out)]
    final = max(finals) if finals else None
    if final == 20000:
        return PTS_SHM_OPEN, "final counter = 20000 (page correctly shared)"
    if final is None:
        return 0, ("shm_cnt did not finish — likely crash/page fault "
                   "(is *pointer being set? is the page mapped?)")
    if final > 10000:
        return 0, (f"final counter = {final}: page appears shared but updates "
                   "were lost — check locking / mapping")
    return 0, (f"final counter = {final}: processes are NOT sharing the page "
               "(each sees its own copy)")


def test_shm_close(repo, qemu_bin):
    """5 pts: close must clear the table entry and must not panic on exit."""
    s = fresh_session(repo, qemu_bin)
    if s is None:
        return 0, "xv6 failed to boot to a shell"
    out = s.run("gr_close", r"GR_CLOSE: \w+|panic", timeout=30)
    # Let exit()/freevm run; a bad kfree in shm_close often panics only here.
    time.sleep(1.5)
    s._read_available()
    out = s.log
    s.close()

    if "panic" in out:
        return 0, ("kernel panic during/after the close test — are you "
                   "kfree()ing a frame that is still mapped? (double free)")
    if "GR_CLOSE: OK" in out:
        return PTS_SHM_CLOSE, "table entry cleared; reopen produced a fresh page"
    if "GR_CLOSE: STALE_ENTRY" in out:
        return 0, ("reopening a closed id returned the OLD page — shm_close "
                   "is not clearing the shm_table entry when refcnt hits 0")
    if "GR_CLOSE: OPEN_FAIL" in out:
        return 0, "shm_open failed, so shm_close could not be tested"
    if "GR_CLOSE: REOPEN_FAIL" in out:
        return 0, "shm_open failed after a close — table state is corrupted"
    return 0, "close test produced no result — likely crash in shm_open/close"


def test_check_address(repo, qemu_bin):
    """10 pts: mapped addr -> prints phys/user-kernel/perms; unmapped -> 1."""
    s = fresh_session(repo, qemu_bin)
    if s is None:
        return 0, "xv6 failed to boot to a shell"
    out = s.run("gr_addr", r"GR_ADDR: END_UNMAPPED ret=-?\d+|panic", timeout=30)
    s.close()

    if "panic" in out:
        return 0, "kernel panic while running check_address"

    m_map = re.search(r"GR_ADDR: BEGIN_MAPPED\n(.*?)GR_ADDR: END_MAPPED "
                      r"ret=(-?\d+)", out, re.S)
    m_unm = re.search(r"GR_ADDR: END_UNMAPPED ret=(-?\d+)", out)
    if not m_map or not m_unm:
        return 0, ("test program did not complete — did check_address crash "
                   "on the unmapped address? (pass alloc=0 to walkpgdir and "
                   "check for a null PTE)")

    printed, ret_mapped = m_map.group(1), int(m_map.group(2))
    ret_unmapped = int(m_unm.group(1))

    problems = []
    if ret_unmapped != 1:
        problems.append(f"unmapped address returned {ret_unmapped}, expected 1")
    if ret_mapped == 1:
        problems.append("a mapped user address was reported as not mapped")
    if not re.search(r"0x[0-9a-fA-F]+|[0-9a-fA-F]{4,}", printed):
        problems.append("no physical address (hex) printed for a mapped page")
    if not re.search(r"user|kernel", printed, re.I):
        problems.append("kernel/user page type not printed")
    if not re.search(r"read", printed, re.I) or \
       not re.search(r"writ", printed, re.I):
        problems.append("read/write permissions not printed")

    if not problems:
        return PTS_CHECK_ADDR, ("mapped address info printed correctly; "
                                "unmapped address returned 1")
    return 0, "; ".join(problems)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def report(rows):
    line = "=" * 70
    print("\n" + line)
    print("CS153 LAB 3 AUTOGRADER RESULTS".center(70))
    print(line)
    total = 0
    for name, pts, maxpts, msg in rows:
        total += pts
        status = "PASS" if pts == maxpts else "FAIL"
        print(f"[{status}] {name:<28} {pts:>2}/{maxpts:<2}")
        print(f"       {msg}")
    print(line)
    print(f"TOTAL SCORE: {total} / {PTS_TOTAL}".center(70))
    print(line + "\n")
    return total


def main():
    ap = argparse.ArgumentParser(description="CS153 Lab 3 autograder")
    ap.add_argument("repo", nargs="?", default=".",
                    help="path to the xv6 lab 3 repository (default: .)")
    ap.add_argument("--qemu", default=None,
                    help="qemu binary (default: auto-detect)")
    ap.add_argument("--keep", action="store_true",
                    help="keep injected grader files after the run")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    if not os.path.exists(os.path.join(repo, "shm.c")):
        sys.exit(f"error: {repo} does not look like the Lab 3 repo "
                 "(shm.c not found)")

    qemu_bin = args.qemu or shutil.which("qemu-system-i386") \
        or shutil.which("qemu-system-x86_64")
    if not qemu_bin or not shutil.which("make"):
        sys.exit("error: this grader needs `make` and `qemu-system-i386` "
                 "on PATH")

    # Drop grader test sources into the repo.
    with open(os.path.join(repo, "gr_close.c"), "w") as f:
        f.write(GR_CLOSE_C)
    with open(os.path.join(repo, "gr_addr.c"), "w") as f:
        f.write(GR_ADDR_C)

    rows = []
    try:
        print("[*] Building xv6 (this can take a minute)...")
        ok, part2_buildable, note = build(repo)
        if not ok:
            print("[!] BUILD FAILED — cannot grade. Compiler output tail:\n")
            print(note)
            rows = [("shm_open()", 0, PTS_SHM_OPEN, "build failed"),
                    ("shm_close()", 0, PTS_SHM_CLOSE, "build failed"),
                    ("check_address()", 0, PTS_CHECK_ADDR, "build failed")]
            report(rows)
            sys.exit(1)
        if note:
            print(f"[*] Build OK {note}")
        else:
            print("[*] Build OK")

        print("[*] Test 1/3: shm_open — running shm_cnt ...")
        p, m = test_shm_open(repo, qemu_bin)
        rows.append(("shm_open()  (shm_cnt=20000)", p, PTS_SHM_OPEN, m))

        print("[*] Test 2/3: shm_close — running grader close test ...")
        p, m = test_shm_close(repo, qemu_bin)
        rows.append(("shm_close() (fresh reopen)", p, PTS_SHM_CLOSE, m))

        print("[*] Test 3/3: check_address — running grader address test ...")
        if part2_buildable:
            p, m = test_check_address(repo, qemu_bin)
        else:
            p, m = 0, ("check_address not implemented or not wired up "
                       "(user.h / usys.S / syscall.c / syscall.h)")
        rows.append(("check_address()", p, PTS_CHECK_ADDR, m))
    finally:
        restore_repo(repo, args.keep)
        subprocess.run(["make", "clean"], cwd=repo, capture_output=True)

    total = report(rows)
    sys.exit(0 if total == PTS_TOTAL else 0)


if __name__ == "__main__":
    main()
