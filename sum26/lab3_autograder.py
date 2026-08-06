#!/usr/bin/env python3

import os

# These must be set before importing pwntools.
os.environ.setdefault("TERM", "xterm")
os.environ.setdefault("PWNLIB_NOTERM", "1")

import atexit
import random
import re
import subprocess
import sys
from pathlib import Path

from pwn import PTY, context, process


TOTAL_POINTS = 80
STACK_LAYOUT_POINTS = 75
STACK_GROWTH_POINTS = 5

MAKEFILE = Path("Makefile")

LAYOUT_NAME = "lab3_stack_layout_test"
GROWTH_NAME = "lab3_stack_growth_test"

ADDRESS_MIN = 0x7FFF0000
ADDRESS_MAX = 0x80000000


LAYOUT_SOURCE = r"""
#include "types.h"
#include "stat.h"
#include "user.h"

int
main(int argc, char *argv[])
{
  int v = argc;
  printf(1, "%p\n", &v);
  exit();
}
"""


GROWTH_SOURCE = r"""
#include "types.h"
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
  int n;
  int result;

  if(argc != 2){
    printf(1, "Usage: %s levels\n", argv[0]);
    exit();
  }

  n = atoi(argv[1]);
  printf(1, "Lab 4: Recursing %d levels\n", n);

  result = recurse(n);

  printf(1, "Lab 4: Yielded a value of %d\n", result);
  exit();
}
"""


class GradeError(Exception):
    pass


def modify_makefile(contents, programs):
    contents = contents.replace(" -Werror", " ")

    match = re.search(
        r"(?ms)^UPROGS\s*=\s*(.*?)(?=^fs\.img\s*:)",
        contents,
    )

    if not match:
        raise GradeError("Could not find the UPROGS section in Makefile.")

    old_block = match.group(1)
    existing = re.findall(r"_([A-Za-z0-9_.-]+)", old_block)

    for program in programs:
        if program not in existing:
            existing.append(program)

    new_block = "UPROGS=\\\n"
    for program in existing:
        new_block += "\t_{}\\\n".format(program)
    new_block += "\n"

    return contents[:match.start()] + new_block + contents[match.end():]


def boot_xv6():
    env = os.environ.copy()
    env["TERM"] = "xterm"
    env["PWNLIB_NOTERM"] = "1"

    proc = process(
        ["make", "qemu-nox"],
        stdin=PTY,
        stdout=PTY,
        stderr=PTY,
        env=env,
    )

    try:
        boot_output = proc.recvuntil(b"init: starting sh", timeout=60)
        proc.recvuntil(b"$ ", timeout=15)
    except Exception:
        remaining = proc.recvrepeat(2)
        combined = boot_output if "boot_output" in locals() else b""
        combined += remaining

        raise GradeError(
            "xv6 failed to compile, boot, or reach its shell.\n"
            + combined.decode("latin-1", errors="replace")
        )

    return proc


def run_layout_test(proc, argument_count):
    arguments = " ".join(str(i) for i in range(1, argument_count + 1))
    command = LAYOUT_NAME

    if arguments:
        command += " " + arguments

    proc.sendline(command.encode())

    try:
        # Wait directly for a complete pointer line such as:
        # 7FFFFFBC
        matched = proc.recvline_regex(
            rb"^\s*(?:0x)?[0-9A-Fa-f]{8}\s*$",
            timeout=10,
        )
    except Exception:
        captured = proc.recvrepeat(1)
        raise GradeError(
            "Could not parse stack address after command {!r}.\n"
            "Captured output was: {!r}".format(
                command,
                captured.decode("latin-1", errors="replace"),
            )
        )

    text = matched.decode("latin-1", errors="replace").strip()
    address_match = re.search(r"(?:0x)?([0-9A-Fa-f]{8})", text)

    if not address_match:
        raise GradeError(
            "Matched a line but could not extract its address: {!r}".format(text)
        )

    address = int(address_match.group(1), 16)

    # Consume the prompt printed after the program exits.
    try:
        proc.recvuntil(b"$ ", timeout=10)
    except Exception:
        raise GradeError(
            "The xv6 shell prompt did not return after command {!r}.".format(
                command
            )
        )

    return address


def run_growth_test(proc, depth):
    command = "{} {}".format(GROWTH_NAME, depth)
    proc.sendline(command.encode())

    try:
        line = proc.recvline_regex(
            rb"Lab 4: Yielded a value of\s+-?[0-9]+",
            timeout=20,
        )
    except Exception:
        captured = proc.recvrepeat(1)
        raise GradeError(
            "Could not parse stack-growth output after command {!r}.\n"
            "Captured output was: {!r}".format(
                command,
                captured.decode("latin-1", errors="replace"),
            )
        )

    text = line.decode("latin-1", errors="replace")

    match = re.search(
        r"Lab 4: Yielded a value of\s+(-?[0-9]+)",
        text,
    )

    if not match:
        raise GradeError(
            "Could not extract the stack-growth result from {!r}.".format(text)
        )

    result = int(match.group(1))

    try:
        proc.recvuntil(b"$ ", timeout=10)
    except Exception:
        raise GradeError(
            "The xv6 shell prompt did not return after command {!r}.".format(
                command
            )
        )

    return result


def grade_layout(proc):
    addresses = {}

    test_counts = list(range(1, 8))
    test_counts += [random.randint(1, 7) for _ in range(20)]
    random.shuffle(test_counts)

    for supplied_arguments in test_counts:
        address = run_layout_test(proc, supplied_arguments)

        # argc includes the program name.
        argc = supplied_arguments + 1

        print(
            "[TEST] argc={} address={:08X}".format(
                argc,
                address,
            )
        )

        if not (ADDRESS_MIN <= address < ADDRESS_MAX):
            raise GradeError(
                "Address {:08X} is outside [{:08X}, {:08X}).".format(
                    address,
                    ADDRESS_MIN,
                    ADDRESS_MAX,
                )
            )

        if argc in addresses and addresses[argc] != address:
            raise GradeError(
                "argc={} produced inconsistent addresses: {:08X} and {:08X}."
                .format(argc, addresses[argc], address)
            )

        addresses[argc] = address

    ordered = sorted(addresses.items())
    moved_down = False

    for index in range(1, len(ordered)):
        previous_argc, previous_address = ordered[index - 1]
        current_argc, current_address = ordered[index]

        if current_address > previous_address:
            raise GradeError(
                "Stack moved upward as argc increased:\n"
                "argc={} -> {:08X}\n"
                "argc={} -> {:08X}".format(
                    previous_argc,
                    previous_address,
                    current_argc,
                    current_address,
                )
            )

        if current_address < previous_address:
            moved_down = True

    if not moved_down:
        raise GradeError(
            "Stack address never moved downward as argument count increased."
        )

    return addresses


def grade_growth(proc):
    depths = random.sample(range(500, 1001, 50), 3)

    for depth in depths:
        actual = run_growth_test(proc, depth)
        expected = depth * (depth + 1) // 2

        print(
            "[TEST] depth={} expected={} actual={}".format(
                depth,
                expected,
                actual,
            )
        )

        if actual != expected:
            raise GradeError(
                "Incorrect result at depth {}: expected {}, received {}."
                .format(depth, expected, actual)
            )

    return depths


def main():
    context.log_level = "error"

    if not MAKEFILE.exists():
        print("[!] Makefile not found.")
        print("[!] Run this script from the xv6 repository root.")
        print("Your score: 0 / {}".format(TOTAL_POINTS))
        return 1

    original_makefile = MAKEFILE.read_bytes()

    generated_paths = [
        Path(LAYOUT_NAME + ".c"),
        Path(GROWTH_NAME + ".c"),
    ]

    previous_files = {
        path: path.read_bytes() if path.exists() else None
        for path in generated_paths
    }

    qemu = None
    score = 0

    def restore():
        nonlocal qemu

        if qemu is not None:
            try:
                qemu.close()
            except Exception:
                pass

        try:
            MAKEFILE.write_bytes(original_makefile)
        except Exception:
            pass

        for path, prior_content in previous_files.items():
            try:
                if prior_content is None:
                    if path.exists():
                        path.unlink()
                else:
                    path.write_bytes(prior_content)
            except Exception:
                pass

    atexit.register(restore)

    try:
        Path(LAYOUT_NAME + ".c").write_text(
            LAYOUT_SOURCE,
            encoding="utf-8",
        )
        Path(GROWTH_NAME + ".c").write_text(
            GROWTH_SOURCE,
            encoding="utf-8",
        )

        makefile_text = original_makefile.decode(
            "utf-8",
            errors="replace",
        )

        MAKEFILE.write_text(
            modify_makefile(
                makefile_text,
                [LAYOUT_NAME, GROWTH_NAME],
            ),
            encoding="utf-8",
        )

        print("[*] Running make clean...")

        clean = subprocess.run(
            ["make", "clean"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120,
        )

        if clean.returncode != 0:
            raise GradeError("make clean failed:\n" + clean.stdout)

        print("[*] Building and booting xv6...")
        qemu = boot_xv6()

        print("[*] Testing new stack layout...")
        addresses = grade_layout(qemu)
        score += STACK_LAYOUT_POINTS

        print("[+] Stack-layout test passed.")
        for argc, address in sorted(addresses.items()):
            print("    argc={} -> {:08X}".format(argc, address))
        print("[+] Score: {} / {}".format(score, TOTAL_POINTS))

        print("[*] Testing automatic stack growth...")
        depths = grade_growth(qemu)
        score += STACK_GROWTH_POINTS

        print(
            "[+] Stack-growth test passed at depths: {}".format(
                ", ".join(str(depth) for depth in depths)
            )
        )

    except subprocess.TimeoutExpired as error:
        print("[!] Build command timed out: {}".format(error))
        print("Your score: {} / {}".format(score, TOTAL_POINTS))
        return 1

    except GradeError as error:
        print("[!] {}".format(error))

        if score == STACK_LAYOUT_POINTS:
            print("[!] Stack-growth verification failed.")
        else:
            print("[!] Stack-layout verification failed.")

        print("Your score: {} / {}".format(score, TOTAL_POINTS))
        return 1

    except Exception as error:
        print(
            "[!] Unexpected autograder error: {}: {}".format(
                type(error).__name__,
                error,
            )
        )
        print("Your score: {} / {}".format(score, TOTAL_POINTS))
        return 1

    print("[!] All checks finished.")
    print("=======")
    print("Your score: {} / {}".format(score, TOTAL_POINTS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
