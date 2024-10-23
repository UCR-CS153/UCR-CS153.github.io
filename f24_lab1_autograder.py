import yaml
import base64
import re
from pwn import *

rubrics_part1 = r"""
- points: 5
  cmd: "test_getfamily 0"
  expect: "Parent: 2\nSiblings: \nChildren: \n$"
  note: "[getfamily] getfamily failed on test case 0 "
  name: "Test 0: getfamily - No Siblings, No Children"

- points: 5
  cmd: "test_getfamily 1"
  expect: "Parent: 4\nSiblings: 6 7 \nChildren: \n$"
  note: "[getfamily] getfamily failed on test case 1 "
  name: "Test 1: getfamily - Two Sibling, No Children"

- points: 5
  cmd: "test_getfamily 2"
  expect: "Parent: 8\nSiblings: \nChildren: 10 11 \n$"
  note: "[getfamily] getfamily failed on test case 2 "
  name: "Test 2: getfamily - No Siblings, Two Children"

- points: 10
  cmd: "test_getfamily 3"
  expect: "Parent: 12\nSiblings: 14 15 \nChildren: 16 17 \n"
  note: "[getfamily] getfamily failed on test case 3 "
  name: "Test 3: getfamily - Two Siblings, Two Children"
"""

rubrics_part23 = r"""
- points: 25
  cmd: "test_exit_wait 1"
  expect: "1\n42\n-1\n0\n$"
  note: "[exit and wait] first test for exit and wait failed"
  name: "Test 1: exit and wait - Test cases with different exit statuses"

- points: 25
  cmd: "test_exit_wait 2"
  expect: "-1\n1\n1\n0\n0\n0\n$"
  note: "[exit and wait] second test for exit and wait failed"
  name: "Test 2: exit and wait - Check if exit status is correctly passed to wait syscall"
"""

rubrics_part4 = r"""
- points: 25
  cmd: "test_waitpid"
  expect: "0 1 -1\n-1\n$"
  note: "[waitpid] test for waitpid failed"
  name: "Test 1: waitpid - Checking test cases for waitpid"
"""

code_test_part1 = """
I2luY2x1ZGUgInR5cGVzLmgiCiNpbmNsdWRlICJzdGF0LmgiCiNpbmNsdWRlICJ1c2VyLmgiCgp2b2lkIHRlc3Rfbm9fc2libGluZ19ub19jaGlsZHJlbigpOwp2b2lkIHRlc3RfdHdvX3NpYmxpbmdfbm9fY2hpbGRyZW4oKTsKdm9pZCB0ZXN0X25vX3NpYmxpbmdfdHdvX2NoaWxkcmVuKCk7CnZvaWQgdGVzdF90d29fc2libGluZ190d29fY2hpbGRyZW4oKTsKCmludCBtYWluKGludCBhcmdjLCBjaGFyICphcmd2W10pIHsKICAgIGlmIChhcmdjIDwgMikgewogICAgICAgIHByaW50ZigxLCAiVXNhZ2U6IHRlc3RfZ2V0ZmFtaWx5IDx0ZXN0X251bWJlcj5cbiIpOwogICAgICAgIGV4aXQoMCk7CiAgICB9CgogICAgaW50IHRlc3RfY2FzZSA9IGF0b2koYXJndlsxXSk7CgogICAgc3dpdGNoKHRlc3RfY2FzZSkgewogICAgICAgIGNhc2UgMDoKICAgICAgICAgICAgdGVzdF9ub19zaWJsaW5nX25vX2NoaWxkcmVuKCk7CiAgICAgICAgICAgIGJyZWFrOwogICAgICAgIGNhc2UgMToKICAgICAgICAgICAgdGVzdF90d29fc2libGluZ19ub19jaGlsZHJlbigpOwogICAgICAgICAgICBicmVhazsKICAgICAgICBjYXNlIDI6CiAgICAgICAgICAgIHRlc3Rfbm9fc2libGluZ190d29fY2hpbGRyZW4oKTsKICAgICAgICAgICAgYnJlYWs7CiAgICAgICAgY2FzZSAzOgogICAgICAgICAgICB0ZXN0X3R3b19zaWJsaW5nX3R3b19jaGlsZHJlbigpOwogICAgICAgICAgICBicmVhazsKICAgICAgICBkZWZhdWx0OgogICAgICAgICAgICBwcmludGYoMSwgIlRoZSBhcmd1bWVudCBpcyBub3QgY29ycmVjdCFcbiIpOwogICAgICAgICAgICBleGl0KDApOwogICAgfQoKICAgIGV4aXQoMCk7Cn0KCi8vIFRlc3QgY2FzZSAwOiBObyBzaWJsaW5ncywgbm8gY2hpbGRyZW4Kdm9pZCB0ZXN0X25vX3NpYmxpbmdfbm9fY2hpbGRyZW4oKSB7CiAgICBnZXRmYW1pbHkoKTsgIAp9CgovLyBUZXN0IGNhc2UgMTogVHdvIHNpYmxpbmdzLCBubyBjaGlsZHJlbgp2b2lkIHRlc3RfdHdvX3NpYmxpbmdfbm9fY2hpbGRyZW4oKSB7CiAgICBpbnQgcGlkMSwgcGlkMiwgcGlkMzsKCiAgICBwaWQxID0gZm9yaygpOwogICAgaWYgKHBpZDEgPT0gMCkgewogICAgICAgIHNsZWVwKDIpOwogICAgICAgIGdldGZhbWlseSgpOwogICAgICAgIGV4aXQoMCk7CiAgICB9CgogICAgcGlkMiA9IGZvcmsoKTsKICAgIGlmIChwaWQyID09IDApIHsKICAgICAgICBzbGVlcCg1KTsKICAgICAgICBleGl0KDApOwogICAgfQoKICAgIHBpZDMgPSBmb3JrKCk7CiAgICBpZiAocGlkMyA9PSAwKSB7CiAgICAgICAgc2xlZXAoNSk7CiAgICAgICAgZXhpdCgwKTsKICAgIH0KCiAgICB3YWl0KDApOwogICAgd2FpdCgwKTsKICAgIHdhaXQoMCk7Cn0KCi8vIFRlc3QgY2FzZSAyOiBObyBzaWJsaW5ncywgdHdvIGNoaWxkcmVuCnZvaWQgdGVzdF9ub19zaWJsaW5nX3R3b19jaGlsZHJlbigpIHsKICAgIGludCBwaWQxLCBwaWQyLCBwaWQzOwoKICAgIHBpZDEgPSBmb3JrKCk7CiAgICBpZiAocGlkMSA9PSAwKSB7CiAgICAgICAgcGlkMiA9IGZvcmsoKTsKICAgICAgICBpZiAocGlkMiA9PSAwKSB7CiAgICAgICAgICAgIHNsZWVwKDEwKTsKICAgICAgICAgICAgZXhpdCgwKTsKICAgICAgICB9CgogICAgICAgIHBpZDMgPSBmb3JrKCk7CiAgICAgICAgaWYgKHBpZDMgPT0gMCkgewogICAgICAgICAgICBzbGVlcCgxMCk7CiAgICAgICAgICAgIGV4aXQoMCk7CiAgICAgICAgfQoKICAgICAgICBnZXRmYW1pbHkoKTsKCiAgICAgICAgd2FpdCgwKTsKICAgICAgICB3YWl0KDApOwoKICAgICAgICBleGl0KDApOwogICAgfQoKICAgIHdhaXQoMCk7Cn0KCi8vIFRlc3QgY2FzZSAzOiBUd28gc2libGluZ3MsIHR3byBjaGlsZHJlbgp2b2lkIHRlc3RfdHdvX3NpYmxpbmdfdHdvX2NoaWxkcmVuKCkgewogICAgaW50IHBpZDEsIHBpZDIsIHBpZDMsIHBpZDQsIHBpZDU7CgogICAgcGlkMSA9IGZvcmsoKTsKICAgIGlmIChwaWQxID09IDApIHsKICAgICAgICBzbGVlcCg1KTsKICAgICAgICBwaWQ0ID0gZm9yaygpOwogICAgICAgIGlmIChwaWQ0ID09IDApIHsKICAgICAgICAgICAgc2xlZXAoMTApOwogICAgICAgICAgICBleGl0KDApOwogICAgICAgIH0KCiAgICAgICAgcGlkNSA9IGZvcmsoKTsKICAgICAgICBpZiAocGlkNSA9PSAwKSB7CiAgICAgICAgICAgIHNsZWVwKDEwKTsKICAgICAgICAgICAgZXhpdCgwKTsKICAgICAgICB9CiAgICAgICAgc2xlZXAoMik7CiAgICAgICAgZ2V0ZmFtaWx5KCk7CgogICAgICAgIHdhaXQoMCk7CiAgICAgICAgd2FpdCgwKTsKCiAgICAgICAgZXhpdCgwKTsKICAgIH0KCiAgICBwaWQyID0gZm9yaygpOwogICAgaWYgKHBpZDIgPT0gMCkgewogICAgICAgIHNsZWVwKDEwKTsKICAgICAgICBleGl0KDApOwogICAgfQoKICAgIHBpZDMgPSBmb3JrKCk7CiAgICBpZiAocGlkMyA9PSAwKSB7CiAgICAgICAgc2xlZXAoMTApOwogICAgICAgIGV4aXQoMCk7CiAgICB9CgogICAgd2FpdCgwKTsKICAgIHdhaXQoMCk7CiAgICB3YWl0KDApOwp9
"""

code_test_part23 = """I2luY2x1ZGUgInR5cGVzLmgiCiNpbmNsdWRlICJzdGF0LmgiCiNpbmNsdWRlICJ1c2VyLmgiCgp2b2lkIHRlc3Rfc2ltcGxlX2V4aXRfd2FpdChpbnQgc3RhdHVzKSB7CiAgICBpbnQgcGlkID0gZm9yaygpOwogICAgaWYgKHBpZC
A8IDApIHsKICAgICAgICBwcmludGYoMSwgIkZvcmsgZmFpbGVkIVxuIik7CiAgICAgICAgZXhpdCgtMSk7CiAgICB9CiAgICBpZiAocGlkID09IDApIHsKICAgICAgICBleGl0KHN0YXR1cyk7CiAgICB9IGVsc2UgewogICAgICAg
IGludCB3YWl0X3N0YXR1czsKICAgICAgICBpbnQgd2FpdF9waWQgPSB3YWl0KCZ3YWl0X3N0YXR1cyk7CiAgICAgICAgaWYgKHdhaXRfcGlkID09IC0xKSB7CiAgICAgICAgICAgIHByaW50ZigxLCAiV2FpdCBmYWlsZWQhXG4iKT
sKICAgICAgICB9IGVsc2UgewogICAgICAgICAgICBpZiAod2FpdF9zdGF0dXMgPT0gc3RhdHVzKSB7CiAgICAgICAgICAgICAgICBwcmludGYoMSwgIiVkXG4iLCB3YWl0X3N0YXR1cyk7CiAgICAgICAgICAgIH0KICAgICAgICB9
CiAgICB9Cn0KCnZvaWQgdGVzdF9tb3JlX2V4aXRfd2FpdChpbnQgY2gxX3N0YXR1cywgaW50IGNoMl9zdGF0dXMpIHsKICAgIGludCBjaDFfcGlkID0gZm9yaygpOwogICAgaWYgKGNoMV9waWQgPCAwKSB7CiAgICAgICAgcHJpbn
RmKDEsICJGb3JrIGZhaWxlZCFcbiIpOwogICAgICAgIGV4aXQoLTEpOwogICAgfQogICAgaWYgKGNoMV9waWQgPT0gMCkgewogICAgICAgIGludCBjaDJfcGlkID0gZm9yaygpOwogICAgICAgIGlmIChjaDJfcGlkIDwgMCkgewog
ICAgICAgICAgICBwcmludGYoMSwgIkZvcmsgZmFpbGVkIVxuIik7CiAgICAgICAgICAgIGV4aXQoLTEpOwogICAgICAgIH0KICAgICAgICBpZiAoY2gyX3BpZCA9PSAwKSB7CiAgICAgICAgICAgIC8vIHNsZWVwKDEwMCk7CiAgIC
AgICAgICAgIGV4aXQoY2gyX3N0YXR1cyk7CiAgICAgICAgfSBlbHNlIHsKICAgICAgICAgICAgaW50IGNoMl93YWl0X3N0YXR1czsKICAgICAgICAgICAgaW50IGNoMl93YWl0X3BpZCA9IHdhaXQoJmNoMl93YWl0X3N0YXR1cyk7
CiAgICAgICAgICAgIGlmIChjaDJfd2FpdF9waWQgPT0gLTEpIHsKICAgICAgICAgICAgICAgIHByaW50ZigxLCAiV2FpdCBmYWlsZWQhXG4iKTsKICAgICAgICAgICAgfSBlbHNlIHsKICAgICAgICAgICAgICAgIGlmIChjaDJfd2
FpdF9zdGF0dXMgPT0gY2gyX3N0YXR1cykgewogICAgICAgICAgICAgICAgICAgIHByaW50ZigxLCAiJWRcbiIsIGNoMl93YWl0X3N0YXR1cyk7CiAgICAgICAgICAgICAgICB9CiAgICAgICAgICAgIH0KICAgICAgICB9IAogICAg
ICAgIGV4aXQoY2gxX3N0YXR1cyk7CiAgICB9IGVsc2UgewogICAgICAgIGludCBjaDFfd2FpdF9zdGF0dXM7CiAgICAgICAgaW50IGNoMV93YWl0X3BpZCA9IHdhaXQoJmNoMV93YWl0X3N0YXR1cyk7CiAgICAgICAgaWYgKGNoMV
93YWl0X3BpZCA9PSAtMSkgewogICAgICAgICAgICBwcmludGYoMSwgIldhaXQgZmFpbGVkIVxuIik7CiAgICAgICAgfSBlbHNlIHsKICAgICAgICAgICAgaWYgKGNoMV93YWl0X3N0YXR1cyA9PSBjaDFfc3RhdHVzKSB7CiAgICAg
ICAgICAgICAgICBwcmludGYoMSwgIiVkXG4iLCBjaDFfd2FpdF9zdGF0dXMpOwogICAgICAgICAgICB9CiAgICAgICAgfQogICAgfQp9Cgp2b2lkIGZpcnN0X3Rlc3QoKSB7CiAgICAvLyBUZXN0IGNhc2VzIHdpdGggZGlmZmVyZW
50IGV4aXQgc3RhdHVzZXMKICAgIHRlc3Rfc2ltcGxlX2V4aXRfd2FpdCgxKTsgICAvLyBFeGl0IHdpdGggc3RhdHVzIDEKICAgIHRlc3Rfc2ltcGxlX2V4aXRfd2FpdCg0Mik7ICAvLyBFeGl0IHdpdGggc3RhdHVzIDQyCiAgICB0
ZXN0X3NpbXBsZV9leGl0X3dhaXQoLTEpOyAgLy8gRXhpdCB3aXRoIHN0YXR1cyAtMQogICAgdGVzdF9zaW1wbGVfZXhpdF93YWl0KDApOyAgIC8vIE5vcm1hbCBleGl0CgogICAgZXhpdCgwKTsKfQoKdm9pZCBzZWNvbmRfdGVzdC
gpIHsKICAgdGVzdF9tb3JlX2V4aXRfd2FpdCgxLCAtMSk7IAogICB0ZXN0X21vcmVfZXhpdF93YWl0KDAsIDEpOyAKICAgdGVzdF9tb3JlX2V4aXRfd2FpdCgwLCAwKTsgICAvLyBCb3RoIGV4aXQgbm9ybWFsbHkKCiAgIGV4aXQo
MCk7Cn0KCmludCBtYWluKGludCBhcmdjLCBjaGFyKiBhcmd2W10pIHsKICAgIGlmIChhdG9pKGFyZ3ZbMV0pID09IDEpIHsKICAgICAgICBmaXJzdF90ZXN0KCk7ICAKICAgIH0gZWxzZSBpZiAoYXRvaShhcmd2WzFdKSA9PSAyKS
B7CiAgICAgICAgc2Vjb25kX3Rlc3QoKTsKICAgIH0gZWxzZSB7CiAgICAgICAgcHJpbnRmKDEsICJUaGUgYXJndW1lbnQgaXMgbm90IGNvcnJlY3QhXG4iKTsKICAgICAgICByZXR1cm4gLTE7CiAgICB9CiAgICAKICAgIHJldHVy
biAwOwp9
"""

code_test_part4 = """I2luY2x1ZGUgInR5cGVzLmgiCiNpbmNsdWRlICJzdGF0LmgiCiNpbmNsdWRlICJ1c2VyLmgiCgppbnQgbWFpbih2b2lkKSB7CiAgICBpbnQgY2hpbGQxX3N0YXR1czsKICAgIGludCBjaGlsZDJfc3RhdHVzOwogICAgaW50IGNoaW
xkM19zdGF0dXM7CiAgICBpbnQgb3B0aW9ucyA9IDA7CgogICAgaW50IGNoaWxkMV9waWQgPSBmb3JrKCk7CiAgICBpZiAoY2hpbGQxX3BpZCA8IDApIHsKICAgICAgICBwcmludGYoMSwgIkZvcmsgZmFpbGVkXG4iKTsKICAgICAg
ICBleGl0KC0xKTsKICAgIH0KCiAgICBpZiAoY2hpbGQxX3BpZCA9PSAwKSB7CiAgICAgICAgc2xlZXAoMTAwKTsKICAgICAgICBleGl0KDApOyAKICAgIH0KCiAgICBpbnQgY2hpbGQyX3BpZCA9IGZvcmsoKTsKICAgIGlmIChjaG
lsZDJfcGlkIDwgMCkgewogICAgICAgIHByaW50ZigxLCAiRm9yayBmYWlsZWRcbiIpOwogICAgICAgIGV4aXQoLTEpOwogICAgfQoKICAgIGlmIChjaGlsZDJfcGlkID09IDApIHsKICAgICAgICBzbGVlcCgxMDApOwogICAgICAg
IGV4aXQoMSk7IAogICAgfQoKICAgIGludCBjaGlsZDNfcGlkID0gZm9yaygpOwogICAgaWYgKGNoaWxkM19waWQgPCAwKSB7CiAgICAgICAgcHJpbnRmKDEsICJGb3JrIGZhaWxlZFxuIik7CiAgICAgICAgZXhpdCgtMSk7CiAgIC
B9IAoKICAgIGlmIChjaGlsZDNfcGlkID09IDApIHsKICAgICAgICBzbGVlcCgxMDApOwogICAgICAgIGV4aXQoLTEpOyAKICAgIH0KCiAgICAvLyBQYXJlbnQgcHJvY2VzcyB3YWl0cyBmb3Igc3BlY2lmaWMgY2hpbGQgcHJvY2Vz
c2VzCiAgICB3YWl0cGlkKGNoaWxkMV9waWQsICZjaGlsZDFfc3RhdHVzLCBvcHRpb25zKTsgLy8gV2FpdCBmb3IgY2hpbGQgMQogICAgd2FpdHBpZChjaGlsZDJfcGlkLCAmY2hpbGQyX3N0YXR1cywgb3B0aW9ucyk7IC8vIFdhaX
QgZm9yIGNoaWxkIDIKICAgIHdhaXRwaWQoY2hpbGQzX3BpZCwgJmNoaWxkM19zdGF0dXMsIG9wdGlvbnMpOyAvLyBXYWl0IGZvciBjaGlsZCAzCgogICAgcHJpbnRmKDEsICIlZCAlZCAlZFxuIiwgY2hpbGQxX3N0YXR1cywgY2hp
bGQyX3N0YXR1cywgY2hpbGQzX3N0YXR1cyk7CgogICAgaW50IGludmFsaWRfcGlkID0gOTk5OTsKICAgIGludCByZXN1bHQgPSB3YWl0cGlkKGludmFsaWRfcGlkLCAmY2hpbGQxX3N0YXR1cywgb3B0aW9ucyk7CiAgICBwcmludG
YoMSwgIiVkXG4iLCByZXN1bHQpOwoKICAgIGV4aXQoMCk7Cn0=
"""

def populate_makefile(filename):
    c = open('Makefile', 'r').read().replace(" -Werror", " ")
    uprogs = re.findall(r'UPROGS=([\w\W]*)fs\.img: mkfs', c)[0].replace("\\\n",'').split()
    uprogs.insert(0, f'_{filename}')
    uprogs = " ".join(uprogs)
    c = re.sub(r'UPROGS=([\w\W]*)fs\.img: mkfs', f'UPROGS={uprogs} \nfs.img: mkfs', c)
    open("Makefile", 'w').write(c)

def run_test(code, program, rubrics, points):
    code = base64.b64decode(code)
    populate_makefile(program)
    with open(program+".c", 'wb') as f:   
        f.write(code)

    p = process("make qemu-nox".split())

    errors = []

    try:
        p.recvuntil(b"init: starting sh\n$", timeout=10)
    except:
        print("[!] Failed to compile and start xv6 with testsuite")
        print("[!] Compile log:", p.recvall().decode('latin-1'))
        print(f"Your score: {points}")
        exit(1)

    rubrics = yaml.safe_load(rubrics)
    full = points

    for rubric in rubrics:
        print(f"[!] Checking [{rubric['name']}]")
        full += rubric["points"]
        try:
            if "cmd" in rubric:
                p.sendline(rubric["cmd"].encode())
            recv = p.recvall(timeout=20).decode('latin-1')
            # recv = p.recvuntil(rubric["expect"].encode(), timeout=20).decode('latin-1')
            if rubric["expect"] not in recv:
                print("Expect output: " +  repr(rubric["expect"]))
                print("Your output: " + repr(recv))
                raise Exception("Wrong output")
            points += rubric["points"]
        except:
            errors.append(rubric["note"])

    if errors:
        print("[!] Errors:")
        for error in errors:
            print("    " + error)
    else:
        print("[!] All check passed!")
    print("=======")
    print(f"Your score: {points} / {full}")

    if errors:
        exit(1)

    p.terminate()
    p.kill()

    return points

point1 = run_test(code_test_part1, "test_getfamily", rubrics_part1, 0)
print(f"---> Your total score: {point1} / 100")
point23 = run_test(code_test_part23, "test_exit_wait", rubrics_part23, 0)
print(f"---> Your total score: {point1 + point23} / 100")
point4 = run_test(code_test_part4, "test_waitpid", rubrics_part4, 0)
print(f"---> Your total score: {point1 + point23 + point4} / 100")
