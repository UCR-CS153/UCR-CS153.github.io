rubrics = r"""
- points: 10
  cmd: "ls"
  expect: "echo"
  note: "Test failed"
  name: "Unable to run a command"
"""



from pwn import *
import yaml
import base64
import re
import os

rubrics = yaml.safe_load(rubrics)
full = 0

os.system("touch README")

p = process("make qemu-nox".split())

points = 0
errors = []

try:
    p.recvuntil(b"init: starting sh\n$", timeout=10)
except:
    print("[!]Failed to compile and start xv6 with testsuite")
    print("[!]Compile log:", p.recvall().decode('latin-1'))
    print(f"Your score: {points}")
    exit(1)


for rubric in rubrics:
    print(f"[!]Checking [{rubric['name']}]")
    full += rubric["points"]
    try:
        if "cmd" in rubric:
            p.sendline(rubric["cmd"].encode())
        recv = p.recvuntil(rubric["expect"].encode(), timeout=2).decode('latin-1')
        if rubric["expect"] not in recv:
            raise Exception("Wrong output")
        points += rubric["points"]
    except:
        errors.append(rubric["note"])

if errors:
    print("[!]Errors breakdown:")
    for error in errors:
        print("    " + error)
else:
    print("[!]All check passed!")
print("=======")
print(f"Your score: {points} / {full}")

if errors:
    exit(1)
