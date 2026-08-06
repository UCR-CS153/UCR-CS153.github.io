#!/usr/bin/env python3
"""Autograder for xv6 randomized stack layout and automatic stack growth.

Run this script from the root directory of a student's xv6 repository.
Dependencies:
    python3 -m pip install pwntools
"""

from __future__ import annotations

import atexit
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from pwn import context, process


TOTAL_POINTS = 80
LAYOUT_POINTS = 75
GROWTH_POINTS = 5

XV6_PROMPT = rb"\$ "
BOOT_MARKER = rb"init: starting sh"
MAKEFILE = Path("Makefile")

TEST1_NAME = "test1"
LAB2_NAME = "lab2"

TEST1_SOURCE = r'''#include "types.h"
#include "stat.h"
#include "user.h"

int main (int argc, char *argv[]) {
    int v = argc;
    printf(1, "%p\n", &v);
    exit();
}
'''

LAB2_SOURCE = r'''#include "types.h"
#include "user.h"

#pragma GCC push_options
#pragma GCC optimize ("O0")
static int
recurse(int n)
{
  if(n == 0)
    return 0;
  return n + recurse(n - 1);
}
#pragma GCC pop_options

int
main(int argc, char *argv[])
{
  int n, m;

  if(argc != 2){
    printf(1, "Usage: %s levels\n", argv[0]);
    exit();
  }

  n = atoi(argv[1]);
  printf(1, "Lab 4: Recursing %d levels\n", n);
  m = recurse(n);
  printf(1, "Lab 4: Yielded a value of %d\n", m);
  exit();
}
'''


class GradeFailure(Exception):
    """Raised when a grading check fails."""


def backup_file(path: Path) -> Path:
    backup = path.with_suffix(path.suffix + ".autograder.bak")
    shutil.copy2(path, backup)
    return backup


def add_uprogs(makefile_text: str, program_names: list[str]) -> str:
    """Add programs to UPROGS for the classic MIT xv6 Makefile."""
    text = makefile_text.replace(" -Werror", " ")

    match = re.search(r"(?ms)^UPROGS\s*=\s*(.*?)(?=^fs\.img\s*:)", text)
    if not match:
        raise GradeFailure("Could not locate UPROGS ... fs.img section in Makefile")

    current_block = match.group(1)
    current_programs = re.findall(r"_([A-Za-z0-9_.-]+)", current_block)

    for name in program_names:
        if name not in current_programs:
            current_programs.append(name)

    replacement = "UPROGS=\\\n" + "".join(
        f"\t_{name}\\\n" for name in current_programs
    ) + "\n"

    return text[: match.start()] + replacement + text[match.end() :]


def wait_for_prompt(proc, timeout: float = 20.0) -> bytes:
    """Read through the xv6 prompt and return the captured output."""
    return proc.recvuntil(XV6_PROMPT, timeout=timeout)


def synchronize_shell(proc, timeout: float = 5.0) -> None:
    """Force xv6 to emit a fresh prompt, avoiding stale buffered prompts."""
    proc.sendline(b"")
    proc.recvuntil(XV6_PROMPT, timeout=timeout)


def run_xv6_command(proc, command: str, timeout: float = 5.0) -> str:
    # A repository may leave an additional prompt buffered during boot. If that
    # stale prompt is consumed after sending the command, the captured output is
    # just "$ " and the test is incorrectly reported as failed. Synchronizing
    # with a blank command guarantees that the next prompt belongs to this run.
    synchronize_shell(proc, timeout=min(timeout, 5.0))
    proc.sendline(command.encode())
    output = proc.recvuntil(XV6_PROMPT, timeout=timeout)
    return output.decode("latin-1", errors="replace")


def parse_last_hex_address(output: str) -> int:
    """Parse xv6 printf("%p") output with or without a 0x prefix."""
    candidates = []

    # Prefer a line containing only the address. This avoids interpreting
    # numeric command-line arguments in the echoed shell command as addresses.
    for line in output.replace("\r", "").splitlines():
        match = re.fullmatch(r"\s*(?:0x)?([0-9a-fA-F]{6,16})\s*", line)
        if match:
            candidates.append(match.group(1))

    # Some xv6 console implementations place shell text and program output on
    # the same line. Fall back to any pointer-sized hexadecimal token.
    if not candidates:
        candidates = re.findall(
            r"(?<![0-9A-Za-z])(?:0x)?([0-9a-fA-F]{7,16})(?![0-9A-Za-z])",
            output,
        )

    if not candidates:
        visible = output.replace("\r", "\\r").replace("\n", "\\n\n")
        raise GradeFailure(
            "Could not parse stack address from xv6 output. "
            f"Captured output was:\n{visible}"
        )

    return int(candidates[-1], 16)


def test_stack_layout(proc) -> dict[int, int]:
    """Check high stack placement, consistency, and argc-dependent movement."""
    addresses: dict[int, int] = {}

    # Repeat argument counts in randomized order to detect unstable placement.
    argument_counts = [random.randint(1, 7) for _ in range(random.randint(50, 80))]

    for extra_arg_count in argument_counts:
        args = " ".join(str(i) for i in range(extra_arg_count))
        output = run_xv6_command(proc, f"{TEST1_NAME} {args}", timeout=3.0)
        address = parse_last_hex_address(output)

        # The assignment expects the initial stack near the top of user space.
        if address < 0x7FFF0000 or address >= 0x80000000:
            raise GradeFailure(
                f"Stack address {address:#x} is outside [0x7fff0000, 0x80000000)"
            )

        # argc includes the program name itself.
        argc = extra_arg_count + 1
        previous = addresses.get(argc)
        if previous is not None and previous != address:
            raise GradeFailure(
                f"argc={argc} produced inconsistent addresses: "
                f"{previous:#x} and {address:#x}"
            )
        addresses[argc] = address

    ordered = sorted(addresses.items())
    if len(ordered) < 2:
        raise GradeFailure("Not enough distinct argc values were tested")

    # More arguments consume additional stack space, so the local variable
    # address should never move upward as argc increases.
    for (argc_a, addr_a), (argc_b, addr_b) in zip(ordered, ordered[1:]):
        if addr_b > addr_a:
            raise GradeFailure(
                f"Stack moved upward from argc={argc_a} ({addr_a:#x}) "
                f"to argc={argc_b} ({addr_b:#x})"
            )

    if len(set(addresses.values())) == 1:
        raise GradeFailure("Stack address did not change for different argument counts")

    return addresses


def test_stack_growth(proc) -> list[int]:
    """Run recursive calls deep enough to cross the initial stack page."""
    # Multiple depths make hard-coded output less useful and test repeated growth.
    depths = random.sample(range(350, 851, 25), 3)

    for depth in depths:
        output = run_xv6_command(proc, f"{LAB2_NAME} {depth}", timeout=8.0)
        match = re.search(r"Lab 4: Yielded a value of\s+(-?\d+)", output)
        if not match:
            raise GradeFailure(
                f"No successful recursion result for depth {depth}. Output:\n{output}"
            )

        actual = int(match.group(1))
        expected = depth * (depth + 1) // 2
        if actual != expected:
            raise GradeFailure(
                f"Depth {depth}: expected {expected}, but xv6 printed {actual}"
            )

    return depths


def main() -> int:
    context.log_level = "error"
    random.seed()

    if not MAKEFILE.exists():
        print("[!] Run this script from the root of the xv6 repository.")
        print(f"Your score: 0 / {TOTAL_POINTS}")
        return 1

    points = 0
    makefile_backup = backup_file(MAKEFILE)
    generated_files = [Path(f"{TEST1_NAME}.c"), Path(f"{LAB2_NAME}.c")]
    proc = None

    def restore() -> None:
        nonlocal proc
        if proc is not None:
            try:
                proc.close()
            except Exception:
                pass
        if makefile_backup.exists():
            shutil.move(str(makefile_backup), str(MAKEFILE))
        for path in generated_files:
            try:
                path.unlink()
            except FileNotFoundError:
                pass

    atexit.register(restore)

    try:
        generated_files[0].write_text(TEST1_SOURCE, encoding="utf-8")
        generated_files[1].write_text(LAB2_SOURCE, encoding="utf-8")

        original_makefile = MAKEFILE.read_text(encoding="utf-8")
        MAKEFILE.write_text(
            add_uprogs(original_makefile, [TEST1_NAME, LAB2_NAME]),
            encoding="utf-8",
        )

        clean = subprocess.run(
            ["make", "clean"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=60,
        )
        if clean.returncode != 0:
            raise GradeFailure(f"make clean failed:\n{clean.stdout}")

        proc = process(["make", "qemu-nox"])
        try:
            proc.recvuntil(BOOT_MARKER, timeout=20)
            wait_for_prompt(proc, timeout=10)
        except Exception:
            compile_log = proc.recvrepeat(1).decode("latin-1", errors="replace")
            raise GradeFailure(
                "Failed to compile or boot xv6 with the tests.\n" + compile_log
            )

        addresses = test_stack_layout(proc)
        points += LAYOUT_POINTS
        print("[+] New stack layout passed")
        print("    " + ", ".join(
            f"argc={argc}: {addr:#x}" for argc, addr in sorted(addresses.items())
        ))
        print(f"    Score: {points} / {TOTAL_POINTS}")

        depths = test_stack_growth(proc)
        points += GROWTH_POINTS
        print(f"[+] Stack growth passed at depths: {', '.join(map(str, depths))}")
        print(f"    Score: {points} / {TOTAL_POINTS}")

    except GradeFailure as exc:
        print(f"[!] {exc}")
        if points == LAYOUT_POINTS:
            print("[!] Stack-growth test failed; stack-layout credit was retained.")
        else:
            print("[!] Stack-layout verification failed.")
        print(f"Your score: {points} / {TOTAL_POINTS}")
        return 1
    except subprocess.TimeoutExpired as exc:
        print(f"[!] Build command timed out: {exc}")
        print(f"Your score: {points} / {TOTAL_POINTS}")
        return 1
    except Exception as exc:
        print(f"[!] Unexpected autograder error: {type(exc).__name__}: {exc}")
        print(f"Your score: {points} / {TOTAL_POINTS}")
        return 1

    print("[!] All checks finished successfully.")
    print("=======")
    print(f"Your score: {points} / {TOTAL_POINTS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
