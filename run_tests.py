"""Run every test in tests/ and say plainly what passed.

    python3 run_tests.py              all of them
    python3 run_tests.py league       only the ones whose name matches

Each test builds its own throwaway database in a temporary folder and starts a
real server on a spare port, so nothing here touches the live site and the order
they run in does not matter. Nothing is installed; this is the standard library
talking to itself.
"""
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.join(ROOT, "tests")


def main():
    pick = sys.argv[1] if len(sys.argv) > 1 else ""
    names = sorted(f[:-3] for f in os.listdir(TESTS)
                   if f.endswith(".py") and f != "__init__.py")
    if pick:
        names = [n for n in names if pick.lower() in n.lower()]
    if not names:
        print("nothing matches %r" % pick)
        return 1

    width = max(len(n) for n in names)
    passed, failed = [], []
    started = time.time()
    for name in names:
        t0 = time.time()
        r = subprocess.run([sys.executable, os.path.join(TESTS, name + ".py")],
                           capture_output=True, text=True)
        took = time.time() - t0
        if r.returncode == 0:
            passed.append(name)
            print("  pass  %-*s  %4.1fs" % (width, name, took))
        else:
            failed.append((name, (r.stdout + r.stderr).strip()))
            print("  FAIL  %-*s  %4.1fs" % (width, name, took))

    print("\n%d passed, %d failed, %.0fs" % (len(passed), len(failed),
                                             time.time() - started))
    for name, out in failed:
        print("\n" + "-" * 62)
        print("%s\n" % name)
        print("\n".join(out.splitlines()[-25:]))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
