import yaml
import base64
import re
from pwn import *

rubrics_part1 = r"""
- points: 5
  cmd: "test_getparents 0"
  expect: "2 1 \n$"
  note: "[getparents] getparents failed on test case 0 "
  name: "Test 0: getparents - No fork"

- points: 5
  cmd: "test_getparents 1"
  expect: "4 2 1 \n$"
  note: "[getparents] getparents failed on test case 1 "
  name: "Test 1: getparents - One fork"

- points: 5
  cmd: "test_getparents 2"
  expect: "7 6 2 1 \n$"
  note: "[getparents] getparents failed on test case 2 "
  name: "Test 2: getparents - Two forks"

- points: 10
  cmd: "test_getparents 3"
  expect: "11 10 9 2 1 \n10 9 2 1 \n$"
  note: "[getparents] getparents failed on test case 3 "
  name: "Test 3: getparents - More forks"
"""

rubrics_part23 = r"""
- points: 15
  cmd: "test_exit_wait 1"
  expect: "1\n42\n-1\n0\n$"
  note: "[exit and wait] first test for exit and wait failed"
  name: "Test 1: exit and wait - Test cases with different exit statuses"

- points: 15
  cmd: "test_exit_wait 2"
  expect: "-1\n1\n1\n0\n0\n0\n$"
  note: "[exit and wait] second test for exit and wait failed"
  name: "Test 2: exit and wait - Check if exit status is correctly passed to wait syscall"
"""

rubrics_part4 = r"""
- points: 0
  cmd: "lab1_autograde 1"
  expect: "4 0"
  note: "Fork failed"
  name: "Exit & Wait - Fork first child process"

- points: 0
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

- points: 20
  expect: "10\n10+14+14\n8\n8+12+12\n9\n9+13+13\n7\n7+11+11\n11\n11+15+15"
  note: "[Waitpid]Child process exit status is incorrect"
  name: "Waitpid - check 5 child processes exit status"

- points: 2.5
  expect: "-1"
  note: "[Waitpid]Syscall does not return -1 while obtaining status of an invalid process"
  name: "Waitpid - check invalid process"

- points: 2.5
  expect: "-1"
  note : "[Waitpid]Syscall does not return -1 when an invalid argument is given"
  name: "Waitpid - check invalid argument"

- points: 5
  cmd: "lab1_autograde 3"
  expect: "-1 -1"
  note: "[Exit & Wait]Should return -1 for a child process that does not exist"
  name: "Exit & Wait - Wait for a child process that does not exist"

"""

code_test_part1 = """
I2luY2x1ZGUgInR5cGVzLmgiCiNpbmNsdWRlICJzdGF0LmgiCiNpbmNsdWRlICJ1c2VyLmgiCgp2b2lkIHRlc3Rfbm9fZm9yaygpOwp2b2lkIHRlc3Rfb25lX2ZvcmsoKTsKdm9pZCB0ZXN0X3R3b19mb3JrcygpOwp2b2lkIHRlc3R
fbW9yZV9mb3JrcygpOwoKaW50IG1haW4oaW50IGFyZ2MsIGNoYXIgKmFyZ3ZbXSkgewogICAgaWYgKGFyZ2MgPCAyKSB7CiAgICAgICAgcHJpbnRmKDEsICJVc2FnZTogdGVzdF9nZXRwYXJlbnRzIDx0ZXN0X251bWJlcj5cbiIpOw
ogICAgICAgIGV4aXQoMCk7CiAgICB9CgogICAgaW50IHRlc3RfY2FzZSA9IGF0b2koYXJndlsxXSk7CgogICAgc3dpdGNoKHRlc3RfY2FzZSkgewogICAgICAgIGNhc2UgMDoKICAgICAgICAgICAgdGVzdF9ub19mb3JrKCk7CiAgI
CAgICAgICAgIGJyZWFrOwogICAgICAgIGNhc2UgMToKICAgICAgICAgICAgdGVzdF9vbmVfZm9yaygpOwogICAgICAgICAgICBicmVhazsKICAgICAgICBjYXNlIDI6CiAgICAgICAgICAgIHRlc3RfdHdvX2ZvcmtzKCk7CiAgICAg
ICAgICAgIGJyZWFrOwogICAgICAgIGNhc2UgMzoKICAgICAgICAgICAgdGVzdF9tb3JlX2ZvcmtzKCk7CiAgICAgICAgICAgIGJyZWFrOwogICAgICAgIGRlZmF1bHQ6CiAgICAgICAgICAgIHByaW50ZigxLCAiVGhlIGFyZ3VtZW5
0IGlzIG5vdCBjb3JyZWN0IVxuIik7CiAgICAgICAgICAgIGV4aXQoMCk7CiAgICB9CgogICAgZXhpdCgwKTsKfQoKLy8gVGVzdCBjYXNlIDAKdm9pZCB0ZXN0X25vX2ZvcmsoKSB7CiAgICBnZXRwYXJlbnRzKCk7ICAKfQoKLy8gVG
VzdCBjYXNlIDEKdm9pZCB0ZXN0X29uZV9mb3JrKCkgewogICAgaW50IHBpZDE7CgogICAgcGlkMSA9IGZvcmsoKTsKICAgIGlmIChwaWQxID09IDApIHsKICAgICAgICBnZXRwYXJlbnRzKCk7CiAgICAgICAgZXhpdCgwKTsKICAgI
H0KCiAgICB3YWl0KDApOwp9CgovLyBUZXN0IGNhc2UgMgp2b2lkIHRlc3RfdHdvX2ZvcmtzKCkgewogICAgaW50IHBpZDEsIHBpZDI7CgogICAgcGlkMSA9IGZvcmsoKTsKICAgIGlmIChwaWQxID09IDApIHsKICAgICAgICBwaWQy
ID0gZm9yaygpOwogICAgICAgIGlmIChwaWQyID09IDApIHsKICAgICAgICAgICAgZ2V0cGFyZW50cygpOwogICAgICAgICAgICBleGl0KDApOwogICAgICAgIH0KCiAgICAgICAgd2FpdCgwKTsKCiAgICAgICAgZXhpdCgwKTsKICA
gIH0KCiAgICB3YWl0KDApOwp9CgovLyBUZXN0IGNhc2UgMyAKdm9pZCB0ZXN0X21vcmVfZm9ya3MoKSB7CiAgICBpbnQgcGlkMSwgcGlkMjsKCiAgICBwaWQxID0gZm9yaygpOwogICAgaWYgKHBpZDEgPT0gMCkgewogICAgICAgIH
BpZDIgPSBmb3JrKCk7CiAgICAgICAgaWYgKHBpZDIgPT0gMCkgewogICAgICAgICAgICBmb3JrKCk7CiAgICAgICAgICAgIHdhaXQoMCk7CiAgICAgICAgICAgIGdldHBhcmVudHMoKTsKICAgICAgICAgICAgc2xlZXAoMSk7CiAgI
CAgICAgICAgIGV4aXQoMCk7CiAgICAgICAgfQoKICAgICAgICB3YWl0KDApOwoKICAgICAgICBleGl0KDApOwogICAgfQoKICAgIHdhaXQoMCk7CiAgICBleGl0KDApOwp9
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

code_test_part4 = """I2luY2x1ZGUgInR5cGVzLmgiCiNpbmNsdWRlICJ1c2VyLmgiCgojZGVmaW5lIFdOT0hBTkcgCTEKCmludCBtYWluKGludCBhcmdjLCBjaGFyICphcmd2W10pCnsKCWludCBnZXRQYXJlbnQodm9pZCk7CglpbnQgZXhpdFdhaXQodm9
pZCk7CglpbnQgd2FpdFBpZCh2b2lkKTsKICBpbnQgd2FpdE5vdGhpbmcodm9pZCk7CgogIHByaW50ZigxLCAiXG5sYWIjMVxuIik7CiAgaWYgKGF0b2koYXJndlsxXSkgPT0gMikKCSAgd2FpdFBpZCgpOwogIGVsc2UgaWYgKGF0b2
koYXJndlsxXSkgPT0gMSkKICAgIGV4aXRXYWl0KCk7ICAKICBlbHNlIGlmIChhdG9pKGFyZ3ZbMV0pID09IDMpCiAgICB3YWl0Tm90aGluZygpOwogICAgLy8gRW5kIG9mIHRlc3QKCSBleGl0KDApOwoJIHJldHVybiAwOwogfQogI
GludCB3YWl0Tm90aGluZyh2b2lkKXsKICAgIGludCByZXQsIGV4aXRfc3RhdHVzID0gLTE7CiAgICByZXQgPSB3YWl0KCZleGl0X3N0YXR1cyk7CiAgICBwcmludGYoMSwgIiVkICVkXG4iLCByZXQsIGV4aXRfc3RhdHVzKTsKICAg
IHJldHVybiAwOwogfQoKaW50IGV4aXRXYWl0KHZvaWQpIHsKCSAgaW50IHBpZCwgcmV0X3BpZCwgZXhpdF9zdGF0dXM7CiAgICBpbnQgaTsKICAvLyB1c2UgdGhpcyBwYXJ0IHRvIHRlc3QgZXhpdChpbnQgc3RhdHVzKSBhbmQgd2F
pdChpbnQqIHN0YXR1cykKIAovLyAgIHByaW50ZigxLCAiXG4gIFBhcnRzIGEgJiBiKSB0ZXN0aW5nIGV4aXQoaW50IHN0YXR1cykgYW5kIHdhaXQoaW50KiBzdGF0dXMpOlxuIik7CgogIGZvciAoaSA9IDA7IGkgPCAyOyBpKyspIH
sKICAgIHBpZCA9IGZvcmsoKTsKICAgIGlmIChwaWQgPT0gMCkgeyAvLyBvbmx5IHRoZSBjaGlsZCBleGVjdXRlZCB0aGlzIGNvZGUKICAgICAgaWYgKGkgPT0gMCl7CiAgICAgICAgcHJpbnRmKDEsICIlZCAlZFxuIiwgZ2V0cGlkK
CksIDApOwogICAgICAgIGV4aXQoMCk7CiAgICAgIH0KICAgICAgZWxzZXsKCSAgICAgIHByaW50ZigxLCAiJWQgJWRcbiIgLGdldHBpZCgpLCAtMSk7CiAgICAgICAgZXhpdCgtMSk7CiAgICAgIH0gCiAgICB9IGVsc2UgaWYgKHBp
ZCA+IDApIHsgLy8gb25seSB0aGUgcGFyZW50IGV4ZWN1dGVzIHRoaXMgY29kZQogICAgICByZXRfcGlkID0gd2FpdCgmZXhpdF9zdGF0dXMpOwogICAgICBwcmludGYoMSwgIiVkKyVkXG4iLCByZXRfcGlkLCBleGl0X3N0YXR1cyk
7CiAgICB9IGVsc2UgeyAvLyBzb21ldGhpbmcgd2VudCB3cm9uZyB3aXRoIGZvcmsgc3lzdGVtIGNhbGwKCSAgICBwcmludGYoMiwgIlxuRXJyb3IgdXNpbmcgZm9ya1xuIik7CiAgICAgIGV4aXQoLTEpOwogICAgfQogIH0KICByZX
R1cm4gMDsKfQoKaW50IHdhaXRQaWQodm9pZCl7CgkKICBpbnQgcmV0X3BpZCwgZXhpdF9zdGF0dXM7CiAgaW50IGk7CiAgaW50IHBpZF9hWzVdPXswLCAwLCAwLCAwLCAwfTsKIC8vIHVzZSB0aGlzIHBhcnQgdG8gdGVzdCB3YWl0K
GludCBwaWQsIGludCogc3RhdHVzLCBpbnQgb3B0aW9ucykKCi8vICAgcHJpbnRmKDEsICJcbiAgUGFydCBjKSB0ZXN0aW5nIHdhaXRwaWQoaW50IHBpZCwgaW50KiBzdGF0dXMsIGludCBvcHRpb25zKTpcbiIpOwoKCWZvciAoaSA9
IDA7IGkgPDU7IGkrKykgewoJCXBpZF9hW2ldID0gZm9yaygpOwoJCWlmIChwaWRfYVtpXSA9PSAwKSB7IC8vIG9ubHkgdGhlIGNoaWxkIGV4ZWN1dGVkIHRoaXMgY29kZQoJCQlwcmludGYoMSwgIiVkICVkXG4iLCBnZXRwaWQoKSw
gZ2V0cGlkKCkgKyA0KTsKCQkJZXhpdChnZXRwaWQoKSArIDQpOwoJCX0KCX0KICBzbGVlcCg1KTsKICBwcmludGYoMSwgIiVkXG4iLHBpZF9hWzNdKTsKICByZXRfcGlkID0gd2FpdHBpZChwaWRfYVszXSwgJmV4aXRfc3RhdHVzLC
AwKTsKICBwcmludGYoMSwgIiVkKyVkKyVkXG4iLHJldF9waWQsIGV4aXRfc3RhdHVzLCBwaWRfYVszXSArIDQpOwogIHNsZWVwKDUpOwogIHByaW50ZigxLCAiJWRcbiIscGlkX2FbMV0pOwogIHJldF9waWQgPSB3YWl0cGlkKHBpZ
F9hWzFdLCAmZXhpdF9zdGF0dXMsIDApOwogIHByaW50ZigxLCAiJWQrJWQrJWRcbiIscmV0X3BpZCwgZXhpdF9zdGF0dXMsIHBpZF9hWzFdICsgNCk7CiAgc2xlZXAoNSk7CiAgcHJpbnRmKDEsICIlZFxuIixwaWRfYVsyXSk7CiAg
cmV0X3BpZCA9IHdhaXRwaWQocGlkX2FbMl0sICZleGl0X3N0YXR1cywgMCk7CiAgcHJpbnRmKDEsICIlZCslZCslZFxuIixyZXRfcGlkLCBleGl0X3N0YXR1cywgcGlkX2FbMl0gKyA0KTsKICBzbGVlcCg1KTsKICBwcmludGYoMSw
gIiVkXG4iLHBpZF9hWzBdKTsKICByZXRfcGlkID0gd2FpdHBpZChwaWRfYVswXSwgJmV4aXRfc3RhdHVzLCAwKTsKICBwcmludGYoMSwgIiVkKyVkKyVkXG4iLHJldF9waWQsIGV4aXRfc3RhdHVzLCBwaWRfYVswXSArIDQpOwogIH
NsZWVwKDUpOwogIHByaW50ZigxLCAiJWRcbiIscGlkX2FbNF0pOwogIHJldF9waWQgPSB3YWl0cGlkKHBpZF9hWzRdLCAmZXhpdF9zdGF0dXMsIDApOwogIHByaW50ZigxLCAiJWQrJWQrJWRcbiIscmV0X3BpZCwgZXhpdF9zdGF0d
XMsIHBpZF9hWzRdICsgNCk7CgogIHJldF9waWQgPSB3YWl0cGlkKDk5OTksICZleGl0X3N0YXR1cywgMCk7CiAgcHJpbnRmKDEsICIlZFxuIixyZXRfcGlkKTsKICAvL3ByaW50ZigxLCAiXG4gVGhpcyBpcyB0aGUgcGFyZW50OiBD
aGlsZCMgJWQgaGFzIGV4aXRlZCB3aXRoIHN0YXR1cyAlZFxuIixyZXRfcGlkLCBleGl0X3N0YXR1cyk7CgogIHJldF9waWQgPSB3YWl0cGlkKDk5OTksIChpbnQqKSAweGZmZmZmZmZmLCAwKTsKICBwcmludGYoMSwgIiVkXG4iLHJ
ldF9waWQpOwoKICByZXR1cm4gMDsKfQ==
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
            recv = p.recvuntil(rubric["expect"].encode(), timeout=20).decode('latin-1')
            # recv = p.recvall(timeout=20).decode('latin-1')
            if rubric["expect"] not in recv:
                if "cmd" in rubric:
                    p.sendline(rubric["cmd"].encode())
                recv = p.recvall(timeout=20).decode('latin-1')
                print("Expect output: \n" +  repr(rubric["expect"]) + "\n")
                print("Your output: ")
                print(repr(recv))
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
    # print("=======")
    # print(f"Your score: {points} / {full}")

    # if errors:
    #     exit(1)

    p.terminate()
    p.kill()

    return points

point1 = run_test(code_test_part1, "test_getparents", rubrics_part1, 0)
print(f"---> Your total score: {point1} / 100")
point23 = run_test(code_test_part23, "test_exit_wait", rubrics_part23, 0)
print(f"---> Your total score: {point1 + point23} / 100")
point4 = run_test(code_test_part4, "lab1_autograde", rubrics_part4, 0)
print(f"---> Your total score: {point1 + point23 + point4} / 100")
if point1+point23+point4 >= 100:
  exit(1)