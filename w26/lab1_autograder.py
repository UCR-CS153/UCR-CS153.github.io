rubrics = r"""
- points: 5
  cmd: "lab1_autograde 4"
  expect: "Getinfo: invalid parameters."
  note: "Part 1: Failed to handle invalid parameters"
  name: "Part 1 - Invalid Parameters"

- points: 10
  expect: "Parent: 3"
  note: "Part 1: Failed to print correct parent PID (Expected 3)"
  name: "Part 1 - Parent PID"

- points: 10
  expect: "Sibling: 5"
  note: "Part 1: Failed to print correct sibling PID (Expected 5)"
  name: "Part 1 - Sibling PID"

- points: 5
  cmd: "lab1_autograde 1"
  expect: "8 0"
  note: "Fork failed"
  name: "Exit & Wait - Fork first child process"

- points: 5
  expect: "8+0"
  note: "[Exit & Wait]Failed to obtain correct first child process exit status"
  name: "Exit & Wait - Wait for first child process"

- points: 0
  expect: "9 -1"
  note: "[Exit & Wait]Fork second child process failed"
  name: "Exit & Wait - Fork second child process"

- points: 15
  expect: "9+-1"
  note: "[Exit & Wait]Failed to obtain correct second child process exit status"
  name: "Exit & Wait - Wait for second child process"

- points: 0
  cmd: "lab1_autograde 2"
  expect: "14 18"
  note: "[Waitpid]Failed to create 5 child processes"
  name: "Waitpid - create 5 child processes"

- points: 40
  expect: "14\n14+18+18\n12\n12+16+16\n13\n13+17+17\n11\n11+15+15\n15\n15+19+19"
  note: "[Waitpid]Child process exit status is incorrect"
  name: "Waitpid - check 5 child processes exit status"

- points: 5
  expect: "-1"
  note: "[Waitpid]Syscall does not return -1 while obtaining status of an invalid process"
  name: "Waitpid - check invalid process"

- points: 5
  expect: "-1"
  note : "[Waitpid]Syscall does not return -1 when an invalid argument is given"
  name: "Waitpid - check invalid argument"

- points: 5
  cmd: "lab1_autograde 3"
  expect: "-1 -1"
  note: "[Exit & Wait]Should return -1 for a child process that does not exist"
  name: "Exit & Wait - Wait for a child process that does not exist"
"""

code = """I2luY2x1ZGUgInR5cGVzLmgiCiNpbmNsdWRlICJ1c2VyLmgiCgojZGVmaW5lIFdOT0hBTkcgMQoKaW50IGdldGluZm8oaW50KTsgLy8gTmV3IFBhcnQgMSBzeXNjYWxsCgppbnQgbWFpbihpbnQgYXJnYywgY2hhciAqYXJndltdKSB7CiAgaW50IGV4aXRXYWl0KHZvaWQpOwogIGludCB3YWl0UGlkKHZvaWQpOwogIGludCB3YWl0Tm90aGluZyh2b2lkKTsKICB2b2lkIHRlc3RHZXRJbmZvKHZvaWQpOwoKICBwcmludGYoMSwgIlxubGFiIzFcbiIpOwogIGlmIChhdG9pKGFyZ3ZbMV0pID09IDEpCiAgICBleGl0V2FpdCgpOwogIGVsc2UgaWYgKGF0b2koYXJndlsxXSkgPT0gMikKICAgIHdhaXRQaWQoKTsKICBlbHNlIGlmIChhdG9pKGFyZ3ZbMV0pID09IDMpCiAgICB3YWl0Tm90aGluZygpOwogIGVsc2UgaWYgKGF0b2koYXJndlsxXSkgPT0gNCkKICAgIHRlc3RHZXRJbmZvKCk7CiAgCiAgZXhpdCgwKTsKICByZXR1cm4gMDsKfQoKdm9pZCB0ZXN0R2V0SW5mbyh2b2lkKSB7CiAgaW50IHBpZDE7CiAgLy8gVGVzdCAxOiBJbnZhbGlkIFBhcmFtZXRlcgogIC8vIFJ1YnJpYyBleHBlY3RzOiAiR2V0aW5mbzogaW52YWxpZCBwYXJhbWV0ZXJzLiIKICBnZXRpbmZvKDApOyAKCiAgLy8gVGVzdCAyOiBQYXJlbnQgUElECiAgLy8gQ3VycmVudCBwcm9jZXNzIGlzIGxpa2VseSBQSUQgMyAoaW5pdD0xLCBzaD0yLCBhdXRvZ3JhZGU9MykuCiAgLy8gQ2hpbGQgd2lsbCBiZSBQSUQgNC4gQ2hpbGQncyBwYXJlbnQgaXMgMy4KICBpZiAoZm9yaygpID09IDApIHsKICAgIHByaW50ZigxLCAiUGFyZW50OiAiKTsKICAgIGdldGluZm8oMSk7IC8vIFNob3VsZCBwcmludCAzCiAgICBwcmludGYoMSwgIlxuIik7CiAgICBleGl0KDApOwogIH0KICB3YWl0KDApOwoKICAvLyBUZXN0IDM6IFNpYmxpbmcgUElECiAgLy8gRm9yayBwMSAoUElEIDUpLiBwMSBzbGVlcHMuCiAgLy8gRm9yayBwMiAoUElEIDYpLiBwMiBhc2tzIGZvciBzaWJsaW5ncy4gU2hvdWxkIGZpbmQgcDEgKDUpLgogIHBpZDEgPSBmb3JrKCk7CiAgaWYgKHBpZDEgPT0gMCkgewogICAgc2xlZXAoMTAwKTsKICAgIGV4aXQoMCk7CiAgfQoKICBpZiAoZm9yaygpID09IDApIHsKICAgIHByaW50ZigxLCAiU2libGluZzogIik7CiAgICBnZXRpbmZvKDIpOyAvLyBTaG91bGQgcHJpbnQgNQogICAgcHJpbnRmKDEsICJcbiIpOwogICAgZXhpdCgwKTsKICB9CiAgCiAgd2FpdCgwKTsgLy8gV2FpdCBmb3IgcDIKICBraWxsKHBpZDEpOwogIHdhaXQoMCk7IC8vIFdhaXQgZm9yIHAxCn0KCmludCB3YWl0Tm90aGluZyh2b2lkKSB7CiAgaW50IHJldCwgZXhpdF9zdGF0dXMgPSAtMTsKICByZXQgPSB3YWl0KCZleGl0X3N0YXR1cyk7CiAgcHJpbnRmKDEsICIlZCAlZFxuIiwgcmV0LCBleGl0X3N0YXR1cyk7CiAgcmV0dXJuIDA7Cn0KCmludCBleGl0V2FpdCh2b2lkKSB7CiAgaW50IHBpZCwgcmV0X3BpZCwgZXhpdF9zdGF0dXM7CiAgaW50IGk7CgogIGZvciAoaSA9IDA7IGkgPCAyOyBpKyspIHsKICAgIHBpZCA9IGZvcmsoKTsKICAgIGlmIChwaWQgPT0gMCkgeyAKICAgICAgaWYgKGkgPT0gMCkgewogICAgICAgIHByaW50ZigxLCAiJWQgJWRcbiIsIGdldHBpZCgpLCAwKTsKICAgICAgICBleGl0KDApOwogICAgICB9IGVsc2UgewogICAgICAgIHByaW50ZigxLCAiJWQgJWRcbiIsIGdldHBpZCgpLCAtMSk7CiAgICAgICAgZXhpdCgtMSk7CiAgICAgIH0KICAgIH0gZWxzZSBpZiAocGlkID4gMCkgeyAKICAgICAgcmV0X3BpZCA9IHdhaXQoJmV4aXRfc3RhdHVzKTsKICAgICAgcHJpbnRmKDEsICIlZCslZFxuIiwgcmV0X3BpZCwgZXhpdF9zdGF0dXMpOwogICAgfSBlbHNlIHsgCiAgICAgIHByaW50ZigyLCAiXG5FcnJvciB1c2luZyBmb3JrXG4iKTsKICAgICAgZXhpdCgtMSk7CiAgICB9CiAgfQogIHJldHVybiAwOwp9CgppbnQgd2FpdFBpZCh2b2lkKSB7CiAgaW50IHJldF9waWQsIGV4aXRfc3RhdHVzOwogIGludCBpOwogIGludCBwaWRfYVs1XSA9IHswLCAwLCAwLCAwLCAwfTsKCiAgZm9yIChpID0gMDsgaSA8IDU7IGkrKykgewogICAgcGlkX2FbaV0gPSBmb3JrKCk7CiAgICBpZiAocGlkX2FbaV0gPT0gMCkgeyAKICAgICAgcHJpbnRmKDEsICIlZCAlZFxuIiwgZ2V0cGlkKCksIGdldHBpZCgpICsgNCk7CiAgICAgIGV4aXQoZ2V0cGlkKCkgKyA0KTsKICAgIH0KICB9CiAgc2xlZXAoNSk7CiAgcHJpbnRmKDEsICIlZFxuIiwgcGlkX2FbM10pOwogIHJldF9waWQgPSB3YWl0cGlkKHBpZF9hWzNdLCAmZXhpdF9zdGF0dXMsIDApOwogIHByaW50ZigxLCAiJWQrJWQrJWRcbiIsIHJldF9waWQsIGV4aXRfc3RhdHVzLCBwaWRfYVszXSArIDQpOwogIHNsZWVwKDUpOwogIHByaW50ZigxLCAiJWRcbiIsIHBpZF9hWzFdKTsKICByZXRfcGlkID0gd2FpdHBpZChwaWRfYVsxXSwgJmV4aXRfc3RhdHVzLCAwKTsKICBwcmludGYoMSwgIiVkKyVkKyVkXG4iLCByZXRfcGlkLCBleGl0X3N0YXR1cywgcGlkX2FbMV0gKyA0KTsKICBzbGVlcCg1KTsKICBwcmludGYoMSwgIiVkXG4iLCBwaWRfYVsyXSk7CiAgcmV0X3BpZCA9IHdhaXRwaWQocGlkX2FbMl0sICZleGl0X3N0YXR1cywgMCk7CiAgcHJpbnRmKDEsICIlZCslZCslZFxuIiwgcmV0X3BpZCwgZXhpdF9zdGF0dXMsIHBpZF9hWzJdICsgNCk7CiAgc2xlZXAoNSk7CiAgcHJpbnRmKDEsICIlZFxuIiwgcGlkX2FbMF0pOwogIHJldF9waWQgPSB3YWl0cGlkKHBpZF9hWzBdLCAmZXhpdF9zdGF0dXMsIDApOwogIHByaW50ZigxLCAiJWQrJWQrJWRcbiIsIHJldF9waWQsIGV4aXRfc3RhdHVzLCBwaWRfYVswXSArIDQpOwogIHNsZWVwKDUpOwogIHByaW50ZigxLCAiJWRcbiIsIHBpZF9hWzRdKTsKICByZXRfcGlkID0gd2FpdHBpZChwaWRfYVs0XSwgJmV4aXRfc3RhdHVzLCAwKTsKICBwcmludGYoMSwgIiVkKyVkKyVkXG4iLCByZXRfcGlkLCBleGl0X3N0YXR1cywgcGlkX2FbNF0gKyA0KTsKCiAgcmV0X3BpZCA9IHdhaXRwaWQoOTk5OSwgJmV4aXRfc3RhdHVzLCAwKTsKICBwcmludGYoMSwgIiVkXG4iLCByZXRfcGlkKTsKCiAgcmV0X3BpZCA9IHdhaXRwaWQoOTk5OSwgKGludCAqKTB4ZmZmZmZmZmYsIDApOwogIHByaW50ZigxLCAiJWRcbiIsIHJldF9waWQpOwoKICByZXR1cm4gMDsKfQ=="""


from pwn import *
import yaml
import base64
import re

def populate_makefile(filename):
    c = open('Makefile', 'r').read().replace(" -Werror", " ")
    uprogs = re.findall(r'UPROGS=([\w\W]*)fs\.img: mkfs', c)[0].replace("\\\n",'').split()
    uprogs.insert(0, f'_{filename}')
    uprogs = " ".join(uprogs)
    c = re.sub(r'UPROGS=([\w\W]*)fs\.img: mkfs', f'UPROGS={uprogs} \nfs.img: mkfs', c)
    open("Makefile", 'w').write(c)

def post_to_gh(obtained, total):
  """
  Write points to for GitHub Actions
  """
  with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
      out.write(f'points={obtained}\n')
      out.write(f'total_points={total}\n')
  print(f"::notice title=Autograding complete::Points {obtained}/{total}")
  print(f"::notice title=Autograding report::{{\"totalPoints\":{obtained},\"maxPoints\":{total}}}")

code = base64.b64decode(code)

rubrics = yaml.safe_load(rubrics)
full = 0
for rubric in rubrics:
    full += rubric["points"]

populate_makefile("lab1_autograde")

with open("lab1_autograde.c", 'wb') as f:   
    f.write(code)

p = process("make qemu-nox".split())

points = 0
errors = []

try:
    p.recvuntil(b"init: starting sh\n$", timeout=10)
except:
    print("[!]Failed to compile and start xv6 with testsuite")
    print("[!]Compile log:", p.recvall().decode('latin-1'))
    print(f"Your score: {points} / {full}")
    post_to_gh(points, full)
    exit(1)


for rubric in rubrics:
    print(f"[!]Checking [{rubric['name']}]")
    try:
        if "cmd" in rubric:
            p.sendline(rubric["cmd"].encode())
        recv = p.recvuntil(rubric["expect"].encode(), timeout=5).decode('latin-1')
        if rubric["expect"] not in recv:
            raise Exception("Wrong output")
        points += rubric["points"]
    except:
        errors.append(rubric["note"])

if errors:
    print("[!]Errors:")
    for error in errors:
        print("    " + error)
else:
    print("[!]All check passed!")
print("=======")
print(f"Your score: {points} / {full}")
post_to_gh(points, full)

if errors:
    exit(1)
