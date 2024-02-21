from pwn import *
import yaml
import base64
import re
from random import randint
from os import system

# code = "I2luY2x1ZGUgInR5cGVzLmgiCiNpbmNsdWRlICJzdGF0LmgiCiNpbmNsdWRlICJ1c2VyLmgiCmludCBtYWluKGludCBhcmdjLCBjaGFyICphcmd2W10pCnsKICBpbnQgaSA9IGFyZ2M7CiAgcHJpbnRmKDEsICJBRERSOl8lcF9cbiIsICZpKTsKICBleGl0KCk7Cn0K"

# test program with stack growth
code = "I2luY2x1ZGUgInR5cGVzLmgiCiNpbmNsdWRlICJ1c2VyLmgiCgppbnQgdGVzdChpbnQgbikgeyAKICAgIGludCB4ID0gbiArIDE7CiAgICByZXR1cm4geDsKfQoKaW50IHRlc3QyKGludCBuKSB7CiAgICBpbnQgYVsxMDEzXSA9IHswfTsKICAgIHByaW50ZigxLCAiVGVzdCAyOiBhcnJheSBhIGlzIGF0ICVwXG4iLCBhKTsKICAgIC8vcHJpbnRmKDEsICJUZXN0IDI6IHRoZSBmaXJzdCB2YWx1ZSBpcyAlZFxuIiwgYVswXSk7CiAgICBpZihuPDIpCiAgICAgIHJldHVybiBuOwogICAgZWxzZQogICAgICByZXR1cm4gdGVzdDIobi0xKSsxOwp9CgppbnQgbWFpbihpbnQgYXJnYywgY2hhciAqYXJndltdKSB7CiAgICBpbnQgb3B0aW9uID0gYXRvaShhcmd2WzFdKTsKICAgIGludCBudW0gPSBhdG9pKGFyZ3ZbMl0pOwoKICAgIGlmIChvcHRpb24gPT0gMSl7CiAgICAgICAgaW50IGkgPSBhcmdjOwogICAgICAgIHByaW50ZigxLCAiQUREUjpfJXBfXG4iLCAmaSk7CiAgICAgICAgZXhpdCgpOwogICAgfQoKICAgIHByaW50ZigxLCAiVGVzdCAyOiBTdGFjayBncm93dGggdGVzdC5cbiIpOwogICAgCiAgICBwcmludGYoMSwgInRlc3QyOl8lZF9cbiIsIHRlc3QyKG51bSkpOwogICAgZXhpdCgpOwp9Cgo="
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
    print(f"Your score: 0 / 80")
    exit(1)

try:
    addrs = {}
    for _ in range(randint(50, 80)):
        arg_count = randint(1, 7)
        # Option 1 for testing new stack layout
        cmd = "lab3_autograde 1 " + " ".join(map(str, range(arg_count)))
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
    print(cmd)
    print(addrs)
    keys = list(addrs.keys())
    keys.sort()
    last = 0x80000000
    decending = False
    for k in keys:
        if int(addrs[k], 16) <= last:
            _last = int(addrs[k], 16)
            if _last != last:
                decending = True
            last = _last
        else:
            raise Exception("")
    if not decending:
        raise Exception("")
    
    points += 75
    print("=======")
    print(f"New stack layout passed. Your score: {points} / 80")
    
    # Testing for stack growth
    count = randint(50, 100)
    cmd = f"lab3_autograde 2 {count}"
    p.sendline(cmd.encode())

    line = p.recvline_regex(r"test2:_(.*)_".encode(), timeout=1).decode()
    ret = re.findall(r"test2:_(.*)_", line)[0]

    if not int(ret) == count:
        raise Exception("Stack growth failed")
    
    points += 5


except Exception as e:
    if points == 75:
        print("[!]Stack growth test does not pass")
        print(f"Your score: {points} / 80")
    else:
        print(e)
        print("[!]Verfiication does not pass")
        print(f"Your score: {points} / 80")
        exit(1)
    

print("[!]All check finished!")
print("=======")
print(f"Your score: {points} / 80")
