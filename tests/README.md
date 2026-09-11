# Tests

    python3 run_tests.py            every test
    python3 run_tests.py league     only the ones whose name matches

Twenty-six of them, about twenty seconds, nothing to install.

Each test makes a throwaway database in a temporary folder, starts a real server
on a spare port, and deletes the lot afterwards. None of them touch the live
site or the real database, and they can run in any order.

## What each one holds down

| Test | Guards |
|---|---|
| `season_test` | a season is fifteen lessons, not a month; closing one keeps the winner |
| `pause_test` | pausing the league subtracts the time rather than hiding it |
| `hw_test` | homework counts what was set — missing work is a nought, like late work |
| `balance_test` | homework belongs to the lesson it was set in, so the last ones still count |
| `deleted_test` | deleting a piece of homework stops it scoring, and keeps the marks |
| `scope_test` | the class view and the school view of the league |
| `portal_full` | what a student sees: one league table, their own row, no teacher links |
| `grade_test` | the marking page: audio, half marks, criteria, undo, quick notes |
| `roster_test` | pause, move, delete and bulk actions on students |
| `delete_student_test` | every table pointing at a student is cleared before the row goes |
| `batch_test` | homework managed as the batch it was set in |
| `assign_test` | one form sets homework, one line or many |
| `auto_test` | the game runs itself, and a stale press cannot skip a question |
| `grammar_test` | grammar questions carry their own wrong answers |
| `game_test` | the live game's pages keep their own scripts |
| `dtest_test` | a digital test: load, key, publish, sit, mark |
| `tests_shelf` | twenty practice-test buttons, each holding its own files |
| `materials_test` | the materials tree and its upload form |
| `music_test` | the song of the day: upload, replace, refuse, remove |
| `stream2_test` | whole tracks stream from disk with flat memory |
| `missing_test` | a song whose file has gone says so |
| `abort_test` | a client hanging up mid-download is not an error |
| `http_test` | students reach their own pages without signing in |
| `nav_test` | pages swap without reloading, so the music keeps playing |
| `revert_test` | the Telegram mini app stayed removed |
| `migrate_test` | a column added after a deploy reaches an existing database |
| `peek_test` | a student's page opens beside the teacher's, not on top of it |

## Writing another

Copy the shape of any of them:

```python
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
import core, server
core.init_db()
...
shutil.rmtree(tmp)
```

Set `DATA_DIR` **before** importing `core`, or the test will write to the real
database. Print what you are checking as well as asserting it — a test that says
what it saw is worth more than one that only says "ok" when it fails at 11pm.

`tests/fixtures/make.py` builds the few files some tests need (practice-test
PDFs, a digital test with a passage image) rather than committing megabytes of
real books.
