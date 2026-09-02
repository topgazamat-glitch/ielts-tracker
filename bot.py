"""Telegram bot: students register, send photos of handwritten work, see progress.

Long-polls the Telegram API using urllib only: python3 bot.py
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

import charts_png
import core

API = "https://api.telegram.org/bot{token}/{method}"
FILE_API = "https://api.telegram.org/file/bot{token}/{path}"

T = {
    "en": {
        "ask_name": "Welcome! What is your full name?",
        "ask_code": "Thanks, {name}. Now send your group's join code (6 characters).",
        "bad_code": "I don't recognise that code. Ask your teacher and try again.",
        "joined": "You're in {group} ✅\n\nSend a photo of your handwritten homework any time.\n"
                  "/progress — your scores\n/language — change language",
        "no_group": "You're not in a group yet. Send /start to join.",
        "too_small": "That photo is too small to read. Please retake it: flat page, "
                     "top-down, whole page in frame, good light.",
        "no_assignment": "Received ✅ — but there's no open assignment right now, so I've "
                         "saved it as unassigned.",
        "received": "Received ✅ for “{title}”. Your teacher will grade it soon.",
        "which": "Which assignment is this for?",
        "reassigned": "Moved to “{title}” ✅",
        "scored": "“{title}” — {score}/10",
        "no_scores": "No graded work yet.",
        "progress": "Your progress\nAverage: {avg}/10\nLast 3: {last3}/10\n"
                    "Submitted: {done} · Missed: {missed}",
        "lang_ask": "Choose your language:",
        "lang_set": "Language set to English ✅",
        'vocab_none': 'No word list is available for your group yet.',
        'vocab_pick': 'Which word list?',
        'vocab_q': 'Word {i} of {n}\n\n{prompt}',
        'vocab_right': '✅ Correct',
        'vocab_wrong': '❌ It was: {term}',
        'vocab_done': 'Done — {correct}/{asked} correct.\nWords known: {known}/{total}',
        'vocab_stats': 'Vocabulary\nKnown: {known}/{total} ({mastery}%)\nAccuracy: {accuracy}%\nDue for review: {due}',
        'chart_caption': 'Average {avg}/10 · last 3 {last3}/10 · completion {completion}%',
        "new_assignment": "New assignment: {title}{due}\nSend a photo when it is ready.",
        "homework_list": "Homework{due}:",
        'hw_none': 'Nothing to do right now.',
        'hw_head': 'Homework{due} — {done}/{total} done',
        'hw_left': 'Still to send: {items}',
        'hw_all': 'All done. Nicely finished.',
        'hw_chase': '{done}/{total} done{due}. Still missing: {items}',
        'ask_prompt': 'What is your question? Write it in one message.',
        'ask_sent': 'Sent to your teacher. You will get an answer here.',
        'ask_answer': 'Your teacher answered:\\n\\n{answer}',
        'rating_head': 'Class standings — {group}',
        'rating_you': 'You are {rank} of {total}.',
        'improve': 'Send an improved version',
        'typed': 'Type the English word for: {prompt}',
        'vq_mode': 'How do you want to practise?',
        'vq_len': 'How many words?',
        'vq_scope': 'Which words?',
        'vq_gap': 'Fill the gap:',
        'vq_w2m': 'What does this word mean?',
        'welcome2': "Here is how it works:\n\n📸 Send a photo of your homework — that is all you need to do.\n📋 What's left — see your tasks\n📊 My progress — your scores\n📚 Practise words — vocabulary\n\nTry the buttons below.",
        'cancelled': 'Cancelled.',
        'nothing_cancel': 'Nothing to cancel.',
        'quiz_start': 'Start practice (10 words)',
        'quiz_options': 'Choose how',
        'quiz_stop': 'Stop',
        'quiz_score': '{correct} of {asked} so far',
        'undo': 'Delete this',
        'undone': 'Deleted. You can send it again.',
        'undo_late': 'That one has already been graded, so it cannot be deleted.',
        'more_pages': 'Sending more photos now will add them to the same homework.',
        'not_listed': 'Not in the list',
        'unassigned_ok': 'Saved without a task. Your teacher will sort it out.',
        'lost': 'I did not understand that. Use the buttons below.',
        "help": "Send a photo of your homework.\n/homework - what is left\n/progress - your chart\n/vocab - word practice\n/language",
    },
    "ru": {
        "ask_name": "Добро пожаловать! Как вас зовут (имя и фамилия)?",
        "ask_code": "Спасибо, {name}. Теперь отправьте код группы (6 символов).",
        "bad_code": "Такой код не найден. Уточните у преподавателя и попробуйте снова.",
        "joined": "Вы в группе {group} ✅\n\nОтправляйте фото домашней работы в любое время.\n"
                  "/progress — ваши оценки\n/language — сменить язык",
        "no_group": "Вы ещё не в группе. Отправьте /start.",
        "too_small": "Фото слишком мелкое. Переснимите: страница ровно, сверху, "
                     "полностью в кадре, при хорошем свете.",
        "no_assignment": "Получено ✅ — но сейчас нет открытого задания, сохранил без привязки.",
        "received": "Получено ✅ для «{title}». Преподаватель скоро проверит.",
        "which": "К какому заданию это относится?",
        "reassigned": "Перенесено в «{title}» ✅",
        "scored": "«{title}» — {score}/10",
        "no_scores": "Проверенных работ пока нет.",
        "progress": "Ваш прогресс\nСредний балл: {avg}/10\nПоследние 3: {last3}/10\n"
                    "Сдано: {done} · Пропущено: {missed}",
        "lang_ask": "Выберите язык:",
        "lang_set": "Язык: русский ✅",
        'vocab_none': 'Для вашей группы пока нет списка слов.',
        'vocab_pick': 'Какой список слов?',
        'vocab_q': 'Слово {i} из {n}\n\n{prompt}',
        'vocab_right': '✅ Верно',
        'vocab_wrong': '❌ Правильно: {term}',
        'vocab_done': 'Готово — {correct}/{asked} правильно.\nВыучено слов: {known}/{total}',
        'vocab_stats': 'Словарный запас\nВыучено: {known}/{total} ({mastery}%)\nТочность: {accuracy}%\nК повторению: {due}',
        'chart_caption': 'Средний {avg}/10 · последние 3 {last3}/10 · сдано {completion}%',
        "new_assignment": "Новое задание: {title}{due}\nОтправьте фото, когда будет готово.",
        "homework_list": "Домашнее задание{due}:",
        'hw_none': 'Сейчас заданий нет.',
        'hw_head': 'Домашнее задание{due} — сделано {done}/{total}',
        'hw_left': 'Осталось отправить: {items}',
        'hw_all': 'Всё сделано. Отлично.',
        'hw_chase': 'Сделано {done}/{total}{due}. Не хватает: {items}',
        'ask_prompt': 'Какой у вас вопрос? Напишите одним сообщением.',
        'ask_sent': 'Отправлено преподавателю. Ответ придёт сюда.',
        'ask_answer': 'Преподаватель ответил:\\n\\n{answer}',
        'rating_head': 'Рейтинг группы — {group}',
        'rating_you': 'Вы {rank} из {total}.',
        'improve': 'Отправить исправленный вариант',
        'typed': 'Напишите английское слово: {prompt}',
        'vq_mode': 'Как будем тренироваться?',
        'vq_len': 'Сколько слов?',
        'vq_scope': 'Какие слова?',
        'vq_gap': 'Заполните пропуск:',
        'vq_w2m': 'Что означает это слово?',
        'welcome2': 'Как это работает:\n\n📸 Отправьте фото домашней работы — это всё.\n📋 Что осталось — ваши задания\n📊 Мой прогресс — оценки\n📚 Учить слова — словарь\n\nПопробуйте кнопки ниже.',
        'cancelled': 'Отменено.',
        'nothing_cancel': 'Нечего отменять.',
        'quiz_start': 'Начать (10 слов)',
        'quiz_options': 'Выбрать режим',
        'quiz_stop': 'Остановить',
        'quiz_score': '{correct} из {asked} верно',
        'undo': 'Удалить',
        'undone': 'Удалено. Можете отправить снова.',
        'undo_late': 'Эта работа уже проверена, удалить нельзя.',
        'more_pages': 'Следующие фото добавятся к этой же работе.',
        'not_listed': 'Нет в списке',
        'unassigned_ok': 'Сохранено без задания. Преподаватель разберётся.',
        'lost': 'Не понял. Используйте кнопки ниже.',
        "help": "Отправьте фото домашней работы.\n/progress - ваш график\n/vocab - слова\n/language",
    },
    "uz": {
        "ask_name": "Xush kelibsiz! Ism va familiyangizni yozing.",
        "ask_code": "Rahmat, {name}. Endi guruh kodini yuboring (6 ta belgi).",
        "bad_code": "Bunday kod topilmadi. O'qituvchingizdan so'rab, qayta urinib ko'ring.",
        "joined": "Siz {group} guruhidasiz ✅\n\nUy vazifangiz rasmini istalgan vaqtda yuboring.\n"
                  "/progress — ballaringiz\n/language — tilni o'zgartirish",
        "no_group": "Siz hali guruhda emassiz. /start yuboring.",
        "too_small": "Rasm juda kichik. Qaytadan oling: varaq tekis, tepadan, "
                     "to'liq kadrda, yorug'likda.",
        "no_assignment": "Qabul qilindi ✅ — hozir ochiq topshiriq yo'q, biriktirilmagan holda saqladim.",
        "received": "“{title}” uchun qabul qilindi ✅. O'qituvchi tez orada tekshiradi.",
        "which": "Bu qaysi topshiriq uchun?",
        "reassigned": "“{title}” ga ko'chirildi ✅",
        "scored": "“{title}” — {score}/10",
        "no_scores": "Hali tekshirilgan ish yo'q.",
        "progress": "Sizning natijangiz\nO'rtacha: {avg}/10\nOxirgi 3 ta: {last3}/10\n"
                    "Topshirilgan: {done} · O'tkazib yuborilgan: {missed}",
        "lang_ask": "Tilni tanlang:",
        "lang_set": "Til: o'zbekcha ✅",
        'vocab_none': "Guruhingiz uchun hozircha so'zlar ro'yxati yo'q.",
        'vocab_pick': "Qaysi ro'yxat?",
        'vocab_q': "{n} tadan {i}-so'z\n\n{prompt}",
        'vocab_right': "✅ To'g'ri",
        'vocab_wrong': "❌ To'g'risi: {term}",
        'vocab_done': "Tugadi — {correct}/{asked} to'g'ri.\nBilingan so'zlar: {known}/{total}",
        'vocab_stats': "Lug'at\nBilingan: {known}/{total} ({mastery}%)\nAniqlik: {accuracy}%\nTakrorlash kerak: {due}",
        'chart_caption': "O'rtacha {avg}/10 · oxirgi 3 ta {last3}/10 · topshirilgan {completion}%",
        "new_assignment": "Yangi topshiriq: {title}{due}\nTayyor bo'lganda rasmini yuboring.",
        "homework_list": "Uy vazifasi{due}:",
        'hw_none': "Hozircha topshiriq yo'q.",
        'hw_head': 'Uy vazifasi{due} — {done}/{total} bajarildi',
        'hw_left': 'Yuborish kerak: {items}',
        'hw_all': 'Hammasi bajarildi. Barakalla.',
        'hw_chase': '{done}/{total} bajarildi{due}. Qolgani: {items}',
        'ask_prompt': 'Savolingiz nima? Bitta xabarda yozing.',
        'ask_sent': "O'qituvchiga yuborildi. Javob shu yerga keladi.",
        'ask_answer': "O'qituvchi javob berdi:\\n\\n{answer}",
        'rating_head': 'Guruh reytingi — {group}',
        'rating_you': "Siz {total} tadan {rank}-o'rindasiz.",
        'improve': 'Tuzatilgan variantni yuborish',
        'typed': "Inglizcha so'zni yozing: {prompt}",
        'vq_mode': 'Qanday mashq qilamiz?',
        'vq_len': "Nechta so'z?",
        'vq_scope': "Qaysi so'zlar?",
        'vq_gap': "Bo'sh joyni to'ldiring:",
        'vq_w2m': "Bu so'z nimani anglatadi?",
        'welcome2': "Bu qanday ishlaydi:\n\n📸 Uy vazifangiz rasmini yuboring — hammasi shu.\n📋 Nima qoldi — topshiriqlaringiz\n📊 Natijam — baholaringiz\n📚 So'z mashqi — lug'at\n\nQuyidagi tugmalarni bosing.",
        'cancelled': 'Bekor qilindi.',
        'nothing_cancel': "Bekor qiladigan narsa yo'q.",
        'quiz_start': "Boshlash (10 ta so'z)",
        'quiz_options': 'Rejimni tanlash',
        'quiz_stop': "To'xtatish",
        'quiz_score': "{asked} tadan {correct} to'g'ri",
        'undo': "O'chirish",
        'undone': "O'chirildi. Qaytadan yuborishingiz mumkin.",
        'undo_late': "Bu ish allaqachon tekshirilgan, o'chirib bo'lmaydi.",
        'more_pages': "Keyingi rasmlar shu ishga qo'shiladi.",
        'not_listed': "Ro'yxatda yo'q",
        'unassigned_ok': "Topshiriqsiz saqlandi. O'qituvchi hal qiladi.",
        'lost': 'Tushunmadim. Quyidagi tugmalardan foydalaning.',
        "help": "Uy vazifangiz rasmini yuboring.\n/progress - grafik\n/vocab - so'zlar\n/language",
    },
}


def t(lang, key, **kw):
    return T.get(lang, T["en"]).get(key, T["en"][key]).format(**kw)


# ------------------------------------------------------------- telegram api

def call(token, method, **params):
    data = urllib.parse.urlencode(
        {k: (json.dumps(v) if isinstance(v, (dict, list)) else v)
         for k, v in params.items() if v is not None}
    ).encode()
    req = urllib.request.Request(API.format(token=token, method=method), data=data)
    try:
        with urllib.request.urlopen(req, timeout=65) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return json.load(e)
    except Exception as e:  # network hiccup - caller retries on the next poll
        return {"ok": False, "error": str(e)}


def send(token, chat_id, text, keyboard=None, markup=None):
    if markup is None and keyboard:
        markup = {"inline_keyboard": keyboard}
    return call(token, "sendMessage", chat_id=chat_id, text=text, reply_markup=markup)


def send_score(token, chat_id, lang, title, score, tags, note, sub_id=None):
    """Called right after a grade is saved, from the dashboard or from Telegram."""
    lang = lang or "en"
    lines = [t(lang, "scored", title=title or "homework", score=f"{score:g}")]
    if tags:
        lines.append("• " + "\n• ".join(tags))
    if note:
        lines.append(note)
    kb = None
    if sub_id and score is not None and score < 8:
        kb = [[{"text": t(lang, "improve"), "callback_data": f"imp:{sub_id}"}]]
    send(token, chat_id, "\n\n".join(lines), keyboard=kb)


def send_photo(token, chat_id, png_bytes, caption=""):
    """Telegram needs multipart/form-data for uploads; built by hand here."""
    boundary = "----ta" + os.urandom(8).hex()
    parts = []
    for name, value in (("chat_id", str(chat_id)), ("caption", caption[:1000])):
        if value:
            parts.append(
                f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"'
                f"\r\n\r\n{value}\r\n".encode()
            )
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="photo";'
        f' filename="progress.png"\r\nContent-Type: image/png\r\n\r\n'.encode()
        + png_bytes + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    req = urllib.request.Request(
        API.format(token=token, method="sendPhoto"), data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def notify_teachers_new(db, token, sub_id):
    """Push a new submission to the teacher with 1-10 buttons underneath."""
    teachers = json.loads(core.meta_get(db, "teachers", "[]"))
    if not teachers:
        return 0
    sub = db.execute(
        "SELECT s.*, st.name, g.name gname, a.title FROM submissions s"
        " JOIN students st ON st.id=s.student_id"
        " LEFT JOIN groups g ON g.id=st.group_id"
        " LEFT JOIN assignments a ON a.id=s.assignment_id WHERE s.id=?",
        (sub_id,),
    ).fetchone()
    if not sub:
        return 0
    f = db.execute(
        "SELECT telegram_file_id FROM files WHERE submission_id=? ORDER BY ord LIMIT 1",
        (sub_id,),
    ).fetchone()
    caption = "%s · %s\n%s%s" % (sub["name"], sub["gname"] or "-",
                                 sub["title"] or "unassigned",
                                 "  (LATE)" if sub["late"] else "")
    kb = [[{"text": str(n), "callback_data": f"g:{sub_id}:{n}"} for n in (1, 2, 3, 4, 5)],
          [{"text": str(n), "callback_data": f"g:{sub_id}:{n}"} for n in (6, 7, 8, 9, 10)]]
    markup = {"inline_keyboard": kb}
    for tid in teachers:
        if f and f["telegram_file_id"]:
            method = "sendVoice" if sub["kind"] == "voice" else "sendPhoto"
            key = "voice" if sub["kind"] == "voice" else "photo"
            call(token, method, chat_id=tid, caption=caption, reply_markup=markup,
                 **{key: f["telegram_file_id"]})
        else:
            send(token, tid, caption, markup=markup)
    return len(teachers)


def grade_submission(db, token, sub_id, score):
    """Score a submission from Telegram and tell the student straight away."""
    db.execute(
        "UPDATE submissions SET status='graded', score=?, graded_at=? WHERE id=?",
        (float(score), core.iso(core.now()), sub_id),
    )
    db.commit()
    row = db.execute(
        "SELECT s.score, s.note, st.telegram_id, st.lang, a.title FROM submissions s"
        " JOIN students st ON st.id=s.student_id"
        " LEFT JOIN assignments a ON a.id=s.assignment_id WHERE s.id=?",
        (sub_id,),
    ).fetchone()
    if row and row["telegram_id"]:
        send_score(token, row["telegram_id"], row["lang"], row["title"],
                   row["score"], [], row["note"], sub_id)
    return row


def download_photo(token, file_id, dest_name):
    info = call(token, "getFile", file_id=file_id)
    if not info.get("ok"):
        return False
    url = FILE_API.format(token=token, path=info["result"]["file_path"])
    dest = os.path.join(core.UPLOAD_DIR, dest_name)
    try:
        with urllib.request.urlopen(url, timeout=60) as r, open(dest, "wb") as fh:
            fh.write(r.read())
        return True
    except Exception:
        return False


# ------------------------------------------------------------------- state

def get_state(db, tid):
    r = db.execute("SELECT * FROM bot_state WHERE telegram_id=?", (tid,)).fetchone()
    if not r:
        return None, {}
    return r["step"], json.loads(r["payload"] or "{}")


def set_state(db, tid, step, payload=None):
    db.execute(
        "INSERT INTO bot_state (telegram_id, step, payload, updated_at) VALUES (?,?,?,?)"
        " ON CONFLICT(telegram_id) DO UPDATE SET step=excluded.step,"
        " payload=excluded.payload, updated_at=excluded.updated_at",
        (tid, step, json.dumps(payload or {}), core.iso(core.now())),
    )
    db.commit()


def student_of(db, tid):
    return db.execute("SELECT * FROM students WHERE telegram_id=?", (tid,)).fetchone()


def open_assignments(db, group_id):
    return db.execute(
        "SELECT * FROM assignments WHERE group_id=? AND closed=0 AND published=1"
        " ORDER BY COALESCE(due_at, created_at) DESC, id DESC",
        (group_id,),
    ).fetchall()



# ------------------------------------------------------------ vocabulary

BUTTONS = {
    "en": ["\U0001F4CB What's left", "\U0001F4CA My progress",
           "\U0001F4DA Practise words", "\U0001F3C6 Rating",
           "\u2753 Ask teacher"],
    "ru": ["\U0001F4CB Что осталось", "\U0001F4CA Мой прогресс",
           "\U0001F4DA Учить слова", "\U0001F3C6 Рейтинг",
           "\u2753 Вопрос учителю"],
    "uz": ["\U0001F4CB Nima qoldi", "\U0001F4CA Natijam",
           "\U0001F4DA So'z mashqi", "\U0001F3C6 Reyting",
           "\u2753 Savol berish"],
}
# every label, in every language, mapped to the command it stands for
BUTTON_COMMANDS = {}
for _lang, _labels in BUTTONS.items():
    for _cmd, _label in zip(("/homework", "/progress", "/vocab", "/rating", "/ask"), _labels):
        BUTTON_COMMANDS[_label] = _cmd


def main_keyboard(lang):
    b = BUTTONS.get(lang, BUTTONS["en"])
    return {"keyboard": [[b[0], b[1]], [b[2], b[3]], [b[4]]],
            "resize_keyboard": True, "is_persistent": True}


def set_commands(token):
    """The menu button next to the message box, in each language."""
    menus = {
        None: [("homework", "what is left to do"), ("progress", "my scores and chart"),
               ("vocab", "practise vocabulary"), ("rating", "class standings"),
               ("ask", "ask the teacher a question"), ("language", "change language"),
               ("cancel", "stop what you are doing")],
        "ru": [("homework", "что осталось сделать"), ("progress", "мои оценки и график"),
               ("vocab", "учить слова"), ("rating", "рейтинг группы"),
               ("ask", "задать вопрос преподавателю"), ("language", "сменить язык"),
               ("cancel", "отменить текущее действие")],
        "uz": [("homework", "nima qolgan"), ("progress", "natijalarim va grafik"),
               ("vocab", "so'z mashqi"), ("rating", "guruh reytingi"),
               ("ask", "o'qituvchiga savol"), ("language", "tilni o'zgartirish"),
               ("cancel", "joriy amalni bekor qilish")],
    }
    ok = True
    for lang, items in menus.items():
        cmds = [{"command": c, "description": d} for c, d in items]
        res = call(token, "setMyCommands", commands=cmds, language_code=lang)
        ok = ok and res.get("ok", False)
    return ok


def lang_keyboard():
    return [[{"text": "English", "callback_data": "lang:en"},
             {"text": "Русский", "callback_data": "lang:ru"},
             {"text": "O'zbek", "callback_data": "lang:uz"}]]


MODE_LABELS = {
    "en": {"m2w": "Meaning \u2192 word", "w2m": "Word \u2192 meaning",
           "type": "Spell it", "gap": "Fill the gap", "mix": "Mixed"},
    "ru": {"m2w": "Значение \u2192 слово", "w2m": "Слово \u2192 значение",
           "type": "Написать слово", "gap": "Заполнить пропуск", "mix": "Смешанный"},
    "uz": {"m2w": "Ma'no \u2192 so'z", "w2m": "So'z \u2192 ma'no",
           "type": "So'zni yozing", "gap": "Bo'sh joyni to'ldirish", "mix": "Aralash"},
}
SCOPE_LABELS = {
    "en": {"all": "Whole unit", "due": "Due for review", "new": "New words"},
    "ru": {"all": "Весь юнит", "due": "На повторение", "new": "Новые слова"},
    "uz": {"all": "Butun bo'lim", "due": "Takrorlash", "new": "Yangi so'zlar"},
}


def offer_modes(db, token, student, list_id):
    """One obvious button to begin; everything else behind 'Choose how'."""
    lang = student["lang"]
    kb = [[{"text": t(lang, "quiz_start"), "callback_data": f"vg:{list_id}:mix:all:10"}],
          [{"text": t(lang, "quiz_options"), "callback_data": f"vo:{list_id}"}]]
    return send(token, student["telegram_id"], t(lang, "vq_mode"), keyboard=kb)


def offer_modes_full(db, token, student, list_id):
    lang = student["lang"]
    labels = MODE_LABELS.get(lang, MODE_LABELS["en"])
    kb = [[{"text": labels["mix"], "callback_data": f"vm:{list_id}:mix"}],
          [{"text": labels["m2w"], "callback_data": f"vm:{list_id}:m2w"},
           {"text": labels["w2m"], "callback_data": f"vm:{list_id}:w2m"}],
          [{"text": labels["type"], "callback_data": f"vm:{list_id}:type"},
           {"text": labels["gap"], "callback_data": f"vm:{list_id}:gap"}]]
    return send(token, student["telegram_id"], t(lang, "vq_mode"), keyboard=kb)


def offer_scope(db, token, student, list_id, mode):
    lang = student["lang"]
    labels = SCOPE_LABELS.get(lang, SCOPE_LABELS["en"])
    kb = [[{"text": labels["all"], "callback_data": f"vs:{list_id}:{mode}:all"}],
          [{"text": labels["due"], "callback_data": f"vs:{list_id}:{mode}:due"},
           {"text": labels["new"], "callback_data": f"vs:{list_id}:{mode}:new"}]]
    return send(token, student["telegram_id"], t(lang, "vq_scope"), keyboard=kb)


def offer_length(db, token, student, list_id, mode, scope):
    kb = [[{"text": str(n), "callback_data": f"vg:{list_id}:{mode}:{scope}:{n}"}
           for n in core.QUIZ_LENGTHS]]
    return send(token, student["telegram_id"], t(student["lang"], "vq_len"), keyboard=kb)


def start_quiz(db, token, student, list_id, mode="mix", scope="all", count=10):
    lang = student["lang"]
    words = core.scope_words(db, student["id"], list_id, scope, count)
    if not words:
        return send(token, student["telegram_id"], t(lang, "vocab_none"))
    sid = db.execute(
        "INSERT INTO quiz_sessions (student_id, list_id, started_at) VALUES (?,?,?)",
        (student["id"], list_id, core.iso(core.now())),
    ).lastrowid
    db.commit()
    set_state(db, student["telegram_id"], "quiz", {
        "session": sid, "list": list_id, "mode": mode,
        "queue": [w["id"] for w in words], "idx": 0, "correct": 0,
    })
    ask_question(db, token, student)


def ask_question(db, token, student):
    lang = student["lang"]
    tid = student["telegram_id"]
    _, st = get_state(db, tid)
    idx, queue = st["idx"], st["queue"]
    if idx >= len(queue):
        return finish_quiz(db, token, student)
    word = db.execute("SELECT * FROM words WHERE id=?", (queue[idx],)).fetchone()
    if not word:  # the list was edited mid-quiz
        st["idx"] = idx + 1
        set_state(db, tid, "quiz", st)
        return ask_question(db, token, student)

    prog = db.execute(
        "SELECT streak FROM word_progress WHERE student_id=? AND word_id=?",
        (student["id"], word["id"]),
    ).fetchone()
    mode = core.pick_mode(st.get("mode", "mix"), word, prog["streak"] if prog else 0)

    st["current"] = word["id"]
    st["typed"] = mode in ("type", "gap")
    set_state(db, tid, "quiz", st)

    counter = t(lang, "vocab_q", i=idx + 1, n=len(queue), prompt="").strip()
    if mode == "gap":
        body = t(lang, "vq_gap") + "\n\n" + core.gap_sentence(word)
        return send(token, tid, counter + "\n\n" + body, markup=main_keyboard(lang))
    if mode == "type":
        body = t(lang, "typed", prompt=word["translation"])
        return send(token, tid, counter + "\n\n" + body, markup=main_keyboard(lang))

    if mode == "w2m":
        prompt, options, label = word["term"], "translation", t(lang, "vq_w2m")
    else:
        prompt, options, label = word["translation"], "term", ""
    opts = core.quiz_options(db, st["list"], word)
    kb = [[{"text": o[options][:60], "callback_data": f"q:{st['session']}:{o['id']}"}]
          for o in opts]
    kb.append([{"text": t(lang, "quiz_stop"), "callback_data": "qstop"}])
    head = counter + "\n\n" + (label + "\n\n" if label else "") + prompt
    if idx:
        head = t(lang, "quiz_score", correct=st.get("correct", 0), asked=idx) + "\n\n" + head
    send(token, tid, head, keyboard=kb)


def answer_typed(db, token, student, text):
    tid = student["telegram_id"]
    step, st = get_state(db, tid)
    word = db.execute("SELECT * FROM words WHERE id=?", (st.get("current"),)).fetchone()
    if not word:
        return
    guess = " ".join(text.strip().lower().split()).strip(".,!?;:")
    correct = guess == word["term"].strip().lower()
    core.record_answer(db, student["id"], word["id"], correct)
    lang = student["lang"]
    if correct:
        st["correct"] += 1
        send(token, tid, t(lang, "vocab_right"))
    else:
        send(token, tid, t(lang, "vocab_wrong", term=word["term"]))
    st["idx"] += 1
    st.pop("current", None)
    st["typed"] = False
    set_state(db, tid, "quiz", st)
    ask_question(db, token, student)


def answer_question(db, token, student, chosen_id):
    tid = student["telegram_id"]
    lang = student["lang"]
    step, st = get_state(db, tid)
    if step != "quiz" or "current" not in st:
        return
    word_id = st["current"]
    correct = int(chosen_id) == int(word_id)
    core.record_answer(db, student["id"], word_id, correct)
    if correct:
        st["correct"] += 1
        send(token, tid, t(lang, "vocab_right"))
    else:
        term = db.execute("SELECT term FROM words WHERE id=?", (word_id,)).fetchone()
        send(token, tid, t(lang, "vocab_wrong", term=term["term"] if term else "?"))
    st["idx"] += 1
    st.pop("current", None)
    set_state(db, tid, "quiz", st)
    ask_question(db, token, student)


def finish_quiz(db, token, student):
    tid = student["telegram_id"]
    _, st = get_state(db, tid)
    asked = len(st.get("queue", []))
    db.execute(
        "UPDATE quiz_sessions SET finished_at=?, asked=?, correct=? WHERE id=?",
        (core.iso(core.now()), asked, st.get("correct", 0), st.get("session")),
    )
    db.commit()
    set_state(db, tid, None)
    v = core.vocab_stats(db, student["id"])
    send(token, tid, t(student["lang"], "vocab_done", correct=st.get("correct", 0),
                       asked=asked, known=v["known"], total=v["total"]))


# --------------------------------------------------------------- reporting

def student_chart_png(db, student):
    stats = core.student_stats(db, student["id"])
    band = []
    for row in stats["timeline"]:
        r = db.execute(
            "SELECT AVG(score) a FROM submissions WHERE assignment_id=? AND status='graded'",
            (row["assignment_id"],),
        ).fetchone()
        band.append(round(r["a"], 2) if r["a"] is not None else None)
    g = db.execute("SELECT name FROM groups WHERE id=?", (student["group_id"],)).fetchone()
    sub = f"{g['name'] if g else ''}  ·  average {stats['average'] or '-'}/10"
    return charts_png.score_chart(
        student["name"], sub, stats["timeline"], band=band,
        footer="green = your trend    grey = group average    x = not submitted",
    ), stats


def group_chart_png(db, group):
    rows = []
    for st in db.execute(
        "SELECT * FROM students WHERE group_id=? AND active=1 ORDER BY name",
        (group["id"],),
    ).fetchall():
        s = core.student_stats(db, st["id"])
        rows.append((st["name"], s["average"], s["at_risk"]))
    return charts_png.bars_chart(
        group["name"], "average score per student", rows,
        footer="red = needs attention (2 misses in a row, or a falling trend)",
    )


def remaining_text(db, student, due_at):
    """What is left in this deadline's set, after a submission lands."""
    lang = student["lang"]
    items = core.homework_items(db, student["group_id"], due_at)
    p = core.set_progress(db, student["id"], items)
    head = t(lang, "hw_head", due=due_label(due_at), done=p["done"], total=p["total"])
    if not p["remaining"]:
        return head + "\n" + t(lang, "hw_all")
    names = ", ".join(a["title"] for a in p["remaining"])
    return head + "\n" + t(lang, "hw_left", items=names)


def announce_assignment(token, db, assignment_id):
    """Tell a group that a new assignment is open. Returns how many were told."""
    a = db.execute("SELECT * FROM assignments WHERE id=?", (assignment_id,)).fetchone()
    if not a:
        return 0
    due = ""
    if a["due_at"]:
        due = " (due %s)" % a["due_at"][:10]
    sent = 0
    for st in db.execute(
        "SELECT telegram_id, lang FROM students WHERE group_id=? AND active=1"
        " AND telegram_id IS NOT NULL",
        (a["group_id"],),
    ).fetchall():
        send(token, st["telegram_id"],
             t(st["lang"], "new_assignment", title=a["title"], due=due))
        sent += 1
    return sent


def is_teacher(db, tid):
    return str(tid) in json.loads(core.meta_get(db, "teachers", "[]"))


def teacher_report(db, token, tid):
    groups = db.execute("SELECT * FROM groups WHERE archived=0 ORDER BY name").fetchall()
    if not groups:
        return send(token, tid, "No groups yet. Create one in the dashboard.")
    kb = [[{"text": g["name"][:40], "callback_data": f"rg:{g['id']}"}] for g in groups]
    send(token, tid, "Which group?", keyboard=kb)


# ---------------------------------------------------------------- handlers

def due_label(due_at):
    return " (%s)" % due_at[:10] if due_at else ""


def rating_text(db, student):
    """Top of the class, plus the student's own line, always visible."""
    lang = student["lang"]
    g = db.execute("SELECT name FROM groups WHERE id=?", (student["group_id"],)).fetchone()
    rows = core.rating_rows(db, student["group_id"])
    if not rows:
        return t(lang, "hw_none")
    lines = [t(lang, "rating_head", group=g["name"] if g else "")]
    medals = {1: "\U0001F947", 2: "\U0001F948", 3: "\U0001F949"}
    mine = next((r for r in rows if r["student"]["id"] == student["id"]), None)
    for r in rows[:5]:
        mark = medals.get(r["rank"], "%d." % r["rank"])
        you = "  \u2190" if mine and r["rank"] == mine["rank"] else ""
        lines.append("%s %s — %s%% done, %s/10%s" % (
            mark, r["student"]["name"], r["completion"] if r["completion"] is not None else 0,
            r["average"] if r["average"] is not None else "-", you))
    if mine and mine["rank"] > 5:
        lines.append("...")
        lines.append("%d. %s — %s%% done, %s/10  \u2190" % (
            mine["rank"], mine["student"]["name"],
            mine["completion"] if mine["completion"] is not None else 0,
            mine["average"] if mine["average"] is not None else "-"))
    if mine:
        lines.append("")
        lines.append(t(lang, "rating_you", rank=mine["rank"], total=len(rows)))
        if mine["streak"] >= 2:
            lines.append("\U0001F525 %d in a row" % mine["streak"])
    return "\n".join(lines)


def checklist_text(db, student, lang):
    """Every open set, with a tick or an empty box per item."""
    sets = core.open_sets(db, student["group_id"])
    if not sets:
        return t(lang, "hw_none")
    blocks = []
    for due_at, items in sets:
        p = core.set_progress(db, student["id"], items)
        left = core.due_in_words(due_at)
        head_due = due_label(due_at)
        if left:
            head_due = " (%s, %s)" % (due_at[:10], left)
        lines = [t(lang, "hw_head", due=head_due, done=p["done"], total=p["total"])]
        for a in items:
            lines.append(("\u2705 " if a["id"] in p["done_ids"] else "\u2b1c ") + a["title"])
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def join_group(db, token, tid, name, code, lang):
    g = db.execute(
        "SELECT * FROM groups WHERE join_code=? AND archived=0", (code,)
    ).fetchone()
    if not g:
        set_state(db, tid, "code", {"name": name})
        return send(token, tid, t(lang, "bad_code"))
    existing = student_of(db, tid)
    if existing:
        db.execute("UPDATE students SET name=?, group_id=?, active=1 WHERE id=?",
                   (name, g["id"], existing["id"]))
    else:
        db.execute(
            "INSERT INTO students (telegram_id, name, group_id, created_at) VALUES (?,?,?,?)",
            (tid, name, g["id"], core.iso(core.now())),
        )
    db.commit()
    set_state(db, tid, None)
    send(token, tid, t(lang, "joined", group=g["name"]), markup=main_keyboard(lang))
    send(token, tid, t(lang, "lang_ask"), keyboard=lang_keyboard())
    student = student_of(db, tid)
    send(token, tid, t(lang, "welcome2"))
    if student:
        sets = core.open_sets(db, student["group_id"])
        if sets:
            send(token, tid, checklist_text(db, student, lang))
    return


def handle_text(db, token, msg):
    tid = msg["from"]["id"]
    text = (msg.get("text") or "").strip()
    text = BUTTON_COMMANDS.get(text, text)
    student = student_of(db, tid)
    lang = student["lang"] if student else "en"
    step, payload = get_state(db, tid)

    # a teacher answering a question, or anyone mid-question, is handled first
    if step == "answer" and text and not text.startswith("/"):
        qid = payload.get("question")
        q = db.execute("SELECT * FROM questions WHERE id=?", (qid,)).fetchone()
        set_state(db, tid, None)
        if q:
            db.execute("UPDATE questions SET answer=?, answered_at=? WHERE id=?",
                       (text, core.iso(core.now()), qid))
            db.commit()
            target = db.execute("SELECT telegram_id, lang FROM students WHERE id=?",
                                (q["student_id"],)).fetchone()
            if target and target["telegram_id"]:
                send(token, target["telegram_id"],
                     t(target["lang"], "ask_answer", answer=text))
            return send(token, tid, "Answer sent.")
        return send(token, tid, "That question is gone.")

    if step == "ask" and text and not text.startswith("/"):
        set_state(db, tid, None)
        if not student:
            return send(token, tid, t(lang, "no_group"))
        qid = db.execute(
            "INSERT INTO questions (student_id, text, created_at) VALUES (?,?,?)",
            (student["id"], text[:1000], core.iso(core.now())),
        ).lastrowid
        db.commit()
        for teacher in json.loads(core.meta_get(db, "teachers", "[]")):
            send(token, teacher, "Question from %s:\n\n%s" % (student["name"], text[:1000]),
                 keyboard=[[{"text": "Answer", "callback_data": f"ans:{qid}"}]])
        return send(token, tid, t(lang, "ask_sent"))

    if step == "quiz" and payload.get("typed") and text and not text.startswith("/"):
        return answer_typed(db, token, student, text)

    if text.startswith("/start"):
        # "https://t.me/yourbot?start=AB12CD" arrives here as "/start AB12CD"
        parts = text.split(maxsplit=1)
        payload = parts[1].strip().upper() if len(parts) > 1 else ""
        carried = {}
        if payload.startswith("P") and len(payload) > 8:
            # a parent link, not a student one
            row = db.execute("SELECT * FROM parents WHERE token=?", (parts[1].strip()[1:],)).fetchone()
            if row:
                db.execute("UPDATE parents SET telegram_id=? WHERE id=?", (tid, row["id"]))
                db.commit()
                child = db.execute("SELECT name FROM students WHERE id=?",
                                   (row["student_id"],)).fetchone()
                return send(token, tid,
                            "You will get a weekly summary for %s here."
                            % (child["name"] if child else "your child"))
            return send(token, tid, "That parent link is not valid.")
        if payload:
            g = db.execute(
                "SELECT * FROM groups WHERE join_code=? AND archived=0", (payload,)
            ).fetchone()
            if g:
                carried["code"] = g["join_code"]
        set_state(db, tid, "name", carried)
        return send(token, tid, t(lang, "ask_name"))

    if text.startswith("/language"):
        return send(token, tid, t(lang, "lang_ask"), keyboard=lang_keyboard())

    if text.startswith("/progress"):
        if not student:
            return send(token, tid, t(lang, "no_group"))
        st = core.student_stats(db, student["id"])
        if not st["graded_count"]:
            return send(token, tid, t(lang, "no_scores"))
        image, _ = student_chart_png(db, student)
        caption = t(lang, "chart_caption", avg=st["average"], last3=st["last3"],
                    completion=st["completion"] if st["completion"] is not None else "-")
        send_photo(token, tid, image, caption)
        v = core.vocab_stats(db, student["id"])
        if v["practised"]:
            send(token, tid, t(lang, "vocab_stats", known=v["known"], total=v["total"],
                               mastery=v["mastery"], accuracy=v["accuracy"], due=v["due"]))
        return

    if text.startswith("/homework") or text.startswith("/hw"):
        if not student:
            return send(token, tid, t(lang, "no_group"))
        return send(token, tid, checklist_text(db, student, lang))

    if text.startswith("/ask"):
        if not student:
            return send(token, tid, t(lang, "no_group"))
        set_state(db, tid, "ask")
        return send(token, tid, t(lang, "ask_prompt"))

    if text.startswith("/rating"):
        if not student:
            return send(token, tid, t(lang, "no_group"))
        return send(token, tid, rating_text(db, student))

    if text.startswith("/vocab"):
        if not student:
            return send(token, tid, t(lang, "no_group"))
        lists = core.lists_for_student(db, student["id"])
        if not lists:
            return send(token, tid, t(lang, "vocab_none"))
        if len(lists) == 1:
            return offer_modes(db, token, student, lists[0]["id"])
        kb = [[{"text": wl["title"][:40], "callback_data": f"vl:{wl['id']}"}] for wl in lists]
        return send(token, tid, t(lang, "vocab_pick"), keyboard=kb)

    if text.startswith("/iamteacher"):
        # one-time claim: proves it is you by using the dashboard password
        parts = text.split(maxsplit=1)
        cfg = core.load_config()
        if len(parts) == 2 and parts[1].strip() == cfg["teacher_password"]:
            ids = json.loads(core.meta_get(db, "teachers", "[]"))
            if str(tid) not in ids:
                ids.append(str(tid))
            core.meta_set(db, "teachers", json.dumps(ids))
            return send(token, tid, "You are registered as the teacher.\n"
                                    "/report — group and student charts\n"
                                    "/pending — how many submissions are waiting")
        return send(token, tid, "Wrong password.")

    if text.startswith("/report"):
        if not is_teacher(db, tid):
            return send(token, tid, t(lang, "help"))
        return teacher_report(db, token, tid)

    if text.startswith("/pending"):
        if not is_teacher(db, tid):
            return send(token, tid, t(lang, "help"))
        n = db.execute("SELECT COUNT(*) c FROM submissions WHERE status='pending'").fetchone()["c"]
        return send(token, tid, f"{n} submission(s) waiting to be graded.")

    if text.startswith("/cancel") or text.startswith("/stop"):
        step, _ = get_state(db, tid)
        set_state(db, tid, None)
        return send(token, tid, t(lang, "cancelled" if step else "nothing_cancel"),
                    markup=main_keyboard(lang) if student else None)

    if text.startswith("/help"):
        return send(token, tid, t(lang, "help"))

    if step == "name" and text:
        name = text[:80]
        if payload.get("code"):
            return join_group(db, token, tid, name, payload["code"], lang)
        set_state(db, tid, "code", {"name": name})
        return send(token, tid, t(lang, "ask_code", name=name))

    if step == "code" and text:
        name = payload.get("name") or msg["from"].get("first_name", "Student")
        return join_group(db, token, tid, name, text.strip().upper(), lang)

    if not student:
        return send(token, tid, t(lang, "no_group"))
    return send(token, tid, t(lang, "lost"), markup=main_keyboard(lang))


def handle_photo(db, token, msg):
    tid = msg["from"]["id"]
    student = student_of(db, tid)
    if not student:
        return send(token, tid, t("en", "no_group"))
    lang = student["lang"]

    photo = max(msg["photo"], key=lambda p: p.get("width", 0) * p.get("height", 0))
    # free quality gate: Telegram hands us the dimensions, so a page shot that
    # is too small to read never costs a grading slot
    if max(photo.get("width", 0), photo.get("height", 0)) < CFG_MIN_WIDTH:
        return send(token, tid, t(lang, "too_small"))

    mgid = msg.get("media_group_id")
    sub = None
    if mgid:
        sub = db.execute(
            "SELECT * FROM submissions WHERE student_id=? AND media_group_id=?",
            (student["id"], mgid),
        ).fetchone()

    first_page = sub is None
    if first_page:
        opens = open_assignments(db, student["group_id"])
        aid = opens[0]["id"] if opens else None
        due = opens[0]["due_at"] if opens else None
        for a in opens:
            if a["id"] == aid:
                due = a["due_at"]
        late = 1 if (due and due < core.iso(core.now())) else 0
        improves = None
        step, stt = get_state(db, tid)
        if step == "improve":
            improves = stt.get("submission")
            set_state(db, tid, None)
        cur = db.execute(
            "INSERT INTO submissions (student_id, assignment_id, created_at,"
            " media_group_id, late, improves) VALUES (?,?,?,?,?,?)",
            (student["id"], aid, core.iso(core.now()), mgid, late, improves),
        )
        db.commit()
        sub_id = cur.lastrowid
    else:
        sub_id = sub["id"]
        opens = open_assignments(db, student["group_id"])

    ord_ = db.execute(
        "SELECT COUNT(*) c FROM files WHERE submission_id=?", (sub_id,)
    ).fetchone()["c"]
    fname = f"{sub_id}_{ord_}_{int(time.time())}.jpg"
    if not download_photo(token, photo["file_id"], fname):
        return send(token, tid, "Could not download that photo, please resend.")
    db.execute(
        "INSERT INTO files (submission_id, filename, telegram_file_id, width, height, ord)"
        " VALUES (?,?,?,?,?,?)",
        (sub_id, fname, photo["file_id"], photo.get("width"), photo.get("height"), ord_),
    )
    db.commit()

    if not first_page:
        return  # stay quiet for the rest of an album
    notify_teachers_new(db, token, sub_id)
    if not opens:
        return send(token, tid, t(lang, "no_assignment"))
    kb = None
    if len(opens) > 1:
        done_ids = {r["assignment_id"] for r in db.execute(
            "SELECT DISTINCT assignment_id FROM submissions WHERE student_id=?"
            " AND assignment_id IS NOT NULL AND id!=?", (student["id"], sub_id))}
        # what they still owe comes first - that is almost always the answer
        ordered = ([a for a in opens if a["id"] not in done_ids]
                   + [a for a in opens if a["id"] in done_ids])
        kb = [[{"text": (("\u2705 " if a["id"] in done_ids else "\u2b1c ") + a["title"])[:60],
                "callback_data": f"pick:{sub_id}:{a['id']}"}]
              for a in ordered[:12]]
        kb.append([{"text": t(lang, "not_listed"), "callback_data": f"pick:{sub_id}:0"}])
        return send(token, tid, t(lang, "which"), keyboard=kb)
    send(token, tid,
         t(lang, "received", title=opens[0]["title"]) + "\n" + t(lang, "more_pages"),
         keyboard=[[{"text": t(lang, "undo"), "callback_data": f"del:{sub_id}"}]])
    return send(token, tid, remaining_text(db, student, opens[0]["due_at"]))


def handle_voice(db, token, msg):
    """A voice note is a speaking submission - same queue, no size gate."""
    tid = msg["from"]["id"]
    student = student_of(db, tid)
    if not student:
        return send(token, tid, t("en", "no_group"))
    lang = student["lang"]
    voice = msg.get("voice") or msg.get("audio") or {}
    opens = open_assignments(db, student["group_id"])
    aid = opens[0]["id"] if opens else None
    due = opens[0]["due_at"] if opens else None
    sub_id = db.execute(
        "INSERT INTO submissions (student_id, assignment_id, created_at, kind, late)"
        " VALUES (?,?,?,'voice',?)",
        (student["id"], aid, core.iso(core.now()),
         1 if (due and due < core.iso(core.now())) else 0),
    ).lastrowid
    db.commit()
    fname = f"{sub_id}_0_{int(time.time())}.oga"
    if not download_photo(token, voice.get("file_id"), fname):
        return send(token, tid, "Could not download that recording, please resend.")
    db.execute("INSERT INTO files (submission_id, filename, telegram_file_id, ord)"
               " VALUES (?,?,?,0)", (sub_id, fname, voice.get("file_id")))
    db.commit()
    notify_teachers_new(db, token, sub_id)
    if not opens:
        return send(token, tid, t(lang, "no_assignment"))
    if len(opens) > 1:
        kb = [[{"text": a["title"][:60], "callback_data": f"pick:{sub_id}:{a['id']}"}]
              for a in opens[:12]]
        return send(token, tid, t(lang, "which"), keyboard=kb)
    return send(token, tid, t(lang, "received", title=opens[0]["title"]))


def handle_callback(db, token, cq):
    tid = cq["from"]["id"]
    data = cq.get("data", "")
    call(token, "answerCallbackQuery", callback_query_id=cq["id"])

    if data.startswith("lang:"):
        lang = data.split(":", 1)[1]
        db.execute("UPDATE students SET lang=? WHERE telegram_id=?", (lang, tid))
        db.commit()
        return send(token, tid, t(lang, "lang_set"), markup=main_keyboard(lang))

    if data.startswith("g:") and is_teacher(db, tid):
        _, sub_id, score = data.split(":")
        row = grade_submission(db, token, int(sub_id), int(score))
        return send(token, tid, "Saved %s/10 for %s." % (
            score, row["title"] or "unassigned" if row else "?"))

    if data.startswith("ans:") and is_teacher(db, tid):
        set_state(db, tid, "answer", {"question": int(data.split(":")[1])})
        return send(token, tid, "Type your answer; I will pass it on.")

    if data.startswith("imp:"):
        student = student_of(db, tid)
        if student:
            set_state(db, tid, "improve", {"submission": int(data.split(":")[1])})
            send(token, tid, t(student["lang"], "improve") + " \u2b07")
        return

    if data.startswith("vl:"):
        student = student_of(db, tid)
        if student:
            offer_modes(db, token, student, int(data.split(":")[1]))
        return

    if data == "qstop":
        student = student_of(db, tid)
        set_state(db, tid, None)
        if student:
            send(token, tid, t(student["lang"], "cancelled"),
                 markup=main_keyboard(student["lang"]))
        return

    if data.startswith("vo:"):
        student = student_of(db, tid)
        if student:
            offer_modes_full(db, token, student, int(data.split(":")[1]))
        return

    if data.startswith("del:"):
        student = student_of(db, tid)
        if not student:
            return
        sub_id = int(data.split(":")[1])
        row = db.execute("SELECT * FROM submissions WHERE id=? AND student_id=?",
                         (sub_id, student["id"])).fetchone()
        if not row:
            return
        if row["status"] == "graded":
            return send(token, tid, t(student["lang"], "undo_late"))
        for f in db.execute("SELECT filename FROM files WHERE submission_id=?", (sub_id,)):
            path = os.path.join(core.UPLOAD_DIR, f["filename"])
            if os.path.exists(path):
                os.remove(path)
        db.execute("DELETE FROM files WHERE submission_id=?", (sub_id,))
        db.execute("DELETE FROM submissions WHERE id=?", (sub_id,))
        db.commit()
        return send(token, tid, t(student["lang"], "undone"))

    if data.startswith("vm:"):
        student = student_of(db, tid)
        if student:
            _, lid, mode = data.split(":")
            offer_scope(db, token, student, int(lid), mode)
        return

    if data.startswith("vs:"):
        student = student_of(db, tid)
        if student:
            _, lid, mode, scope = data.split(":")
            offer_length(db, token, student, int(lid), mode, scope)
        return

    if data.startswith("vg:"):
        student = student_of(db, tid)
        if student:
            _, lid, mode, scope, n = data.split(":")
            start_quiz(db, token, student, int(lid), mode, scope, int(n))
        return

    if data.startswith("q:"):
        student = student_of(db, tid)
        if student:
            answer_question(db, token, student, data.split(":")[2])
        return

    if data.startswith("rg:") and is_teacher(db, tid):
        g = db.execute("SELECT * FROM groups WHERE id=?", (int(data.split(":")[1]),)).fetchone()
        if not g:
            return
        send_photo(token, tid, group_chart_png(db, g), g["name"])
        studs = db.execute(
            "SELECT id, name FROM students WHERE group_id=? AND active=1 ORDER BY name",
            (g["id"],),
        ).fetchall()
        if studs:
            kb = [[{"text": st["name"][:40], "callback_data": f"rs:{st['id']}"}] for st in studs]
            send(token, tid, "Open a student:", keyboard=kb)
        return

    if data.startswith("rs:") and is_teacher(db, tid):
        st = db.execute("SELECT * FROM students WHERE id=?", (int(data.split(":")[1]),)).fetchone()
        if not st:
            return
        image, stats = student_chart_png(db, st)
        v = core.vocab_stats(db, st["id"])
        cap = (f"{st['name']} · avg {stats['average'] or '-'}/10 · "
               f"completion {stats['completion'] if stats['completion'] is not None else '-'}%")
        if v["practised"]:
            cap += f" · vocabulary {v['known']}/{v['total']}"
        send_photo(token, tid, image, cap)
        return

    if data.startswith("pick:"):
        _, sub_id, aid = data.split(":")
        student = student_of(db, tid)
        if not student:
            return
        if aid == "0":
            db.execute("UPDATE submissions SET assignment_id=NULL WHERE id=? AND student_id=?",
                       (int(sub_id), student["id"]))
            db.commit()
            return send(token, tid, t(student["lang"], "unassigned_ok"))
        db.execute(
            "UPDATE submissions SET assignment_id=? WHERE id=? AND student_id=?",
            (int(aid), int(sub_id), student["id"]),
        )
        db.commit()
        a = db.execute("SELECT * FROM assignments WHERE id=?", (int(aid),)).fetchone()
        send(token, tid, t(student["lang"], "reassigned", title=a["title"]),
             keyboard=[[{"text": t(student["lang"], "undo"),
                         "callback_data": f"del:{sub_id}"}]])
        return send(token, tid, remaining_text(db, student, a["due_at"]))


# -------------------------------------------------------------------- loop

CFG_MIN_WIDTH = 800


def main():
    global CFG_MIN_WIDTH
    cfg = core.load_config()
    token = cfg["telegram_token"]
    if not token:
        raise SystemExit("Set telegram_token in config.json (or TELEGRAM_TOKEN) first.")
    CFG_MIN_WIDTH = cfg["min_photo_width"]
    core.init_db()
    me = call(token, "getMe")
    if not me.get("ok"):
        raise SystemExit(f"Telegram rejected the token: {me}")
    username = me["result"].get("username") or ""
    db = core.connect()
    core.meta_set(db, "bot_username", username)
    db.close()
    set_commands(token)
    print(f"Bot @{username} polling. Ctrl-C to stop.")

    offset = None
    while True:
        res = call(token, "getUpdates", offset=offset, timeout=50,
                   allowed_updates=["message", "callback_query"])
        if not res.get("ok"):
            time.sleep(3)
            continue
        db = core.connect()
        try:
            for upd in res["result"]:
                offset = upd["update_id"] + 1
                try:
                    if "callback_query" in upd:
                        handle_callback(db, token, upd["callback_query"])
                    elif "message" in upd:
                        msg = upd["message"]
                        if "photo" in msg:
                            handle_photo(db, token, msg)
                        elif "voice" in msg or "audio" in msg:
                            handle_voice(db, token, msg)
                        elif "text" in msg:
                            handle_text(db, token, msg)
                except Exception as exc:  # one bad update must not kill the bot
                    print("update error:", exc)
        finally:
            db.close()


if __name__ == "__main__":
    main()
