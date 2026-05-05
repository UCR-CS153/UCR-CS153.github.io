from pwn import *
import yaml
import base64
import re
from random import randint

code = "I2luY2x1ZGUgInR5cGVzLmgiCiNpbmNsdWRlICJ1c2VyLmgiCgp2b2lkIHNwaW4oaW50IG4pewogIGludCBpLGo7CiAgZm9yKGk9MDtpPG47aSsrKXsKICAgIGFzbSgibm9wIik7CiAgICBmb3Ioaj0wO2o8MTAwMDA7aisrKSBhc20oIm5vcCIpOwogIH0KfQoKdm9pZCBvcmRlcnRlc3Qodm9pZCl7CiAgaW50IGkscGlkLHByaW87CiAgcHJpbnRmKDEsIkJFR0lOIG9yZGVyXG4iKTsKICBzZXRwcmlvcml0eSgwKTsKICBmb3IoaT0wO2k8MztpKyspewogICAgcGlkPWZvcmsoKTsKICAgIGlmKHBpZD09MCl7CiAgICAgIHByaW89MzAtMTAqaTsKICAgICAgc2V0cHJpb3JpdHkocHJpbyk7CiAgICAgIHNwaW4oNTAwMDApOwogICAgICBwcmludGYoMSwiT1JERVIgJWQgJWQgJWQgJWRcbiIsaSxnZXRwaWQoKSxwcmlvLHVwdGltZSgpKTsKICAgICAgZXhpdCgpOwogICAgfQogIH0KICBzZXRwcmlvcml0eSgzMSk7CiAgZm9yKGk9MDtpPDM7aSsrKSB3YWl0KCk7CiAgc2V0cHJpb3JpdHkoMTApOwogIHByaW50ZigxLCJFTkQgb3JkZXJcbiIpOwp9Cgp2b2lkIHlpZWxkdGVzdCh2b2lkKXsKICBpbnQgZmRzWzJdLHBpZCxpOwogIGNoYXIgYz0neCc7CiAgcGlwZShmZHMpOwogIHByaW50ZigxLCJCRUdJTiB5aWVsZFxuIik7CiAgc2V0cHJpb3JpdHkoMCk7CiAgcGlkPWZvcmsoKTsKICBpZihwaWQ9PTApewogICAgc2V0cHJpb3JpdHkoNSk7CiAgICByZWFkKGZkc1swXSwmYywxKTsKICAgIHByaW50ZigxLCJZSUVMRCBIICVkICVkXG4iLGdldHBpZCgpLHVwdGltZSgpKTsKICAgIGV4aXQoKTsKICB9CiAgc2xlZXAoNSk7CiAgcGlkPWZvcmsoKTsKICBpZihwaWQ9PTApewogICAgc2V0cHJpb3JpdHkoMCk7CiAgICB3cml0ZShmZHNbMV0sJmMsMSk7CiAgICBzZXRwcmlvcml0eSgxMCk7CiAgICBwcmludGYoMSwiWUlFTEQgTCAlZCAlZFxuIixnZXRwaWQoKSx1cHRpbWUoKSk7CiAgICBleGl0KCk7CiAgfQogIHNldHByaW9yaXR5KDMxKTsKICBmb3IoaT0wO2k8MjtpKyspIHdhaXQoKTsKICBzZXRwcmlvcml0eSgxMCk7CiAgcHJpbnRmKDEsIkVORCB5aWVsZFxuIik7Cn0KCmludCBtYWluKGludCBhcmdjLGNoYXIgKmFyZ3ZbXSl7CiAgb3JkZXJ0ZXN0KCk7CiAgeWllbGR0ZXN0KCk7CiAgZXhpdCgpOwp9"

def populate_makefile(filename):
    c = open('Makefile', 'r').read().replace(" -Werror", " ")
    uprogs = re.findall(r'UPROGS=([\w\W]*)fs\.img: mkfs', c)[0].replace("\\\n", ' ').split()
    prog = f'_{filename}'
    uprogs = [x for x in uprogs if x != prog]
    uprogs.insert(0, prog)
    uprogs = " ".join(uprogs)
    c = re.sub(r'UPROGS=([\w\W]*)fs\.img: mkfs', f'UPROGS={uprogs} \nfs.img: mkfs', c)
    open("Makefile", 'w').write(c)

def read_one_run(p):
    p.sendline(b"lab2_autograde")
    lines = []
    while True:
        line = p.recvline(timeout=60)
        if not line:
            raise Exception("timeout")
        s = line.decode("latin-1", "ignore").strip()
        lines.append(s)
        if s == "END yield":
            break
    return lines

def grade_one_run(lines):
    order = []
    yseq = []

    for line in lines:
        m = re.match(r"ORDER (\d+) (\d+) (\d+) (\d+)$", line)
        if m:
            order.append(tuple(map(int, m.groups())))

        m = re.match(r"YIELD ([HL]) (\d+) (\d+)$", line)
        if m:
            yseq.append((m.group(1), int(m.group(2)), int(m.group(3))))

    points = 0
    errors = []

    if len(order) != 3:
        errors.append("missing ORDER output")
        return points, errors, order, yseq

    prios = [x[2] for x in order]
    stamps = [x[3] for x in order]

    if prios == [10, 20, 30]:
        points += 45
    else:
        errors.append(f"wrong priority order: {prios}, expected [10, 20, 30]")

    diff1 = stamps[1] - stamps[0]
    diff2 = stamps[2] - stamps[1]

    if diff1 > 0 and diff2 > 0:
        var = abs((diff1 / diff2) - 1)
    else:
        var = 999

    if diff1 >= 3 and diff2 >= 3 and var <= 0.25:
        points += 15
    else:
        errors.append(f"bad timestamp spacing: stamps={stamps}, diff1={diff1}, diff2={diff2}, var={var:.2f}")

    if len(yseq) == 2 and [x[0] for x in yseq] == ["H", "L"]:
        points += 10
    else:
        errors.append(f"bad yield order: {[x[0] for x in yseq]}, expected ['H', 'L']")

    return points, errors, order, yseq

code = base64.b64decode(code)

populate_makefile("lab2_autograde")

with open("lab2_autograde.c", "wb") as f:
    f.write(code)

p = process("make CPUS=1 qemu-nox".split())

try:
    p.recvuntil(b"init: starting sh\n$", timeout=20)
except:
    print("[!]Failed to compile and start xv6 with testsuite")
    print("[!]Compile log:", p.recvall(timeout=3).decode("latin-1", "ignore"))
    print("Your score: 0")
    exit(1)

scores = []
all_errors = []
last_lines = []

try:
    for _ in range(randint(5, 7)):
        lines = read_one_run(p)
        last_lines = lines
        points, errors, order, yseq = grade_one_run(lines)
        scores.append(points)
        if errors:
            all_errors.extend(errors)

except Exception as e:
    print("[!]Scheduler does not work as expected")
    print(f"[!]Error: {e}")
    print("=======")
    print("Last output:")
    for line in last_lines:
        print(line)
    print("=======")
    print("Your score: 0")
    exit(1)

final_score = min(scores) if scores else 0

if final_score == 70:
    print("[!]All check passed!")
    print("=======")
    print("Your score: 70 / 70")
else:
    print("[!]Scheduler does not work as expected")
    print("=======")
    print("Errors:")
    for e in all_errors[:10]:
        print(f"[!]{e}")
    print("=======")
    print("Last output:")
    for line in last_lines:
        print(line)
    print("=======")
    print(f"Your score: {final_score} / 70")
    exit(1)
