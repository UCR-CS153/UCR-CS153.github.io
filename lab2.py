from pwn import *
import yaml
import base64
import re
from random import randint

code = "I2luY2x1ZGUgInR5cGVzLmgiCiNpbmNsdWRlICJ1c2VyLmgiCmludCBQU2NoZWR1bGVyKHZvaWQpO2ludCBtYWluKGludCBhcmdjLCBjaGFyICphcmd2W10peyBQU2NoZWR1bGVyKCk7IGV4aXQoKTt9IGludCBQU2NoZWR1bGVyKHZvaWQpeyBpbnQgcGlkLCByZXRfcGlkOyBpbnQgaSxqLGs7IHNldHByaW9yaXR5KDApOyBmb3IgKGkgPSAwOyBpIDwgMzsgaSsrKSB7CXBpZCA9IGZvcmsoKTsJaWYgKHBpZCA+IDApIHsgY29udGludWU7IH0gZWxzZSBpZiAoIHBpZCA9PSAwKSB7IHNldHByaW9yaXR5KDMwIC0gMTAgKiBpKTsgZm9yIChqID0gMDsgaiA8IDUwMDAwOyBqKyspIHsgYXNtKCJub3AiKTsgZm9yKGsgPSAwOyBrIDwgMTAwMDA7IGsrKykgeyBhc20oIm5vcCIpOyAgfSB9IGV4aXQoKTsgfSBlbHNlIHsgcHJpbnRmKDIsIiBcbiBFcnJvciBmb3JrKCkgXG4iKTsgZXhpdCgpOyB9IH0gaWYocGlkID4gMCkgeyBmb3IgKGkgPSAwOyBpIDwgMzsgaSsrKSB7IHJldF9waWQgPSB3YWl0KCk7IHByaW50ZigxLCAicCBpOiVkIHQ6JWRcbiIsIHJldF9waWQsIHVwdGltZSgpKTsgfSB9IHJldHVybiAwO30="

def populate_makefile(filename):
    c = open('Makefile', 'r').read().replace(" -Werror", " ")
    uprogs = re.findall(r'UPROGS=([\w\W]*)fs\.img: mkfs', c)[0].replace("\\\n",'').split()
    uprogs.insert(0, f'_{filename}')
    uprogs = " ".join(uprogs)
    c = re.sub(r'UPROGS=([\w\W]*)fs\.img: mkfs', f'UPROGS={uprogs} \nfs.img: mkfs', c)
    open("Makefile", 'w').write(c)

code = base64.b64decode(code)
full = 0

populate_makefile("lab2_autograde")

with open("lab2_autograde.c", 'wb') as f:   
    f.write(code)

p = process("make CPUS=1 qemu-nox".split())

points = 0
errors = []

try:
    p.recvuntil(b"init: starting sh\n$", timeout=10)
except:
    print("[!]Failed to compile and start xv6 with testsuite")
    print("[!]Compile log:", p.recvall().decode('latin-1'))
    print(f"Your score: {points}")
    exit(1)

direction = None
try:
    for _ in range(randint(5, 7)):
        p.sendline("lab2_autograde".encode())

        pids = []
        stamps = []
        for _ in range(3):
            line = p.recvline_regex(r"p i:(\d+) t:(\d+)".encode()).decode()
            # print(line)
            pid, stamp = re.findall(r"p i:(\d+) t:(\d+)", line)[0]
            pids.append(int(pid))
            stamps.append(int(stamp))

        if pids[0] < pids[1] < pids[2]:
            cur_direction = 'a'
        elif pids[0] > pids[1] > pids[2]:
            cur_direction = 'd'
        else:
            raise Exception("")
        # print(direction, cur_direction)
        if direction is None:
            direction = cur_direction
        elif direction != cur_direction:
            raise Exception("")
        
        diff1 = stamps[1] - stamps[0]
        diff2 = stamps[2] - stamps[1]

        var = abs((diff1 / diff2) - 1)
        errors.append(var)
        if var > 0.15 or diff1 < 3 or diff2 < 3:
            raise Exception("")
        

except:
    print("[!]Scheduler does not work as expected")
    if errors:
        print(f"[!]Errors for your scheudler: {sum(errors)/len(errors):.2f}")
    print(f"Your score: 0")
    exit(1)

print(f"[!]Errors for your scheudler: {sum(errors)/len(errors):.2f}")
print("[!]All check passed!")
print("=======")
print(f"Your score: 75 / 75")
