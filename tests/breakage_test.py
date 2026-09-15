"""A broken page tells the teacher, once an hour, and never says more than it should.

Run me with:  python3 run_tests.py breakage
"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)
import core
core.init_db(); db = core.connect()

sent = []
import bot
bot.send = lambda token, tid, text, *a, **k: sent.append((tid, text))
core.load_config = (lambda real: (lambda: dict(real(), telegram_token="x")))(
    core.load_config)

print("1. WITH NOBODY REGISTERED, NOTHING IS SENT")
core.report_breakage("/queue", ValueError("boom"))
print("   messages:", len(sent))
assert not sent

core.meta_set(db, "teachers", json.dumps(["555"])); db.commit()

print("\n2. A BREAKAGE REACHES THE TEACHER")
core.report_breakage("/queue", ValueError("boom"))
print("   messages:", len(sent))
assert len(sent) == 1
tid, text = sent[0]
print("   to %s: %s" % (tid, text.splitlines()[0]))
assert "/queue" in text and "ValueError" in text and "boom" in text

print("\n3. THE SAME PAGE DOES NOT SEND AGAIN WITHIN THE HOUR")
core.report_breakage("/queue", ValueError("boom again"))
print("   messages:", len(sent))
assert len(sent) == 1, "a page everybody reloads must not send forty messages"

print("\n4. A DIFFERENT PAGE STILL DOES")
core.report_breakage("/roster", KeyError("other"))
print("   messages:", len(sent))
assert len(sent) == 2

print("\n5. AN HOUR LATER THE FIRST PAGE CAN SEND AGAIN")
from datetime import timedelta
core.meta_set(db, "broke:/queue",
              core.iso(core.now() - timedelta(hours=2)))
db.commit()
core.report_breakage("/queue", ValueError("boom"))
print("   messages:", len(sent))
assert len(sent) == 3

print("\n6. REPORTING CANNOT TAKE THE SITE DOWN")
def explode(*a, **k):
    raise RuntimeError("telegram is on fire")
bot.send = explode
core.report_breakage("/tests", ValueError("x"))    # must not raise
print("   survived a failing bot")

print("\nALL GOOD")
