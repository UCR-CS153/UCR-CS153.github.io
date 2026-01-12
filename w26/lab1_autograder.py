rubrics = r"""
- points: 5
  cmd: "lab1_autograde 4"
  expect: "Getinfo: invalid parameters."
  note: "Part 1: Failed to handle invalid parameters"
  name: "Part 1 - Invalid Parameters"

- points: 10
  expect: "Parent: 3"
  note: "Part 1: Failed to print correct parent PID"
  name: "Part 1 - Parent PID"

- points: 10
  expect: "Sibling: 5"
  note: "Part 1: Failed to print correct sibling PID"
  name: "Part 1 - Sibling PID"

- points: 5
  cmd: "lab1_autograde 1"
  expect: "Child 1 Running"
  note: "Fork failed"
  name: "Exit & Wait - Fork first child process"

- points: 5
  expect: "Child 1: Match 0"
  note: "[Exit & Wait]Failed to obtain correct first child process exit status"
  name: "Exit & Wait - Wait for first child process"

- points: 15
  expect: "Child 2: Match -1"
  note: "[Exit & Wait]Failed to obtain correct second child process exit status"
  name: "Exit & Wait - Wait for second child process"

- points: 0
  cmd: "lab1_autograde 2"
  expect: "Check 1"
  note: "[Waitpid]Failed to create 5 child processes"
  name: "Waitpid - create 5 child processes"

- points: 40
  expect: "Test 1: OK\nCheck 2\nTest 2: OK\nCheck 3\nTest 3: OK\nCheck 4\nTest 4: OK\nCheck 5\nTest 5: OK"
  note: "[Waitpid]Child process exit status is incorrect or waitpid didn't wait for correct PID"
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

code = """I2luY2x1ZGUgInR5cGVzLmgiCiNpbmNsdWRlICJ1c2VyLmgiCiNkZWZpbmUgV05PSEFORyAxCmludCBnZXRpbmZvKGludCk7CmludCBtYWluKGludCBhcmdjLCBjaGFyICphcmd2W10pIHsKICBpbnQgZXhpdFdhaXQodm9pZCk7CiAgaW50IHdhaXRQaWQodm9pZCk7CiAgaW50IHdhaXROb3RoaW5nKHZvaWQpOwogIHZvaWQgdGVzdEdldEluZm8odm9pZCk7CiAgcHJpbnRmKDEsICJcbmxhYiMxXG4iKTsKICBpZiAoYXRvaShhcmd2WzFdKSA9PSAxKSBleGl0V2FpdCgpOwogIGVsc2UgaWYgKGF0b2koYXJndlsxXSkgPT0gMikgd2FpdFBpZCgpOwogIGVsc2UgaWYgKGF0b2koYXJndlsxXSkgPT0gMykgd2FpdE5vdGhpbmcoKTsKICBlbHNlIGlmIChhdG9pKGFyZ3ZbMV0pID09IDQpIHRlc3RHZXRJbmZvKCk7CiAgZXhpdCgwKTsKICByZXR1cm4gMDsKfQp2b2lkIHRlc3RHZXRJbmZvKHZvaWQpIHsKICBpbnQgcGlkMTsKICBnZXRpbmZvKDApOwogIGlmIChmb3JrKCkgPT0gMCkgeyBwcmludGYoMSwgIlBhcmVudDogIik7IGdldGluZm8oMSk7IHByaW50ZigxLCAiXG4iKTsgZXhpdCgwKTsgfQogIHdhaXQoMCk7CiAgcGlkMSA9IGZvcmsoKTsKICBpZiAocGlkMSA9PSAwKSB7IHNsZWVwKDEwMCk7IGV4aXQoMCk7IH0KICBpZiAoZm9yaygpID09IDApIHsgcHJpbnRmKDEsICJTaWJsaW5nOiAiKTsgZ2V0aW5mbygyKTsgcHJpbnRmKDEsICJcbiIpOyBleGl0KDApOyB9CiAgd2FpdCgwKTsga2lsbChwaWQxKTsgd2FpdCgwKTsKfQppbnQgd2FpdE5vdGhpbmcodm9pZCkgewogIGludCByZXQsIGV4aXRfc3RhdHVzID0gLTE7CiAgcmV0ID0gd2FpdCgmZXhpdF9zdGF0dXMpOwogIHByaW50ZigxLCAiJWQgJWRcbiIsIHJldCwgZXhpdF9zdGF0dXMpOwogIHJldHVybiAwOwp9CmludCBleGl0V2FpdCh2b2lkKSB7CiAgaW50IHBpZCwgcmV0X3BpZCwgZXhpdF9zdGF0dXM7CiAgaW50IGk7CiAgZm9yIChpID0gMDsgaSA8IDI7IGkrKykgewogICAgcGlkID0gZm9yaygpOwogICAgaWYgKHBpZCA9PSAwKSB7CiAgICAgIGlmIChpID09IDApIHsgcHJpbnRmKDEsICJDaGlsZCAxIFJ1bm5pbmdcbiIpOyBleGl0KDApOyB9CiAgICAgIGVsc2UgeyBleGl0KC0xKTsgfQogICAgfSBlbHNlIGlmIChwaWQgPiAwKSB7CiAgICAgIHJldF9waWQgPSB3YWl0KCZleGl0X3N0YXR1cyk7CiAgICAgIGlmIChpID09IDApIHsKICAgICAgICBpZihyZXRfcGlkID09IHBpZCAmJiBleGl0X3N0YXR1cyA9PSAwKSBwcmludGYoMSwgIkNoaWxkIDE6IE1hdGNoIDBcbiIpOwogICAgICAgIGVsc2UgcHJpbnRmKDEsICJDaGlsZCAxOiBGYWlsIChHb3QgJWQgJWRcbiIsIHJldF9waWQsIGV4aXRfc3RhdHVzKTsKICAgICAgfSBlbHNlIHsKICAgICAgICBpZihyZXRfcGlkID09IHBpZCAmJiBleGl0X3N0YXR1cyA9PSAtMSkgcHJpbnRmKDEsICJDaGlsZCAyOiBNYXRjaCAtMVxuIik7CiAgICAgICAgZWxzZSBwcmludGYoMSwgIkNoaWxkIDI6IEZhaWwgKEdvdCAlZCAlZClcbiIsIHJldF9waWQsIGV4aXRfc3RhdHVzKTsKICAgICAgfQogICAgfSBlbHNlIHsgcHJpbnRmKDIsICJcbkVycm9yIHVzaW5nIGZvcmtcbiIpOyBleGl0KC0xKTsgfQogIH0KICByZXR1cm4gMDsKfQppbnQgd2FpdFBpZCh2b2lkKSB7CiAgaW50IHJldF9waWQsIGV4aXRfc3RhdHVzOwogIGludCBpOwogIGludCBwaWRfYVs1XSA9IHswLCAwLCAwLCAwLCAwfTsKICBmb3IgKGkgPSAwOyBpIDwgNTsgaSsrKSB7CiAgICBwaWRfYVtpXSA9IGZvcmsoKTsKICAgIGlmIChwaWRfYVtpXSA9PSAwKSB7IGV4aXQoZ2V0cGlkKCkgKyA0KTsgfQogIH0KICBzbGVlcCg1KTsKICBwcmludGYoMSwgIkNoZWNrIDFcbiIpOwogIHJldF9waWQgPSB3YWl0cGlkKHBpZF9hWzNdLCAmZXhpdF9zdGF0dXMsIDApOwogIGlmKHJldF9waWQgPT0gcGlkX2FbM10gJiYgZXhpdF9zdGF0dXMgPT0gcGlkX2FbM10gKyA0KSBwcmludGYoMSwgIlRlc3QgMTogT0tcbiIpOwogIGVsc2UgcHJpbnRmKDEsICJUZXN0IDE6IEZhaWxcbiIpOwogIHNsZWVwKDUpOwogIHByaW50ZigxLCAiQ2hlY2sgMlxuIik7CiAgcmV0X3BpZCA9IHdhaXRwaWQocGlkX2FbMV0sICZleGl0X3N0YXR1cywgMCk7CiAgaWYocmV0X3BpZCA9PSBwaWRfYVsxXSAmJiBleGl0X3N0YXR1cyA9PSBwaWRfYVsxXSArIDQpIHByaW50ZigxLCAiVGVzdCAyOiBPS1xuIik7CiAgZWxzZSBwcmludGYoMSwgIlRlc3QgMjogRmFpbFxuIik7CiAgc2xlZXAoNSk7CiAgcHJpbnRmKDEsICJDaGVjayAzXG4iKTsKICByZXRfcGlkID0gd2FpdHBpZChwaWRfYVsyXSwgJmV4aXRfc3RhdHVzLCAwKTsKICBpZihyZXRfcGlkID09IHBpZF9hWzJdICYmIGV4aXRfc3RhdHVzID09IHBpZF9hWzJdICsgNCkgcHJpbnRmKDEsICJUZXN0IDM6IE9LXG4iKTsKICBlbHNlIHByaW50ZigxLCAiVGVzdCAzOiBGYWlsXG4iKTsKICBzbGVlcCg1KTsKICBwcmludGYoMSwgIkNoZWNrIDRcbiIpOwogIHJldF9waWQgPSB3YWl0cGlkKHBpZF9hWzBdLCAmZXhpdF9zdGF0dXMsIDApOwogIGlmKHJldF9waWQgPT0gcGlkX2FbMF0gJiYgZXhpdF9zdGF0dXMgPT0gcGlkX2FbMF0gKyA0KSBwcmludGYoMSwgIlRlc3QgNDogT0tcbiIpOwogIGVsc2UgcHJpbnRmKDEsICJUZXN0IDQ6IEZhaWxcbiIpOwogIHNsZWVwKDUpOwogIHByaW50ZigxLCAiQ2hlY2sgNVxuIik7CiAgcmV0X3BpZCA9IHdhaXRwaWQocGlkX2FbNF0sICZleGl0X3N0YXR1cywgMCk7CiAgaWYocmV0X3BpZCA9PSBwaWRfYVs0XSAmJiBleGl0X3N0YXR1cyA9PSBwaWRfYVs0XSArIDQpIHByaW50ZigxLCAiVGVzdCA1OiBPS1xuIik7CiAgZWxzZSBwcmludGYoMSwgIlRlc3QgNTogRmFpbFxuIik7CiAgcmV0X3BpZCA9IHdhaXRwaWQoOTk5OSwgJmV4aXRfc3RhdHVzLCAwKTsKICBwcmludGYoMSwgIiVkXG4iLCByZXRfcGlkKTsKICByZXRfcGlkID0gd2FpdHBpZCg5OTk5LCAoaW50ICopMHhmZmZmZmZmZiwgMCk7CiAgcHJpbnRmKDEsICIlZFxuIiwgcmV0X3BpZCk7CiAgcmV0dXJuIDA7Cn0="""

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
        recv = p.recvuntil(rubric["expect"].encode(), timeout=10).decode('latin-1')
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
