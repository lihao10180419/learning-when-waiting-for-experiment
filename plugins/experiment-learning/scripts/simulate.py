"""Small local lifecycle test. Never downloads models or uses GPUs."""
import argparse
import os
import sys
import time

p = argparse.ArgumentParser()
p.add_argument("--seconds", type=float, default=15)
p.add_argument("--exit-code", type=int, default=0)
a = p.parse_args()
print(f"SIMULATION stdout start pid={os.getpid()}", flush=True)
print("SIMULATION stderr preserved", file=sys.stderr, flush=True)
end = time.monotonic() + a.seconds
while time.monotonic() < end:
    time.sleep(min(.1, max(0, end - time.monotonic())))
print(f"SIMULATION stdout finish exit={a.exit_code}", flush=True)
sys.exit(a.exit_code)
