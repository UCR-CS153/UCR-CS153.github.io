from pwn import *
import yaml
import base64
import re
from random import randint
from os import system

# test program with stack growth
code = "I2luY2x1ZGUgInR5cGVzLmgiCiNpbmNsdWRlICJwYXJhbS5oIgojaW5jbHVkZSAidXNlci5oIgoKaW50CmJhc2ljX3Rlc3Qodm9pZCkKewogIGludCBsb2NhbDsKICB1aW50IGFkZHIgPSAodWludCkmbG9jYWw7CgogIHByaW50ZigxLCAic3RhY2tncm93OiBiYXNpYyBzdGFjayBhZGRyZXNzICVwXG4iLCAmbG9jYWwpOwoKICAvLyBGb3IgdGhlIG5ldyB0b3Atb2YtdXNlci1zcGFjZSBzdGFjayBsYXlvdXQsIHRoZSBzdGFjayBzaG91bGQgYmUKICAvLyB3aXRoaW4gYSBoaWdoIHVzZXItc3BhY2UgcmFuZ2UganVzdCBiZWxvdyBLRVJOQkFTRS4KICBpZihhZGRyIDwgMHg3ZjAwMDAwMHUgfHwgYWRkciA+IDB4N2ZmZmZmZmZ1KQogICAgcmV0dXJuIDA7CiAgcmV0dXJuIDE7Cn0KCmludApib251c190ZXN0KGludCBkZXB0aCkKewogIHZvbGF0aWxlIGNoYXIgYnVmWzQwOTZdOwogIGludCBpOwoKICBmb3IoaSA9IDA7IGkgPCBzaXplb2YoYnVmKTsgaSArPSA0MDk2KQogICAgYnVmW2ldID0gZGVwdGg7CgogIGlmKGRlcHRoIDw9IDApCiAgICByZXR1cm4gMDsKCiAgcmV0dXJuIGJvbnVzX3Rlc3QoZGVwdGggLSAxKSArIDE7Cn0KCmludAptYWluKGludCBhcmdjLCBjaGFyICphcmd2W10pCnsKICBpbnQgc3VjY2VzczsKCiAgcHJpbnRmKDEsICJzdGFja2dyb3c6IHJ1bm5pbmcgYmFzaWMgc3RhY2sgbGF5b3V0IHRlc3RcbiIpOwogIHN1Y2Nlc3MgPSBiYXNpY190ZXN0KCk7CiAgaWYoc3VjY2VzcykKICAgIHByaW50ZigxLCAic3RhY2tncm93OiBiYXNpYyB0ZXN0IHN1Y2Nlc3NcbiIpOwogIGVsc2UgewogICAgcHJpbnRmKDEsICJzdGFja2dyb3c6IGJhc2ljIHRlc3QgZmFpbHVyZVxuIik7CiAgICBleGl0KCk7CiAgfQoKICBwcmludGYoMSwgInN0YWNrZ3JvdzogcnVubmluZyBib251cyBzdGFjayBncm93dGggdGVzdFxuIik7CiAgc3VjY2VzcyA9IGJvbnVzX3Rlc3QoOCk7CiAgaWYoc3VjY2VzcyA9PSA4KQogICAgcHJpbnRmKDEsICJzdGFja2dyb3c6IGJvbnVzIHRlc3Qgc3VjY2VzcyAoZGVwdGg9OClcbiIpOwogIGVsc2UKICAgIHByaW50ZigxLCAic3RhY2tncm93OiBib251cyB0ZXN0IGZhaWx1cmVcbiIpOwoKICBleGl0KCk7Cn0K"
def populate_makefile(filename):
    c = open('Makefile', 'r').read().replace(" -Werror", " ")
    uprogs = re.findall(r'UPROGS=([\w\W]*)fs\.img: mkfs', c)[0].replace("\\\n",'').split()
    uprogs.insert(0, f'_{filename}')
    uprogs = " ".join(uprogs)
    c = re.sub(r'UPROGS=([\w\W]*)fs\.img: mkfs', f'UPROGS={uprogs} \nfs.img: mkfs', c)
    open("Makefile", 'w').write(c)

code = base64.b64decode(code)
full = 0

populate_makefile("lab3_autograde")

with open("lab3_autograde.c", 'wb') as f:   
    f.write(code)

system("make clean")

p = process("make qemu-nox".split())

points = 0

try:
    p.recvuntil(b"init: starting sh\n$", timeout=10)
except:
    print("[!]Failed to compile and start xv6 with testsuite")
    print("[!]Compile log:", p.recvall().decode('latin-1'))
    print(f"Your score: 0 / 90")
    exit(1)

try:
    p.sendline(b"lab3_autograde")

    line = p.recvline_regex(r"stackgrow: basic stack address (.*)".encode(), timeout=5).decode()
    addr = re.findall(r"stackgrow: basic stack address (.*)", line)[0]
    if int(addr, 16) < 0x7F000000 or int(addr, 16) > 0x7FFFFFFF:
        raise Exception("Stack address out of range")

    p.recvline_regex(r"stackgrow: basic test success".encode(), timeout=5)
    points += 80
    print("=======")
    print(f"New stack layout passed. Your score: {points} / 90")

    p.recvline_regex(r"stackgrow: running bonus stack growth test".encode(), timeout=5)
    p.recvline_regex(r"stackgrow: bonus test success \(depth=8\)".encode(), timeout=5)
    points += 10

except Exception as e:
    if points == 80:
        print("[!]Stack growth test does not pass")
        print(f"Your score: {points} / 90")
    else:
        print(e)
        print("[!]Verfiication does not pass")
        print(f"Your score: {points} / 90")
        exit(1)
    

print("[!]All check finished!")
print("=======")
print(f"Your score: {points} / 90")
