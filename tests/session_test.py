"""Signing in survives a restart, and a POST from elsewhere does not work.

Run me with:  python3 run_tests.py session
"""
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)
import core
core.init_db(); db = core.connect()

print("1. A SESSION IS A ROW, NOT A DICTIONARY")
token = core.open_session(db)
print("   live:", core.session_live(db, token))
assert core.session_live(db, token)

print("\n2. IT SURVIVES THE PROCESS GOING AWAY")
db.close()
db2 = core.connect()          # a brand new connection, as after a restart
print("   still live:", core.session_live(db2, token))
assert core.session_live(db2, token), "a restart must not sign the teacher out"

print("\n3. SIGNING OUT ENDS IT")
core.close_session(db2, token)
print("   live after sign out:", core.session_live(db2, token))
assert not core.session_live(db2, token)

print("\n4. A MADE-UP COOKIE IS NOT A SESSION")
assert not core.session_live(db2, "not-a-real-token")
assert not core.session_live(db2, "")
print("   rejected")

print("\n5. AN OLD ONE EXPIRES")
old = core.open_session(db2)
db2.execute("UPDATE sessions SET created_at=? WHERE token=?",
            (core.iso(core.now() - __import__("datetime").timedelta(
                days=core.SESSION_DAYS + 1)), old))
db2.commit()
print("   %d days old is live: %s" % (core.SESSION_DAYS + 1,
                                      core.session_live(db2, old)))
assert not core.session_live(db2, old)

print("\n6. A CROSS-SITE POST IS REFUSED")
import server

class FakeHeaders(dict):
    def get(self, k, d=None):
        return dict.get(self, k, d)

class Fake:
    def __init__(self, headers):
        self.headers = FakeHeaders(headers)
    _same_origin = server.Handler._same_origin

cases = [
    ({"Host": "site.uz", "Origin": "https://evil.com"}, False, "another origin"),
    ({"Host": "site.uz", "Origin": "https://site.uz"}, True, "its own origin"),
    ({"Host": "site.uz", "Referer": "https://evil.com/x"}, False, "another referer"),
    ({"Host": "site.uz"}, True, "a script, with neither"),
    ({"Host": "site.uz:8080", "Origin": "https://site.uz"}, True, "a port on the host"),
]
for headers, want, why in cases:
    got = Fake(headers)._same_origin()
    print("   %-22s -> %s" % (why, "allowed" if got else "refused"))
    assert got == want, why

print("\nALL GOOD")
