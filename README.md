# Teaching Assistant — IELTS homework tracker

Students send photos of handwritten work to a Telegram bot. You grade them 1–10
from a keyboard-driven web queue. The site charts progress per student and per group.

No dependencies — Python 3 standard library only (this machine has no Node,
Homebrew or Docker, so the whole thing is stdlib `http.server` + `sqlite3` + `urllib`).

## Setup

1. Create a bot: message **@BotFather** on Telegram → `/newbot` → copy the token.
2. `cp config.example.json config.json` and fill in `telegram_token` and a real
   `teacher_password`. (`TELEGRAM_TOKEN` / `TEACHER_PASSWORD` env vars override the file.)
3. `./run.sh` — starts the dashboard on http://localhost:8080 and the bot together.

Demo data to see the charts populated: `python3 seed_demo.py --reset`.

## Daily flow

- **Groups** → create a group. Once the bot has connected once, this page shows a
  ready-made invite link per group (`https://t.me/yourbot?start=CODE`). Send that to
  the group; one tap opens the bot and joins them, so nobody types a code. The
  6-character code still works for anyone you tell it to manually.
- **Assignments** → create one per group. Open assignments are what the bot offers
  students when they send a photo.
- Students `/start` the bot, give their name and the join code, then send photos.
- **Students without Telegram** can upload on the web instead: open their page in the
  dashboard, copy their private link (`/s/<token>`) and send it to them. That link
  opens their own upload page - no password, no account, and it shows only their own
  work and scores. Photos land in the same grading queue.
- **Vocabulary** → paste a word list (`word = meaning`, one per line) and assign it
  to a group. Students practise with `/vocab`; scoring is automatic.
- Students see their own chart with `/progress`.
- You can see charts inside Telegram too: send `/iamteacher <your dashboard password>`
  to the bot once, then `/report` gives you group and per-student charts, and
  `/pending` says how many submissions are waiting.
- **Grade** → one submission per screen. Keys `1`–`9`, `0` = 10, `Enter` saves and
  advances, `s` skips to the back of the queue. Tap feedback chips instead of typing.
  Saving pushes the score to the student in Telegram automatically.
- **Overview** → who is at risk (two consecutive misses, or a falling trend).

## Design decisions worth keeping

- **A missed assignment is never scored zero.** It shows as a gap in the score chart
  and is counted in the separate completion figure — so the score line measures
  ability and completion measures discipline. Merging them hides which one is wrong.
- **Charts plot a rolling 3-submission average**, with raw scores as dots. A raw
  1–10 line is too noisy to read a trend from.
- **A student's chart shows the group average behind their line** for context.
- **Photo quality is gated for free.** Telegram sends image dimensions with every
  photo, and web uploads are sniffed for their real JPEG/PNG dimensions in
  `uploads.py`, so anything under `min_photo_width` is rejected with a retake
  instruction before it ever reaches your queue.
- **Student links are secret URLs, not accounts.** No passwords to reset for 60
  teenagers. A link identifies one student; submitted photos stay behind the
  teacher login.
- **Albums stay one submission.** Multi-page work sent as a Telegram album is
  grouped by `media_group_id` and acknowledged once.
- **Trilingual by student.** Bot messages are English / Russian / Uzbek, chosen once
  per student and stored on their record.
- **Charts are drawn pixel by pixel** (`png.py`) because Telegram only displays real
  images and this machine has no image library. No dependency, no CDN, works offline.
- **Vocabulary is spaced repetition, not a quiz.** A word answered correctly comes
  back after 1, 2, 4, 8, 16, 32 then 64 days; a wrong answer resets it to tomorrow.
  A word counts as *known* after three correct recalls in a row.

## Files

| File | Role |
|---|---|
| `core.py` | Config, SQLite schema, timeline and at-risk statistics |
| `server.py` | Teacher dashboard, grading queue, all routes |
| `bot.py` | Telegram long-polling: registration, photo intake, score delivery |
| `charts.py` | Hand-rolled SVG charts for the website |
| `png.py` | Minimal PNG encoder and rasteriser, incl. a 5x7 bitmap font |
| `uploads.py` | Multipart form parsing and JPEG/PNG dimension sniffing |
| `charts_png.py` | The same charts as images, for sending into Telegram |
| `app.py` | Runs the website and the bot together as one program |
| `seed_demo.py` | Fake group + scores for trying the UI |
| `data/app.db` | SQLite database · `data/uploads/` submitted photos |

## Not built yet, by choice

AI pre-grading. Every submission stores the photo, your score and your feedback
tags — after a few hundred of those you have examples of *your* grading standard,
which makes a calibrated "suggested score" feature cheap and accurate later.
The schema already supports it; nothing else needs to change.

## Running unattended

`app.py` also starts a scheduler thread (`jobs.py`) that does, every 15 minutes:

| Job | What it does | Runs |
|---|---|---|
| Deadline reminder | Tells students who have not submitted that a task is due tomorrow | once per student per assignment |
| Missed nudge | The day after a deadline, tells whoever sent nothing | once per student per assignment |
| Weekly digest | Sends you the queue size and the at-risk list in Telegram | once a week |
| Backup | Consistent SQLite copy into `data/backups/`, keeps the last 14 | daily |

**Messaging is off until you enable it.** Set `"automation": true` in `config.json`
(no restart needed for the password; this one is read on each pass, so a save is enough).
Backups run regardless. Nothing is sent outside 09:00-21:00 local time, and every
message is recorded in the `notifications` table first, so a crash, a restart or a
double pass can never send the same reminder twice.

## Running it online, non-stop

Locally the site only exists while your Mac is awake. To keep it running 24/7 you
rent a small computer that never sleeps. The app is packaged for that:

- `app.py` runs the website **and** the bot in one process, which is what hosting
  platforms expect.
- `Dockerfile` builds it anywhere. There is nothing to install - no dependencies.
- `DATA_DIR` env var points the database and uploaded photos at a mounted disk,
  so a redeploy never wipes student work. **This is the setting that matters most.**

### Railway (recommended, about $5/month)

1. railway.app -> sign in with GitHub -> New Project -> Deploy from GitHub repo
   -> pick `ielts-tracker`. It builds from the Dockerfile on its own.
2. Add a **Volume**, mount path `/data`. Without this, every redeploy wipes
   student work.
3. Add these **Variables**:

   | Variable | Value |
   |---|---|
   | `DATA_DIR` | `/data` |
   | `TELEGRAM_TOKEN` | the token from BotFather |
   | `TEACHER_PASSWORD` | your dashboard password |
   | `AUTOMATION` | `true` |
   | `TIMEZONE_OFFSET_HOURS` | `5` |

   Every setting in `config.json` has an environment variable, so the hosted
   copy needs no config file at all. `PORT` is supplied by the platform.
4. Settings -> Networking -> Generate Domain. That HTTPS address is the dashboard.
5. Stop the copy on your Mac. Two copies polling the same bot will fight over
   updates and answer students twice.

On first start against an empty volume the app imports `bootstrap.json`, so your
classes come back **with their original join codes** and the invite links already
in your students' hands keep working. Students, submissions and scores are not in
that file; they start fresh.

To refresh it after adding classes or vocabulary: `python3 bootstrap.py export`,
then commit.

### Two rules once it is online

- **Run exactly one copy.** SQLite and Telegram polling both assume a single
  instance; two containers will double-answer students and corrupt the queue.
- **Back up `/data`.** It holds the database and every photo. A monthly download
  is enough at this size.

## Before this leaves your laptop

- Set a strong `teacher_password`; sessions are in-memory and reset on restart.
- Put it behind HTTPS (a reverse proxy, or a tunnel like Cloudflare Tunnel).
  Student photographs of their work should not travel over plain HTTP.
- Back up `data/` — it holds both the database and every submitted photo.
