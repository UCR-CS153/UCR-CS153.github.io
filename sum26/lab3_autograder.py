#!/usr/bin/env python3

import atexit
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path

from pwn import context, process


TOTAL_POINTS = 80
STACK_LAYOUT_POINTS = 75
STACK_GROWTH_POINTS = 5

MAKEFILE_PATH = Path("Makefile")

TEST1_PROGRAM = "test1"
GROWTH_PROGRAM = "lab2"

ADDRESS_MIN = 0x7FFF0000
ADDRESS_MAX = 0x80000000

TEST1_SOURCE = r'''
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
'''

LAB2_SOURCE = r'''
#include "types.h"
#include "user.h"

/*
 * Prevent GCC from replacing the recursive function with an optimized
 * closed-form or loop implementation.
 */
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
'''


class GradingError(Exception):
    pass


def update_makefile(makefile_content, program_names):
    """
    Add the autograder programs to the xv6 UPROGS section.
    """

    # Some student repositories fail because of compiler warnings.
    makefile_content = makefile_content.replace(" -Werror", " ")

    match = re.search(
        r"(?ms)^UPROGS\s*=\s*(.*?)(?=^fs\.img\s*:)",
        makefile_content,
    )

    if match is None:
        raise GradingError(
            "Could not locate the UPROGS section in the Makefile."
        )

    uprogs_block = match.group(1)

    existing_programs = re.findall(
        r"_([A-Za-z0-9_.-]+)",
        uprogs_block,
    )

    for program_name in program_names:
        if program_name not in existing_programs:
            existing_programs.append(program_name)

    new_uprogs = "UPROGS=\\\n"

    for program_name in existing_programs:
        new_uprogs += "\t_{}\\\n".format(program_name)

    new_uprogs += "\n"

    return (
        makefile_content[:match.start()]
        + new_uprogs
        + makefile_content[match.end():]
    )


def receive_until_shell(proc, timeout=10):
    """
    Read xv6 output until a shell prompt is observed.

    This is used only for synchronization. Test values are parsed directly
    from complete output lines.
    """

    output = bytearray()
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            chunk = proc.recv(timeout=0.25)
        except EOFError:
            break

        if not chunk:
            continue

        output.extend(chunk)

        normalized = bytes(output).replace(b"\r", b"")

        if normalized.endswith(b"\n$ ") or normalized.endswith(b"\n$"):
            break

    return bytes(output)


def wait_for_xv6_shell(proc, timeout=40):
    """
    Wait until xv6 finishes booting and starts its shell.
    """

    output = bytearray()
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            chunk = proc.recv(timeout=0.5)
        except EOFError:
            break

        if not chunk:
            continue

        output.extend(chunk)

        normalized = bytes(output).replace(b"\r", b"")

        if b"init: starting sh" in normalized:
            if normalized.endswith(b"\n$ ") or normalized.endswith(b"\n$"):
                return bytes(output)

            remaining = receive_until_shell(proc, timeout=10)
            output.extend(remaining)
            return bytes(output)

    raise GradingError(
        "xv6 did not reach the shell.\n\n"
        + output.decode("latin-1", errors="replace")
    )


def run_xv6_command(proc, command, timeout=10):
    """
    Execute one command in xv6 and collect its complete output.

    The old shell prompt is removed before sending the command. Output is then
    read until xv6 prints the next shell prompt.
    """

    # Remove an old buffered shell prompt.
    proc.clean(timeout=0.15)

    proc.sendline(command.encode("ascii"))

    output = bytearray()
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            chunk = proc.recv(timeout=0.25)
        except EOFError:
            break

        if not chunk:
            continue

        output.extend(chunk)

        normalized = bytes(output).replace(b"\r", b"")

        if normalized.endswith(b"\n$ ") or normalized.endswith(b"\n$"):
            break

    decoded = bytes(output).decode("latin-1", errors="replace")

    if not decoded.strip():
        raise GradingError(
            "No output was captured for command: {}".format(command)
        )

    return decoded


def parse_stack_address(output):
    """
    Parse an xv6 pointer printed as, for example:

        7FFFFFBC

    Both eight-digit values and values prefixed with 0x are accepted.
    """

    normalized = output.replace("\r", "")

    # Prefer a line containing only the address.
    matches = re.findall(
        r"(?im)^\s*(?:0x)?([0-9a-f]{8})\s*$",
        normalized,
    )

    if not matches:
        # Fallback for repositories that print extra text on the same line.
        matches = re.findall(
            r"(?i)(?<![0-9a-f])(?:0x)?([0-9a-f]{8})(?![0-9a-f])",
            normalized,
        )

    if not matches:
        raise GradingError(
            "Could not parse the stack address.\n"
            "Captured xv6 output: {!r}".format(output)
        )

    return int(matches[-1], 16)


def parse_growth_result(output):
    """
    Parse:

        Lab 4: Yielded a value of <number>
    """

    match = re.search(
        r"Lab\s+4:\s*Yielded\s+a\s+value\s+of\s+(-?\d+)",
        output,
        re.IGNORECASE,
    )

    if match is None:
        raise GradingError(
            "Could not parse the recursion result.\n"
            "Captured xv6 output: {!r}".format(output)
        )

    return int(match.group(1))


def test_stack_layout(proc):
    """
    Verify:

    1. The user stack is near 0x80000000.
    2. Equal argument counts produce equal stack addresses.
    3. Increasing argument counts move the stack downward.
    """

    addresses = {}

    # Test each argument count at least once.
    argument_counts = list(range(1, 8))

    # Repeat random argument counts to check consistency.
    for _ in range(25):
        argument_counts.append(random.randint(1, 7))

    random.shuffle(argument_counts)

    for extra_argument_count in argument_counts:
        arguments = " ".join(
            str(value)
            for value in range(1, extra_argument_count + 1)
        )

        command = TEST1_PROGRAM

        if arguments:
            command += " " + arguments

        output = run_xv6_command(
            proc,
            command,
            timeout=8,
        )

        address = parse_stack_address(output)

        # argc contains the program name in addition to supplied arguments.
        argc = extra_argument_count + 1

        print(
            "[TEST] argc={} address={:08X}".format(
                argc,
                address,
            )
        )

        if not (ADDRESS_MIN <= address < ADDRESS_MAX):
            raise GradingError(
                "Stack address {:08X} for argc={} is outside the "
                "expected range [{:08X}, {:08X}).".format(
                    address,
                    argc,
                    ADDRESS_MIN,
                    ADDRESS_MAX,
                )
            )

        if argc in addresses:
            if addresses[argc] != address:
                raise GradingError(
                    "The same argument count produced different addresses.\n"
                    "argc={}: {:08X} and {:08X}".format(
                        argc,
                        addresses[argc],
                        address,
                    )
                )
        else:
            addresses[argc] = address

    sorted_addresses = sorted(addresses.items())

    address_changed = False

    for index in range(1, len(sorted_addresses)):
        previous_argc, previous_address = sorted_addresses[index - 1]
        current_argc, current_address = sorted_addresses[index]

        if current_address > previous_address:
            raise GradingError(
                "The stack address moved upward when argc increased.\n"
                "argc={} -> {:08X}\n"
                "argc={} -> {:08X}".format(
                    previous_argc,
                    previous_address,
                    current_argc,
                    current_address,
                )
            )

        if current_address < previous_address:
            address_changed = True

    if not address_changed:
        raise GradingError(
            "The stack address did not move when the argument count increased."
        )

    return addresses


def test_stack_growth(proc):
    """
    Force the stack to grow across multiple pages using recursion.
    """

    # Use several depths so a hard-coded implementation is less likely to pass.
    possible_depths = list(range(500, 1001, 50))
    test_depths = random.sample(possible_depths, 3)

    for depth in test_depths:
        command = "{} {}".format(
            GROWTH_PROGRAM,
            depth,
        )

        output = run_xv6_command(
            proc,
            command,
            timeout=15,
        )

        actual_result = parse_growth_result(output)
        expected_result = depth * (depth + 1) // 2

        print(
            "[TEST] recursion depth={} expected={} actual={}".format(
                depth,
                expected_result,
                actual_result,
            )
        )

        if actual_result != expected_result:
            raise GradingError(
                "Incorrect recursion result at depth {}. "
                "Expected {}, but received {}.".format(
                    depth,
                    expected_result,
                    actual_result,
                )
            )

    return test_depths


def main():
    context.log_level = "error"
    os.environ.setdefault("TERM", "xterm")

    random.seed()

    if not MAKEFILE_PATH.exists():
        print("[!] Makefile was not found.")
        print("[!] Run the autograder from the xv6 repository root.")
        print("Your score: 0 / {}".format(TOTAL_POINTS))
        return 1

    original_makefile = MAKEFILE_PATH.read_bytes()

    generated_files = [
        Path(TEST1_PROGRAM + ".c"),
        Path(GROWTH_PROGRAM + ".c"),
    ]

    original_generated_files = {}

    for path in generated_files:
        if path.exists():
            original_generated_files[path] = path.read_bytes()
        else:
            original_generated_files[path] = None

    qemu_process = None
    score = 0

    def restore_repository():
        nonlocal qemu_process

        if qemu_process is not None:
            try:
                qemu_process.close()
            except Exception:
                pass

        try:
            MAKEFILE_PATH.write_bytes(original_makefile)
        except Exception:
            pass

        for path, original_content in original_generated_files.items():
            try:
                if original_content is None:
                    if path.exists():
                        path.unlink()
                else:
                    path.write_bytes(original_content)
            except Exception:
                pass

    atexit.register(restore_repository)

    try:
        Path(TEST1_PROGRAM + ".c").write_text(
            TEST1_SOURCE,
            encoding="utf-8",
        )

        Path(GROWTH_PROGRAM + ".c").write_text(
            LAB2_SOURCE,
            encoding="utf-8",
        )

        makefile_text = original_makefile.decode(
            "utf-8",
            errors="replace",
        )

        updated_makefile = update_makefile(
            makefile_text,
            [TEST1_PROGRAM, GROWTH_PROGRAM],
        )

        MAKEFILE_PATH.write_text(
            updated_makefile,
            encoding="utf-8",
        )

        print("[*] Cleaning repository...")

        clean_result = subprocess.run(
            ["make", "clean"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120,
        )

        if clean_result.returncode != 0:
            raise GradingError(
                "make clean failed:\n{}".format(clean_result.stdout)
            )

        print("[*] Building and starting xv6...")

        environment = os.environ.copy()
        environment.setdefault("TERM", "xterm")

        qemu_process = process(
            ["make", "qemu-nox"],
            env=environment,
        )

        try:
            wait_for_xv6_shell(
                qemu_process,
                timeout=60,
            )
        except GradingError:
            remaining_output = qemu_process.recvrepeat(1).decode(
                "latin-1",
                errors="replace",
            )

            raise GradingError(
                "xv6 failed to compile, boot, or reach its shell.\n"
                + remaining_output
            )

        print("[*] Testing the new user-stack layout...")

        addresses = test_stack_layout(qemu_process)

        score += STACK_LAYOUT_POINTS

        print("[+] Stack-layout tests passed.")

        for argc, address in sorted(addresses.items()):
            print(
                "    argc={} -> {:08X}".format(
                    argc,
                    address,
                )
            )

        print(
            "[+] Score: {} / {}".format(
                score,
                TOTAL_POINTS,
            )
        )

        print("[*] Testing automatic stack growth...")

        depths = test_stack_growth(qemu_process)

        score += STACK_GROWTH_POINTS

        print(
            "[+] Stack-growth tests passed for depths: {}".format(
                ", ".join(str(depth) for depth in depths)
            )
        )

        print(
            "[+] Score: {} / {}".format(
                score,
                TOTAL_POINTS,
            )
        )

    except subprocess.TimeoutExpired as error:
        print("[!] A build command timed out: {}".format(error))
        print(
            "Your score: {} / {}".format(
                score,
                TOTAL_POINTS,
            )
        )
        return 1

    except GradingError as error:
        print("[!] {}".format(error))

        if score == STACK_LAYOUT_POINTS:
            print(
                "[!] Stack growth failed, but stack-layout credit is retained."
            )
        else:
            print("[!] Stack-layout verification failed.")

        print(
            "Your score: {} / {}".format(
                score,
                TOTAL_POINTS,
            )
        )
        return 1

    except Exception as error:
        print(
            "[!] Unexpected autograder error: {}: {}".format(
                type(error).__name__,
                error,
            )
        )

        print(
            "Your score: {} / {}".format(
                score,
                TOTAL_POINTS,
            )
        )
        return 1

    print("[!] All checks finished successfully.")
    print("=======")
    print(
        "Your score: {} / {}".format(
            score,
            TOTAL_POINTS,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
