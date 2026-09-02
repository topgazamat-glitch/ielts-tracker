"""Single entry point: runs the dashboard and the Telegram bot in one process.

Hosting platforms expect one program per service, so this starts the bot on a
background thread and serves the website on the main thread. Locally you can
still run server.py and bot.py separately if you prefer.

    python3 app.py
"""
import threading
import time

import bootstrap
import bot
import core
import jobs
import server


def bot_forever():
    """Keep the bot alive; a network blip must never take the website down."""
    while True:
        try:
            bot.main()
        except SystemExit as exc:
            print(f"Bot not started: {exc}")
            return
        except Exception as exc:
            print(f"Bot crashed, restarting in 10s: {exc}")
            time.sleep(10)


def main():
    db = core.init_db()
    if bootstrap.load_if_empty(db):
        print("First run: classes and vocabulary restored from bootstrap.json")
    db.close()
    cfg = core.load_config()
    if cfg["telegram_token"]:
        threading.Thread(target=bot_forever, daemon=True).start()
    else:
        print("No telegram_token set - running the website only.")
    threading.Thread(target=jobs.forever, daemon=True).start()
    server.main()


if __name__ == "__main__":
    main()
