from pwn import *
import yaml
import base64
import re
from random import randint

code = "I2luY2x1ZGUgInR5cGVzLmgiCiNpbmNsdWRlICJzdGF0LmgiCiNpbmNsdWRlICJ1c2VyLmgiCmludCBtYWluKGludCBhcmdjLCBjaGFyICphcmd2W10pCnsKICBpbnQgaSA9IGFyZ2M7CiAgcHJpbnRmKDEsICJBRERSOl8lcF9cbiIsICZpKTsKICBleGl0KCk7Cn0K"

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

p = process("make qemu-nox".split())

points = 0

try:
    p.recvuntil(b"init: starting sh\n$", timeout=10)
except:
    print("[!]Failed to compile and start xv6 with testsuite")
    print("[!]Compile log:", p.recvall().decode('latin-1'))
    print(f"Your score: 0 / 80")
    exit(1)

try:
    addrs = {}
    for _ in range(randint(30, 50)):
        arg_count = randint(1, 7)
        cmd = "lab3_autograde " + " ".join(map(str, range(arg_count)))
        p.sendline(cmd.encode())

        pids = []
        stamps = []
        line = p.recvline_regex(r"ADDR:_(.*)_".encode(), timeout=1).decode()
        addr = re.findall(r"ADDR:_(.*)_", line)[0]
        if int(addr, 16) < 0x7FFF0000:
            raise Exception("")
        if arg_count in addrs and addrs[arg_count] != addr:
            raise Exception("")
        else:
            addrs[arg_count] = addr

    keys = list(addrs.keys())
    keys.sort()
    last = 0x80000000
    for k in keys:
        if int(addrs[k], 16) <= last:
            last = int(addrs[k], 16)
        else:
            raise Exception("")


except:
    print("[!]Verfiication does not pass")
    print(f"Your score: 0 / 80")
    exit(1)

print("[!]All check passed!")
print("=======")
print(f"Your score: 80 / 80")
