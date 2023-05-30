from pwn import *
import yaml
import base64
import re
from random import randint

code = "I2luY2x1ZGUgInR5cGVzLmgiCiNpbmNsdWRlICJzdGF0LmgiCiNpbmNsdWRlICJ1c2VyLmgiCiNpbmNsdWRlICJ1c3BpbmxvY2suaCIKc3RydWN0IHNobV9jbnQgeyBzdHJ1Y3QgdXNwaW5sb2NrIGxvY2s7IGludCBjbnQ7fTtpbnQgbWFpbihpbnQgYXJnYywgY2hhciAqYXJndltdKXtpbnQgcGlkO2ludCBpPTA7c3RydWN0IHNobV9jbnQgKmNvdW50ZXI7aW50IG1heCA9IGF0b2koYXJndlsxXSk7IHBpZD1mb3JrKCk7IHNsZWVwKDEpO3NobV9vcGVuKDEsKGNoYXIgKiopJmNvdW50ZXIpOyAgZm9yKGkgPSAwOyBpIDwgbWF4OyBpKyspeyB1YWNxdWlyZSgmKGNvdW50ZXItPmxvY2spKTsgY291bnRlci0+Y250Kys7IGlmKGklMTAwMCA9PSAwKSBwcmludGYoMSwiLSIpOyB1cmVsZWFzZSgmKGNvdW50ZXItPmxvY2spKTt9IHVhY3F1aXJlKCYoY291bnRlci0+bG9jaykpOyBwcmludGYoMSwgIlxuQ05UXyVkX1xuIiwgY291bnRlci0+Y250KTsgdXJlbGVhc2UoJihjb3VudGVyLT5sb2NrKSk7IGlmKHBpZCl7IHdhaXQoKTsgfSBzaG1fY2xvc2UoMSk7IGV4aXQoKTsgcmV0dXJuIDA7fQ=="

def populate_makefile(filename):
    c = open('Makefile', 'r').read().replace(" -Werror", " ")
    uprogs = re.findall(r'UPROGS=([\w\W]*)fs\.img: mkfs', c)[0].replace("\\\n",'').split()
    uprogs.insert(0, f'_{filename}')
    uprogs = " ".join(uprogs)
    c = re.sub(r'UPROGS=([\w\W]*)fs\.img: mkfs', f'UPROGS={uprogs} \nfs.img: mkfs', c)
    open("Makefile", 'w').write(c)

code = base64.b64decode(code)
full = 80

populate_makefile("lab4_autograde")

with open("lab4_autograde.c", 'wb') as f:   
    f.write(code)

p = process("make CPUS=2 qemu-nox".split())

points = 0

try:
    p.recvuntil(b"init: starting sh\n$", timeout=10)
except:
    print("[!]Failed to compile and start xv6 with testsuite")
    print("[!]Compile log:", p.recvall().decode('latin-1'))
    print(f"Your score: 0 / 80")
    exit(1)

try:
    cnts = []
    for _ in range(randint(20, 30)):
        count = randint(50000, 800000)
        cmd = f"lab4_autograde {count}"
        p.sendline(cmd.encode())

        line = p.recvline_regex(r"CNT_(.*)_".encode(), timeout=60).decode()
        # print(line)
        cnt1 = re.findall(r"CNT_(.*)_", line)[0]
        line = p.recvline_regex(r"CNT_(.*)_".encode(), timeout=60).decode()
        # print(line)
        cnt2 = re.findall(r"CNT_(.*)_", line)[0]
        cnts.append((count, int(cnt1), int(cnt2)))
    
    for count, cnt1, cnt2 in cnts:
        if cnt2 != 2 * count:
            raise Exception("")
    points += 80

except Exception as e:
    # probably a timeout
    print("[!]Encountered timeout")
    if cnts:
        count, cnt1, cnt2 = cnts[0]
        if cnt2 == 2 * count:
            points += 60
            print(f"[!]But you passed the first test case. This might be a malfunction of your shm_close() implementation. Please check your code.")
finally:
    print(f"Your score: {points} / 80")
    # print(cnts)
    exit(0 if points == full else 1)