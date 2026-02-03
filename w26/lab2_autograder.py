from pwn import *
import yaml
import base64
import re
from random import randin

code = "I2luY2x1ZGUgInR5cGVzLmgiCiNpbmNsdWRlICJ1c2VyLmgiCgppbnQgUFNjaGVkdWxlcih2b2lkKTsKCmludCBtYWluKGludCBhcmdjLCBjaGFyICphcmd2W10pIHsKICBQU2NoZWR1bGVyKCk7CiAgZXhpdCgpOwp9CgppbnQgUFNjaGVkdWxlcih2b2lkKSB7CiAgaW50IHBpZDsKICBpbnQgaSwgaiwgazsKICBzZXRwcmlvcml0eSgwKTsKICBmb3IgKGkgPSAwOyBpIDwgMzsgaSsrKSB7CiAgICBwaWQgPSBmb3JrKCk7CiAgICBpZiAocGlkID4gMCkgewogICAgICBjb250aW51ZTsKICAgIH0gZWxzZSBpZiAocGlkID09IDApIHsKICAgICAgc2V0cHJpb3JpdHkoMzAgLSAxMCAqIGkpOwogICAgICBmb3IgKGogPSAwOyBqIDwgNTAwMDA7IGorKykgewogICAgICAgIGFzbSgibm9wIik7CiAgICAgICAgZm9yIChrID0gMDsgayA8IDEwMDAwOyBrKyspIHsKICAgICAgICAgIGFzbSgibm9wIik7CiAgICAgICAgfQogICAgICB9CiAgICAgIHByaW50ZigxLCAicCBpOiVkIHQ6JWRcbiIsIGdldHBpZCgpLCB1cHRpbWUoKSk7CiAgICAgIGV4aXQoKTsKICAgIH0gZWxzZSB7CiAgICAgIHByaW50ZigyLCAiIFxuIEVycm9yIGZvcmsoKSBcbiIpOwogICAgICBleGl0KCk7CiAgICB9CiAgfQogIGlmIChwaWQgPiAwKSB7CiAgICBmb3IgKGkgPSAwOyBpIDwgMzsgaSsrKSB7CiAgICAgIHdhaXQoKTsKICAgIH0KICB9CiAgcmV0dXJuIDA7Cn0="
def populate_makefile(filename):
    c = open('Makefile', 'r').read().replace(" -Werror", " ")
    uprogs = re.findall(r'UPROGS=([\w\W]*)fs\.img: mkfs', c)[0].replace("\\\n",'').split()
    uprogs.insert(0, f'_{filename}')
    uprogs = " ".join(uprogs)
    c = re.sub(r'UPROGS=([\w\W]*)fs\.img: mkfs', f'UPROGS={uprogs} \nfs.img: mkfs', c)
    open("Makefile", 'w').write(c)

def post_to_gh(obtained, total):
  """
  Write points to for GitHub Actions
  """
  fd = os.environ.get('GITHUB_OUTPUT')
  if fd is not None:
    with open(fd, 'a') as out:
        out.write(f'points={obtained}\n')
        out.write(f'total_points={total}\n')
  print(f"::notice title=Autograding complete::Points {obtained}/{total}")
  print(f"::notice title=Autograding report::{{\"totalPoints\":{obtained},\"maxPoints\":{total}}}")

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
    post_to_gh(0, 70)
    exit(1)

direction = None
try:
    for _ in range(randint(5, 7)):
        p.sendline("lab2_autograde".encode())

        pids = []
        stamps = []
        for _ in range(3):
            line = p.recvline_regex(r"p i:(\d+) t:(\d+)".encode()).decode()
            print(line)
            pid, stamp = re.findall(r"p i:(\d+) t:(\d+)", line)[0]
            pids.append(int(pid))
            stamps.append(int(stamp))

        if pids[0] < pids[1] < pids[2]:
            cur_direction = 'a'
        elif pids[0] > pids[1] > pids[2]:
            cur_direction = 'd'
        else:
            raise Exception("Invalid execution sequence.")
        print(direction, cur_direction)
        if direction is None:
            direction = cur_direction
        elif direction != cur_direction:
            raise Exception("Execution sequence doesn't match in subsequent runs.")
        
        diff1 = stamps[1] - stamps[0]
        diff2 = stamps[2] - stamps[1]

        var = abs((diff1 / diff2) - 1)
        errors.append(var)
        if var > 0.35:
            raise Exception(f"Too large variation in the CPU ticks {var:.2f}")
        elif diff1 < 3:
            raise Exception(f"Too small CPU ticks diff between first two processes {diff1}")
        elif diff2 < 3:
            raise Exception(f"Too small CPU ticks diff between second two processes {diff2}")
except Exception as e:
    print("[!]Scheduler does not work as expected: ", e)
    if errors:
        print(f"[!]Errors for your scheduler: {sum(errors)/len(errors):.2f}")
    post_to_gh(0, 70)
    exit(1)

print(f"[!]Errors for your scheduler: {sum(errors)/len(errors):.2f}")
print("[!]All checks have passed!")
print("=======")
post_to_gh(70, 70)
