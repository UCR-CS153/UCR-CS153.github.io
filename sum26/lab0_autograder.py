import os
import subprocess
import sys

required_file = "helloWorld.c"
expected_output = "Hello World!"

print("[*] Starting autograder...")

# 1. Check if helloWorld.c exists
if not os.path.isfile(required_file):
    print(f"[X] Missing required file: {required_file}")
    sys.exit(1)

print(f"[✓] Found {required_file}")

# 2. Compile helloWorld.c
compile_result = subprocess.run(
    ["gcc", required_file, "-o", "helloWorld"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

if compile_result.returncode != 0:
    print("[X] Compilation failed.")
    print(compile_result.stderr)
    sys.exit(1)

print("[✓] Compilation successful")

# 3. Run the compiled program
try:
    run_result = subprocess.run(
        ["./helloWorld"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=5
    )
except subprocess.TimeoutExpired:
    print("[X] Program timed out.")
    sys.exit(1)

# 4. Check output
output = run_result.stdout.strip()

print(f"Student output: {output}")

if output != expected_output:
    print("[X] Wrong output.")
    print(f"Expected: {expected_output}")
    print(f"Got: {output}")
    sys.exit(1)

# 5. Passed
print("[!] All Checks Passed!")
print("---> Your total score: 100 / 100")
print("[!] You are now ready to begin working on Lab 1.")
sys.exit(0)
