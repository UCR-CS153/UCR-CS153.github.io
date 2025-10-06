rubrics = r"""
- points: 5
  cmd: "lab1_autograde 1"
  expect: "4 0"
  note: "Fork failed"
  name: "Exit & Wait - Fork first child process"

- points: 5
  expect: "4+0"
  note: "[Exit & Wait]Failed to obtain correct first child process exit status"
  name: "Exit & Wait - Wait for first child process"

- points: 0
  expect: "5 -1"
  note: "[Exit & Wait]Fork second child process failed"
  name: "Exit & Wait - Fork second child process"

- points: 15
  expect: "5+-1"
  note: "[Exit & Wait]Failed to obtain correct second child process exit status"
  name: "Exit & Wait - Wait for second child process"

- points: 0
  cmd: "lab1_autograde 2"
  expect: "11 15"
  note: "[Waitpid]Failed to create 5 child processes"
  name: "Waitpid - create 5 child processes"

- points: 40
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

"""

code = """I2luY2x1ZGUgInR5cGVzLmgiCiNpbmNsdWRlICJ1c2VyLmgiCgojZGVmaW5lIFdOT0hBTkcgMQoKaW50IG1haW4oaW50IGFyZ2MsIGNoYXIgKmFyZ3ZbXSkgewogIGludCBnZXRQYXJlbnQodm9pZCk7CiAgaW50IGV4aXRXYWl0KHZvaWQpOwogIGludCB3YWl0UGlkKHZvaWQpOwogIGludCB3YWl0Tm90aGluZyh2b2lkKTsKCiAgcHJpbnRmKDEsICJcbmxhYiMxXG4iKTsKICBpZiAoYXRvaShhcmd2WzFdKSA9PSAyKQogICAgd2FpdFBpZCgpOwogIGVsc2UgaWYgKGF0b2koYXJndlsxXSkgPT0gMSkKICAgIGV4aXRXYWl0KCk7CiAgZWxzZSBpZiAoYXRvaShhcmd2WzFdKSA9PSAzKQogICAgd2FpdE5vdGhpbmcoKTsKICAvLyBFbmQgb2YgdGVzdAogIGV4aXQoMCk7CiAgcmV0dXJuIDA7Cn0KCmludCB3YWl0Tm90aGluZyh2b2lkKSB7CiAgaW50IHJldCwgZXhpdF9zdGF0dXMgPSAtMTsKICByZXQgPSB3YWl0KCZleGl0X3N0YXR1cyk7CiAgcHJpbnRmKDEsICIlZCAlZFxuIiwgcmV0LCBleGl0X3N0YXR1cyk7CiAgcmV0dXJuIDA7Cn0KCmludCBleGl0V2FpdCh2b2lkKSB7CiAgaW50IHBpZCwgcmV0X3BpZCwgZXhpdF9zdGF0dXM7CiAgaW50IGk7CiAgLy8gdXNlIHRoaXMgcGFydCB0byB0ZXN0IGV4aXQoaW50IHN0YXR1cykgYW5kIHdhaXQoaW50KiBzdGF0dXMpCgogIC8vICAgcHJpbnRmKDEsICJcbiAgUGFydHMgYSAmIGIpIHRlc3RpbmcgZXhpdChpbnQgc3RhdHVzKSBhbmQgd2FpdChpbnQqCiAgLy8gICBzdGF0dXMpOlxuIik7CgogIGZvciAoaSA9IDA7IGkgPCAyOyBpKyspIHsKICAgIHBpZCA9IGZvcmsoKTsKICAgIGlmIChwaWQgPT0gMCkgeyAvLyBvbmx5IHRoZSBjaGlsZCBleGVjdXRlZCB0aGlzIGNvZGUKICAgICAgaWYgKGkgPT0gMCkgewogICAgICAgIHByaW50ZigxLCAiJWQgJWRcbiIsIGdldHBpZCgpLCAwKTsKICAgICAgICBleGl0KDApOwogICAgICB9IGVsc2UgewogICAgICAgIHByaW50ZigxLCAiJWQgJWRcbiIsIGdldHBpZCgpLCAtMSk7CiAgICAgICAgZXhpdCgtMSk7CiAgICAgIH0KICAgIH0gZWxzZSBpZiAocGlkID4gMCkgeyAvLyBvbmx5IHRoZSBwYXJlbnQgZXhlY3V0ZXMgdGhpcyBjb2RlCiAgICAgIHJldF9waWQgPSB3YWl0KCZleGl0X3N0YXR1cyk7CiAgICAgIHByaW50ZigxLCAiJWQrJWRcbiIsIHJldF9waWQsIGV4aXRfc3RhdHVzKTsKICAgIH0gZWxzZSB7IC8vIHNvbWV0aGluZyB3ZW50IHdyb25nIHdpdGggZm9yayBzeXN0ZW0gY2FsbAogICAgICBwcmludGYoMiwgIlxuRXJyb3IgdXNpbmcgZm9ya1xuIik7CiAgICAgIGV4aXQoLTEpOwogICAgfQogIH0KICByZXR1cm4gMDsKfQoKaW50IHdhaXRQaWQodm9pZCkgewoKICBpbnQgcmV0X3BpZCwgZXhpdF9zdGF0dXM7CiAgaW50IGk7CiAgaW50IHBpZF9hWzVdID0gezAsIDAsIDAsIDAsIDB9OwogIC8vIHVzZSB0aGlzIHBhcnQgdG8gdGVzdCB3YWl0KGludCBwaWQsIGludCogc3RhdHVzLCBpbnQgb3B0aW9ucykKCiAgLy8gICBwcmludGYoMSwgIlxuICBQYXJ0IGMpIHRlc3Rpbmcgd2FpdHBpZChpbnQgcGlkLCBpbnQqIHN0YXR1cywgaW50CiAgLy8gICBvcHRpb25zKTpcbiIpOwoKICBmb3IgKGkgPSAwOyBpIDwgNTsgaSsrKSB7CiAgICBwaWRfYVtpXSA9IGZvcmsoKTsKICAgIGlmIChwaWRfYVtpXSA9PSAwKSB7IC8vIG9ubHkgdGhlIGNoaWxkIGV4ZWN1dGVkIHRoaXMgY29kZQogICAgICBwcmludGYoMSwgIiVkICVkXG4iLCBnZXRwaWQoKSwgZ2V0cGlkKCkgKyA0KTsKICAgICAgZXhpdChnZXRwaWQoKSArIDQpOwogICAgfQogIH0KICBzbGVlcCg1KTsKICBwcmludGYoMSwgIiVkXG4iLCBwaWRfYVszXSk7CiAgcmV0X3BpZCA9IHdhaXRwaWQocGlkX2FbM10sICZleGl0X3N0YXR1cywgMCk7CiAgcHJpbnRmKDEsICIlZCslZCslZFxuIiwgcmV0X3BpZCwgZXhpdF9zdGF0dXMsIHBpZF9hWzNdICsgNCk7CiAgc2xlZXAoNSk7CiAgcHJpbnRmKDEsICIlZFxuIiwgcGlkX2FbMV0pOwogIHJldF9waWQgPSB3YWl0cGlkKHBpZF9hWzFdLCAmZXhpdF9zdGF0dXMsIDApOwogIHByaW50ZigxLCAiJWQrJWQrJWRcbiIsIHJldF9waWQsIGV4aXRfc3RhdHVzLCBwaWRfYVsxXSArIDQpOwogIHNsZWVwKDUpOwogIHByaW50ZigxLCAiJWRcbiIsIHBpZF9hWzJdKTsKICByZXRfcGlkID0gd2FpdHBpZChwaWRfYVsyXSwgJmV4aXRfc3RhdHVzLCAwKTsKICBwcmludGYoMSwgIiVkKyVkKyVkXG4iLCByZXRfcGlkLCBleGl0X3N0YXR1cywgcGlkX2FbMl0gKyA0KTsKICBzbGVlcCg1KTsKICBwcmludGYoMSwgIiVkXG4iLCBwaWRfYVswXSk7CiAgcmV0X3BpZCA9IHdhaXRwaWQocGlkX2FbMF0sICZleGl0X3N0YXR1cywgMCk7CiAgcHJpbnRmKDEsICIlZCslZCslZFxuIiwgcmV0X3BpZCwgZXhpdF9zdGF0dXMsIHBpZF9hWzBdICsgNCk7CiAgc2xlZXAoNSk7CiAgcHJpbnRmKDEsICIlZFxuIiwgcGlkX2FbNF0pOwogIHJldF9waWQgPSB3YWl0cGlkKHBpZF9hWzRdLCAmZXhpdF9zdGF0dXMsIDApOwogIHByaW50ZigxLCAiJWQrJWQrJWRcbiIsIHJldF9waWQsIGV4aXRfc3RhdHVzLCBwaWRfYVs0XSArIDQpOwoKICByZXRfcGlkID0gd2FpdHBpZCg5OTk5LCAmZXhpdF9zdGF0dXMsIDApOwogIHByaW50ZigxLCAiJWRcbiIsIHJldF9waWQpOwogIC8vIHByaW50ZigxLCAiXG4gVGhpcyBpcyB0aGUgcGFyZW50OiBDaGlsZCMgJWQgaGFzIGV4aXRlZCB3aXRoIHN0YXR1cwogIC8vICVkXG4iLHJldF9waWQsIGV4aXRfc3RhdHVzKTsKCiAgcmV0X3BpZCA9IHdhaXRwaWQoOTk5OSwgKGludCAqKTB4ZmZmZmZmZmYsIDApOwogIHByaW50ZigxLCAiJWRcbiIsIHJldF9waWQpOwoKICByZXR1cm4gMDsKfQ=="""


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
