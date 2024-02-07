from pwn import *
import yaml
import base64
import re
from random import randint
from collections import defaultdict

def download_test_file():
    code = "I2luY2x1ZGUgInR5cGVzLmgiCiNpbmNsdWRlICJ1c2VyLmgiCmludCBQU2NoZWR1bGVyKHZvaWQpO2ludCBtYWluKGludCBhcmdjLCBjaGFyICphcmd2W10peyBQU2NoZWR1bGVyKCk7IGV4aXQoKTt9IGludCBQU2NoZWR1bGVyKHZvaWQpeyBpbnQgcGlkOyBpbnQgaSxqLGs7IHNldHByaW9yaXR5KDApOyBmb3IgKGkgPSAwOyBpIDwgMzsgaSsrKSB7CXBpZCA9IGZvcmsoKTsJaWYgKHBpZCA+IDApIHsgY29udGludWU7IH0gZWxzZSBpZiAoIHBpZCA9PSAwKSB7IHNldHByaW9yaXR5KDMwIC0gMTAgKiBpKTsgZm9yIChqID0gMDsgaiA8IDUwMDAwOyBqKyspIHsgYXNtKCJub3AiKTsgZm9yKGsgPSAwOyBrIDwgMTAwMDA7IGsrKykgeyBhc20oIm5vcCIpOyB9IH0gcHJpbnRmKDEsICJwIGk6JWQgdDolZFxuIiwgZ2V0cGlkKCksIHVwdGltZSgpKTsgZXhpdCgpOyB9IGVsc2UgeyBwcmludGYoMiwiIFxuIEVycm9yIGZvcmsoKSBcbiIpOyBleGl0KCk7IH0gfSBpZihwaWQgPiAwKSB7IGZvciAoaSA9IDA7IGkgPCAzOyBpKyspIHsgd2FpdCgpOyB9IH0gcmV0dXJuIDA7fQ=="
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

def run_single_test():
    p = None  # Initialize the process variable outside the try block for visibility in the finally block
    try:
        p = process("make CPUS=1 qemu-nox".split())
        p.recvuntil(b"init: starting sh\n$", timeout=10)
        p.sendline("lab2_autograde".encode())

        pids, timestamps = [], []
        for _ in range(3):
            line = p.recvline_regex(r"p i:(\d+) t:(\d+)".encode()).decode()
            pid, timestamp = map(int, re.findall(r"p i:(\d+) t:(\d+)", line)[0])
            pids.append(pid)
            timestamps.append(timestamp)

        # Validate PID order
        if not (pids == sorted(pids) or pids == sorted(pids, reverse=True)):
            raise Exception("Invalid PID order")
        p.shutdown('send')
        p.close()
        print("Finishing w/ correct order", pids)
        return timestamps

    except Exception as e:
        print(f"[!] Test failed with error: {e}")
        if p:
            p.shutdown('send')  # Shutdown the writing end of the process to signal no more input
            p.close()  # Close the process to clean up any resources

        return None  # Ensure the function returns None to indicate failure

def run_tests():
    points = 0
    test_runs = randint(7, 10)
    timestamp_collections = defaultdict(list)

    for _ in range(test_runs):
        timestamps = run_single_test()
        if timestamps:
            for i, timestamp in enumerate(timestamps):
                # print("adding timestamp")
                timestamp_collections[i].append(timestamp)
    if len(timestamp_collections[0]) > 5: # More than 5 times of correct order.
        points += 70  # Base points for priority scheduler w/o aging.
        print("[!] Priority scheduler checks passed!")

        # Average timestamps across runs
        avg_timestamps = [sum(times) / len(times) for times in timestamp_collections.values()]
        # Check time differences between processes
        # A correct aging impl should have similar execution time.
        time_diffs = [abs(avg_timestamps[i] - avg_timestamps[i+1]) for i in range(len(avg_timestamps) - 1)]

        if all(diff < 15 for diff in time_diffs):
            points += 5  # Additional points for similar execution times

        print("[!] Aging scheduler checks passed!")
    else:
        print("[!] No successful test runs.")

    print("=======")
    print(f"Your score: {points} / 75")

download_test_file()
run_tests()
