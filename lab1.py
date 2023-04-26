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

code = """I2luY2x1ZGUgInR5cGVzLmgiCiNpbmNsdWRlICJ1c2VyLmgiCgojZGVmaW5lIFdOT0hBTkcgCTEKCmludCBtYWluKGludCBhcmdjLCBjaGFyICphcmd2W10pCnsKCWludCBnZXRQYXJlbnQodm9pZCk7CglpbnQgZXhpdFdhaXQodm9pZCk7CglpbnQgd2FpdFBpZCh2b2lkKTsKICBpbnQgd2FpdE5vdGhpbmcodm9pZCk7CgogIHByaW50ZigxLCAiXG5sYWIjMVxuIik7CiAgaWYgKGF0b2koYXJndlsxXSkgPT0gMikKCSAgd2FpdFBpZCgpOwogIGVsc2UgaWYgKGF0b2koYXJndlsxXSkgPT0gMSkKICAgIGV4aXRXYWl0KCk7ICAKICBlbHNlIGlmIChhdG9pKGFyZ3ZbMV0pID09IDMpCiAgICB3YWl0Tm90aGluZygpOwogICAgLy8gRW5kIG9mIHRlc3QKCSBleGl0KDApOwoJIHJldHVybiAwOwogfQogIGludCB3YWl0Tm90aGluZyh2b2lkKXsKICAgIGludCByZXQsIGV4aXRfc3RhdHVzID0gLTE7CiAgICByZXQgPSB3YWl0KCZleGl0X3N0YXR1cyk7CiAgICBwcmludGYoMSwgIiVkICVkXG4iLCByZXQsIGV4aXRfc3RhdHVzKTsKICAgIHJldHVybiAwOwogfQoKaW50IGV4aXRXYWl0KHZvaWQpIHsKCSAgaW50IHBpZCwgcmV0X3BpZCwgZXhpdF9zdGF0dXM7CiAgICBpbnQgaTsKICAvLyB1c2UgdGhpcyBwYXJ0IHRvIHRlc3QgZXhpdChpbnQgc3RhdHVzKSBhbmQgd2FpdChpbnQqIHN0YXR1cykKIAovLyAgIHByaW50ZigxLCAiXG4gIFBhcnRzIGEgJiBiKSB0ZXN0aW5nIGV4aXQoaW50IHN0YXR1cykgYW5kIHdhaXQoaW50KiBzdGF0dXMpOlxuIik7CgogIGZvciAoaSA9IDA7IGkgPCAyOyBpKyspIHsKICAgIHBpZCA9IGZvcmsoKTsKICAgIGlmIChwaWQgPT0gMCkgeyAvLyBvbmx5IHRoZSBjaGlsZCBleGVjdXRlZCB0aGlzIGNvZGUKICAgICAgaWYgKGkgPT0gMCl7CiAgICAgICAgcHJpbnRmKDEsICIlZCAlZFxuIiwgZ2V0cGlkKCksIDApOwogICAgICAgIGV4aXQoMCk7CiAgICAgIH0KICAgICAgZWxzZXsKCSAgICAgIHByaW50ZigxLCAiJWQgJWRcbiIgLGdldHBpZCgpLCAtMSk7CiAgICAgICAgZXhpdCgtMSk7CiAgICAgIH0gCiAgICB9IGVsc2UgaWYgKHBpZCA+IDApIHsgLy8gb25seSB0aGUgcGFyZW50IGV4ZWN1dGVzIHRoaXMgY29kZQogICAgICByZXRfcGlkID0gd2FpdCgmZXhpdF9zdGF0dXMpOwogICAgICBwcmludGYoMSwgIiVkKyVkXG4iLCByZXRfcGlkLCBleGl0X3N0YXR1cyk7CiAgICB9IGVsc2UgeyAvLyBzb21ldGhpbmcgd2VudCB3cm9uZyB3aXRoIGZvcmsgc3lzdGVtIGNhbGwKCSAgICBwcmludGYoMiwgIlxuRXJyb3IgdXNpbmcgZm9ya1xuIik7CiAgICAgIGV4aXQoLTEpOwogICAgfQogIH0KICByZXR1cm4gMDsKfQoKaW50IHdhaXRQaWQodm9pZCl7CgkKICBpbnQgcmV0X3BpZCwgZXhpdF9zdGF0dXM7CiAgaW50IGk7CiAgaW50IHBpZF9hWzVdPXswLCAwLCAwLCAwLCAwfTsKIC8vIHVzZSB0aGlzIHBhcnQgdG8gdGVzdCB3YWl0KGludCBwaWQsIGludCogc3RhdHVzLCBpbnQgb3B0aW9ucykKCi8vICAgcHJpbnRmKDEsICJcbiAgUGFydCBjKSB0ZXN0aW5nIHdhaXRwaWQoaW50IHBpZCwgaW50KiBzdGF0dXMsIGludCBvcHRpb25zKTpcbiIpOwoKCWZvciAoaSA9IDA7IGkgPDU7IGkrKykgewoJCXBpZF9hW2ldID0gZm9yaygpOwoJCWlmIChwaWRfYVtpXSA9PSAwKSB7IC8vIG9ubHkgdGhlIGNoaWxkIGV4ZWN1dGVkIHRoaXMgY29kZQoJCQlwcmludGYoMSwgIiVkICVkXG4iLCBnZXRwaWQoKSwgZ2V0cGlkKCkgKyA0KTsKCQkJZXhpdChnZXRwaWQoKSArIDQpOwoJCX0KCX0KICBzbGVlcCg1KTsKICBwcmludGYoMSwgIiVkXG4iLHBpZF9hWzNdKTsKICByZXRfcGlkID0gd2FpdHBpZChwaWRfYVszXSwgJmV4aXRfc3RhdHVzLCAwKTsKICBwcmludGYoMSwgIiVkKyVkKyVkXG4iLHJldF9waWQsIGV4aXRfc3RhdHVzLCBwaWRfYVszXSArIDQpOwogIHNsZWVwKDUpOwogIHByaW50ZigxLCAiJWRcbiIscGlkX2FbMV0pOwogIHJldF9waWQgPSB3YWl0cGlkKHBpZF9hWzFdLCAmZXhpdF9zdGF0dXMsIDApOwogIHByaW50ZigxLCAiJWQrJWQrJWRcbiIscmV0X3BpZCwgZXhpdF9zdGF0dXMsIHBpZF9hWzFdICsgNCk7CiAgc2xlZXAoNSk7CiAgcHJpbnRmKDEsICIlZFxuIixwaWRfYVsyXSk7CiAgcmV0X3BpZCA9IHdhaXRwaWQocGlkX2FbMl0sICZleGl0X3N0YXR1cywgMCk7CiAgcHJpbnRmKDEsICIlZCslZCslZFxuIixyZXRfcGlkLCBleGl0X3N0YXR1cywgcGlkX2FbMl0gKyA0KTsKICBzbGVlcCg1KTsKICBwcmludGYoMSwgIiVkXG4iLHBpZF9hWzBdKTsKICByZXRfcGlkID0gd2FpdHBpZChwaWRfYVswXSwgJmV4aXRfc3RhdHVzLCAwKTsKICBwcmludGYoMSwgIiVkKyVkKyVkXG4iLHJldF9waWQsIGV4aXRfc3RhdHVzLCBwaWRfYVswXSArIDQpOwogIHNsZWVwKDUpOwogIHByaW50ZigxLCAiJWRcbiIscGlkX2FbNF0pOwogIHJldF9waWQgPSB3YWl0cGlkKHBpZF9hWzRdLCAmZXhpdF9zdGF0dXMsIDApOwogIHByaW50ZigxLCAiJWQrJWQrJWRcbiIscmV0X3BpZCwgZXhpdF9zdGF0dXMsIHBpZF9hWzRdICsgNCk7CgogIHJldF9waWQgPSB3YWl0cGlkKDk5OTksICZleGl0X3N0YXR1cywgMCk7CiAgcHJpbnRmKDEsICIlZFxuIixyZXRfcGlkKTsKICAvL3ByaW50ZigxLCAiXG4gVGhpcyBpcyB0aGUgcGFyZW50OiBDaGlsZCMgJWQgaGFzIGV4aXRlZCB3aXRoIHN0YXR1cyAlZFxuIixyZXRfcGlkLCBleGl0X3N0YXR1cyk7CgogIHJldF9waWQgPSB3YWl0cGlkKDk5OTksIChpbnQqKSAweGZmZmZmZmZmLCAwKTsKICBwcmludGYoMSwgIiVkXG4iLHJldF9waWQpOwoKICByZXR1cm4gMDsKfQ=="""


from pwn import *
import yaml
import base64
import re

def populate_makefile(filename):
    c = open('Makefile', 'r').read()
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
