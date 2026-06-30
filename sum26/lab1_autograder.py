rubrics = r"""
- points: 10
  cmd: "lab1_autograde 1"
  expect: "4 0"
  note: "Fork failed"
  name: "Exit & Wait - Fork first child process"

- points: 10
  expect: "4+0"
  note: "[Exit & Wait]Failed to obtain correct first child process exit status"
  name: "Exit & Wait - Wait for first child process"

- points: 0
  expect: "5 -1"
  note: "[Exit & Wait]Fork second child process failed"
  name: "Exit & Wait - Fork second child process"

- points: 20
  expect: "5+-1"
  note: "[Exit & Wait]Failed to obtain correct second child process exit status"
  name: "Exit & Wait - Wait for second child process"

- points: 0
  cmd: "lab1_autograde 2"
  expect: "11 15"
  note: "[Waitpid]Failed to create 5 child processes"
  name: "Waitpid - create 5 child processes"

- points: 35
  expect: "10\n10+14+14\n8\n8+12+12\n9\n9+13+13\n7\n7+11+11\n11\n11+15+15"
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

- points: 10
  cmd: "lab1_autograde 4"
  expect: "0+1+1"
  note: "[getSiblings]Failed to correctly count siblings (expected parent to see 0, then each of 2 forked children to report 1 sibling)"
  name: "getSiblings - parent and two children correctly count siblings"

"""

code = """I2luY2x1ZGUgInR5cGVzLmgiCiNpbmNsdWRlICJ1c2VyLmgiCgojZGVmaW5lIFdOT0hBTkcgCTEKCmludCBtYWluKGludCBhcmdjLCBjaGFyICphcmd2W10pCnsKCWludCBnZXRQYXJlbnQodm9pZCk7CglpbnQgZXhpdFdhaXQodm9pZCk7CglpbnQgd2FpdFBpZCh2b2lkKTsKICBpbnQgd2FpdE5vdGhpbmcodm9pZCk7CiAgaW50IHRlc3RHZXRTaWJsaW5ncyh2b2lkKTsKCiAgcHJpbnRmKDEsICJcbmxhYiMxXG4iKTsKICBpZiAoYXRvaShhcmd2WzFdKSA9PSAyKQoJICB3YWl0UGlkKCk7CiAgZWxzZSBpZiAoYXRvaShhcmd2WzFdKSA9PSAxKQogICAgZXhpdFdhaXQoKTsgIAogIGVsc2UgaWYgKGF0b2koYXJndlsxXSkgPT0gMykKICAgIHdhaXROb3RoaW5nKCk7CiAgZWxzZSBpZiAoYXRvaShhcmd2WzFdKSA9PSA0KQogICAgdGVzdEdldFNpYmxpbmdzKCk7CiAgICAvLyBFbmQgb2YgdGVzdAoJIGV4aXQoMCk7CgkgcmV0dXJuIDA7CiB9CiAgaW50IHdhaXROb3RoaW5nKHZvaWQpewogICAgaW50IHJldCwgZXhpdF9zdGF0dXMgPSAtMTsKICAgIHJldCA9IHdhaXQoJmV4aXRfc3RhdHVzKTsKICAgIHByaW50ZigxLCAiJWQgJWRcbiIsIHJldCwgZXhpdF9zdGF0dXMpOwogICAgcmV0dXJuIDA7CiB9CgppbnQgdGVzdEdldFNpYmxpbmdzKHZvaWQpewogIGludCBuLCBuMSwgbjIsIHBpZDEsIHBpZDI7CgogIG4gPSBnZXRTaWJsaW5ncygpOwogIHByaW50ZigxLCAiJWQiLCBuKTsKCiAgcGlkMSA9IGZvcmsoKTsKICBpZihwaWQxID09IDApewogICAgc2xlZXAoNSk7CiAgICBuMSA9IGdldFNpYmxpbmdzKCk7CiAgICBwcmludGYoMSwgIislZCIsIG4xKTsKICAgIGV4aXQoMCk7CiAgfQoKICBwaWQyID0gZm9yaygpOwogIGlmKHBpZDIgPT0gMCl7CiAgICBzbGVlcCg1KTsKICAgIG4yID0gZ2V0U2libGluZ3MoKTsKICAgIHByaW50ZigxLCAiKyVkIiwgbjIpOwogICAgZXhpdCgwKTsKICB9CgogIHdhaXQoMCk7CiAgd2FpdCgwKTsKICBwcmludGYoMSwgIlxuIik7CiAgcmV0dXJuIDA7Cn0KCmludCBleGl0V2FpdCh2b2lkKSB7CgkgIGludCBwaWQsIHJldF9waWQsIGV4aXRfc3RhdHVzOwogICAgaW50IGk7CiAgLy8gdXNlIHRoaXMgcGFydCB0byB0ZXN0IGV4aXQoaW50IHN0YXR1cykgYW5kIHdhaXQoaW50KiBzdGF0dXMpCiAKLy8gICBwcmludGYoMSwgIlxuICBQYXJ0cyBhICYgYikgdGVzdGluZyBleGl0KGludCBzdGF0dXMpIGFuZCB3YWl0KGludCogc3RhdHVzKTpcbiIpOwoKICBmb3IgKGkgPSAwOyBpIDwgMjsgaSsrKSB7CiAgICBwaWQgPSBmb3JrKCk7CiAgICBpZiAocGlkID09IDApIHsgLy8gb25seSB0aGUgY2hpbGQgZXhlY3V0ZWQgdGhpcyBjb2RlCiAgICAgIGlmIChpID09IDApewogICAgICAgIHByaW50ZigxLCAiJWQgJWRcbiIsIGdldHBpZCgpLCAwKTsKICAgICAgICBleGl0KDApOwogICAgICB9CiAgICAgIGVsc2V7CgkgICAgICBwcmludGYoMSwgIiVkICVkXG4iICxnZXRwaWQoKSwgLTEpOwogICAgICAgIGV4aXQoLTEpOwogICAgICB9IAogICAgfSBlbHNlIGlmIChwaWQgPiAwKSB7IC8vIG9ubHkgdGhlIHBhcmVudCBleGVjdXRlcyB0aGlzIGNvZGUKICAgICAgcmV0X3BpZCA9IHdhaXQoJmV4aXRfc3RhdHVzKTsKICAgICAgcHJpbnRmKDEsICIlZCslZFxuIiwgcmV0X3BpZCwgZXhpdF9zdGF0dXMpOwogICAgfSBlbHNlIHsgLy8gc29tZXRoaW5nIHdlbnQgd3Jvbmcgd2l0aCBmb3JrIHN5c3RlbSBjYWxsCgkgICAgcHJpbnRmKDIsICJcbkVycm9yIHVzaW5nIGZvcmtcbiIpOwogICAgICBleGl0KC0xKTsKICAgIH0KICB9CiAgcmV0dXJuIDA7Cn0KCmludCB3YWl0UGlkKHZvaWQpewoJCiAgaW50IHJldF9waWQsIGV4aXRfc3RhdHVzOwogIGludCBpOwogIGludCBwaWRfYVs1XT17MCwgMCwgMCwgMCwgMH07CiAvLyB1c2UgdGhpcyBwYXJ0IHRvIHRlc3Qgd2FpdChpbnQgcGlkLCBpbnQqIHN0YXR1cywgaW50IG9wdGlvbnMpCgovLyAgIHByaW50ZigxLCAiXG4gIFBhcnQgYykgdGVzdGluZyB3YWl0cGlkKGludCBwaWQsIGludCogc3RhdHVzLCBpbnQgb3B0aW9ucyk6XG4iKTsKCglmb3IgKGkgPSAwOyBpIDw1OyBpKyspIHsKCQlwaWRfYVtpXSA9IGZvcmsoKTsKCQlpZiAocGlkX2FbaV0gPT0gMCkgeyAvLyBvbmx5IHRoZSBjaGlsZCBleGVjdXRlZCB0aGlzIGNvZGUKCQkJcHJpbnRmKDEsICIlZCAlZFxuIiwgZ2V0cGlkKCksIGdldHBpZCgpICsgNCk7CgkJCWV4aXQoZ2V0cGlkKCkgKyA0KTsKCQl9Cgl9CiAgc2xlZXAoNSk7CiAgcHJpbnRmKDEsICIlZFxuIixwaWRfYVszXSk7CiAgcmV0X3BpZCA9IHdhaXRwaWQocGlkX2FbM10sICZleGl0X3N0YXR1cywgMCk7CiAgcHJpbnRmKDEsICIlZCslZCslZFxuIixyZXRfcGlkLCBleGl0X3N0YXR1cywgcGlkX2FbM10gKyA0KTsKICBzbGVlcCg1KTsKICBwcmludGYoMSwgIiVkXG4iLHBpZF9hWzFdKTsKICByZXRfcGlkID0gd2FpdHBpZChwaWRfYVsxXSwgJmV4aXRfc3RhdHVzLCAwKTsKICBwcmludGYoMSwgIiVkKyVkKyVkXG4iLHJldF9waWQsIGV4aXRfc3RhdHVzLCBwaWRfYVsxXSArIDQpOwogIHNsZWVwKDUpOwogIHByaW50ZigxLCAiJWRcbiIscGlkX2FbMl0pOwogIHJldF9waWQgPSB3YWl0cGlkKHBpZF9hWzJdLCAmZXhpdF9zdGF0dXMsIDApOwogIHByaW50ZigxLCAiJWQrJWQrJWRcbiIscmV0X3BpZCwgZXhpdF9zdGF0dXMsIHBpZF9hWzJdICsgNCk7CiAgc2xlZXAoNSk7CiAgcHJpbnRmKDEsICIlZFxuIixwaWRfYVswXSk7CiAgcmV0X3BpZCA9IHdhaXRwaWQocGlkX2FbMF0sICZleGl0X3N0YXR1cywgMCk7CiAgcHJpbnRmKDEsICIlZCslZCslZFxuIixyZXRfcGlkLCBleGl0X3N0YXR1cywgcGlkX2FbMF0gKyA0KTsKICBzbGVlcCg1KTsKICBwcmludGYoMSwgIiVkXG4iLHBpZF9hWzRdKTsKICByZXRfcGlkID0gd2FpdHBpZChwaWRfYVs0XSwgJmV4aXRfc3RhdHVzLCAwKTsKICBwcmludGYoMSwgIiVkKyVkKyVkXG4iLHJldF9waWQsIGV4aXRfc3RhdHVzLCBwaWRfYVs0XSArIDQpOwoKICByZXRfcGlkID0gd2FpdHBpZCg5OTk5LCAmZXhpdF9zdGF0dXMsIDApOwogIHByaW50ZigxLCAiJWRcbiIscmV0X3BpZCk7CiAgLy9wcmludGYoMSwgIlxuIFRoaXMgaXMgdGhlIHBhcmVudDogQ2hpbGQjICVkIGhhcyBleGl0ZWQgd2l0aCBzdGF0dXMgJWRcbiIscmV0X3BpZCwgZXhpdF9zdGF0dXMpOwoKICByZXRfcGlkID0gd2FpdHBpZCg5OTk5LCAoaW50KikgMHhmZmZmZmZmZiwgMCk7CiAgcHJpbnRmKDEsICIlZFxuIixyZXRfcGlkKTsKCiAgcmV0dXJuIDA7Cn0K"""


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

code = base64.b64decode(code)

rubrics = yaml.safe_load(rubrics)
full = 0

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
    print("[!]Errors:")
    for error in errors:
        print("    " + error)
else:
    print("[!]All check passed!")
print("=======")
print(f"Your score: {points} / {full}")

if errors:
    exit(1)
