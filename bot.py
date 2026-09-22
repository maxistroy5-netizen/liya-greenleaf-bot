import os
import re
import tempfile
import threading
from datetime import date
from urllib.parse import urlsplit, urlunsplit
from http.server import BaseHTTPRequestHandler, HTTPServer

from openai import OpenAI
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from card_generator import generate_business_card

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)

MAIN_KEYBOARD = ReplyKeyboardMarkup([
    ["🌱 Я новичок", "📊 Маркетинг-план"],
    ["🤝 Подготовка к встрече", "💬 Тренировка диалога"],
    ["🎓 Проверить знания", "✍️ Задать вопрос"],
    ["🔍 Разбор тренировки", "🧰 Инструменты"],
], resize_keyboard=True, is_persistent=True)

TRAINING_LEVEL_KEYBOARD = ReplyKeyboardMarkup([
    ["🟢 Лёгкий", "🟡 Средний"], ["🔴 Сложный"], ["⬅️ Главное меню"]
], resize_keyboard=True, is_persistent=True)

TOOLS_KEYBOARD = ReplyKeyboardMarkup([
    ["📱 Создать электронную визитку"],
    ["🤝 3 шага приглашения партнёра"],
    ["⬅️ Главное меню"],
], resize_keyboard=True, is_persistent=True)

CARD_CONFIRM_KEYBOARD = ReplyKeyboardMarkup([
    ["✅ Всё верно", "✏️ Заполнить заново"],
    ["⬅️ Главное меню"],
], resize_keyboard=True, is_persistent=True)

INVITE_STEP1_KEYBOARD = ReplyKeyboardMarkup([
    ["➡️ Шаг 2", "✏️ Изменить текст"],
    ["⬅️ Главное меню"],
], resize_keyboard=True, is_persistent=True)

INVITE_STEP2_KEYBOARD = ReplyKeyboardMarkup([
    ["➡️ Шаг 3", "✏️ Изменить текст"],
    ["⬅️ Главное меню"],
], resize_keyboard=True, is_persistent=True)

INVITE_STEP3_KEYBOARD = ReplyKeyboardMarkup([
    ["🔄 Новое приглашение", "✏️ Изменить текст"],
    ["⬅️ Главное меню"],
], resize_keyboard=True, is_persistent=True)

CARD_FIELDS = [
    ("name", "1/8. Напиши имя и фамилию, как они должны выглядеть на визитке."),
    ("phone", "2/8. Укажи номер телефона."),
    ("telegram", "3/8. Укажи Telegram: @username, номер или ссылку."),
    ("whatsapp", "4/8. Укажи WhatsApp: номер или ссылку."),
    ("max", "5/8. Укажи MAX: номер, имя пользователя или ссылку."),
    ("email", "6/8. Укажи e-mail."),
    ("instagram", "7/8. Укажи Instagram: @username или ссылку."),
    ("photo", "8/8. Теперь отправь своё фото отдельным сообщением. Если пока хочешь только проверить анкету — напиши «пропустить»."),
]

ECOSYSTEM_URL = "https://t.me/addlist/JxquFZkrHw4yYTMy"
BRAND_NAME = "GREENLEAF Leaders | Москва"

with open("knowledge.txt", "r", encoding="utf-8") as f:
    KNOWLEDGE = f.read()
with open("practice_partner.txt", "r", encoding="utf-8") as f:
    PRACTICE_KNOWLEDGE = f.read()
with open("company_knowledge.txt", "r", encoding="utf-8") as f:
    COMPANY_KNOWLEDGE = f.read()

LIYA_PROMPT = """
Ты — Лия, персональный AI-тренер партнёров Greenleaf. Общайся простым русским языком, доброжелательно, уверенно и профессионально.

ИСТОЧНИКИ И БЕЗОПАСНОСТЬ:
1. Маркетинг-план: CURRENT — подтверждённая база. VERIFY всегда обозначай как неподтверждённое и не используй для точного расчёта. Не придумывай отсутствующие правила, проценты или формулы. PV — баллы объёма, а не заработанные деньги.
2. Общие вопросы о компании, истории, географии, представительствах, сертификатах, брендах и продукции — COMPANY-база.
3. Для динамической корпоративной информации разрешён LIVE-поиск только по разрешённым официальным источникам.
4. LIVE НИКОГДА не меняет PV, статусы, бонусы, проценты, квалификации, формулы и расчёты маркетинг-плана: они берутся только из CURRENT.
5. Если LIVE реально использован и дал надёжный ответ, в самом конце поставь отдельной строкой: «🌐 По актуальным данным официальных источников Greenleaf на ДД.ММ.ГГГГ.» Используй фактическую дату проверки.
6. Если LIVE не использовался или не дал надёжного ответа, не добавляй эту подпись и не утверждай, что проверка состоялась.
7. ОБЫЧНЫЙ ВОПРОС: дай чистый ответ без URL, без Markdown-ссылок, без технических параметров и без перечня источников.
8. ИСТОЧНИК ПО ПРОСЬБЕ: только если пользователь прямо просит источник, ссылку, где посмотреть или откуда информация — дай 1–3 наиболее конкретные официальные ссылки. Каждую ссылку показывай только один раз. Не добавляй utm_source, ysclid и другие технические параметры.
9. Если официальные источники дают разные цифры или формулировки, спокойно укажи расхождение; не выбирай одну цифру без основания.
10. Не используй Markdown со звёздочками. Для акцента используй короткие заголовки, переносы строк и эмодзи.

ОБУЧЕНИЕ:
11. Новичка обучай маленькими уроками; после важного понятия задавай один вопрос и проверяй понимание. При ошибке объясни её и не переходи дальше, пока тема не понята.
12. Всегда учитывай историю текущего диалога. Короткий ответ А/Б/В/Г трактуй как ответ на последний вопрос с вариантами.
13. Не перегружай человека информацией. Если данных недостаточно — прямо скажи, чего не хватает.
"""

MODES = {
    "🌱 Я новичок": "Начни обучение маркетинг-плану с нуля маленькими уроками. После каждого важного понятия задай один вопрос. Не переходи дальше, пока пользователь не понял тему.",
    "📊 Маркетинг-план": "Помоги разобраться в маркетинг-плане. Используй CURRENT как основной источник. Сначала спроси тему или предложи несколько тем из базы.",
    "🤝 Подготовка к встрече": "Помоги подготовиться к разговору с потенциальным партнёром. Сначала выясни, с кем встреча и какова цель разговора.",
    "💬 Тренировка диалога": "Проводи реалистичную ролевую тренировку. Играй потенциального партнёра/клиента, не выходи из роли и не подсказывай готовый ответ. После 4–6 содержательных реплик останови роль заголовком «РАЗБОР ТРЕНИРОВКИ», дай краткий разбор и один улучшенный вариант ответа.",
    "🎓 Проверить знания": "Проверяй знания маркетинг-плана только по CURRENT. Задавай по одному вопросу; после ответа объясняй ошибку, если она есть, и только потом продолжай.",
    "✍️ Задать вопрос": "Предложи написать любой вопрос о Greenleaf или маркетинг-плане. Для корпоративных динамических фактов при необходимости используй LIVE; маркетинг-план не проверяй через интернет.",
    "🔍 Разбор тренировки": "Выйди из роли. Начни с «🔍 РАЗБОР ТРЕНИРОВКИ». Укажи, что получилось хорошо, где мог потеряться интерес/доверие, фактические ошибки, один улучшенный пример ответа. В конце спроси: «Продолжаем этот диалог или попробуем нового собеседника?»",
}

LEVELS = {
    "🟢 Лёгкий": "УРОВЕНЬ ЛЁГКИЙ: доброжелательный собеседник, простой интерес, мягкие возражения.",
    "🟡 Средний": "УРОВЕНЬ СРЕДНИЙ: сомневайся, уточняй; возражения: дорого, нет времени, надо подумать, сомнения к сетевому бизнесу.",
    "🔴 Сложный": "УРОВЕНЬ СЛОЖНЫЙ: опытный требовательный скептик, конкретные неудобные вопросы, проси подтверждать утверждения; не груби.",
}

SOURCE_REQUEST_RE = re.compile(r"(?i)\b(источник|источники|ссылк\w*|где\s+(?:это\s+)?посмотреть|откуда\s+(?:ты\s+)?(?:взял\w*|информац\w*)|подтвержден\w*|официальн\w+\s+источник)\b")
URL_RE = re.compile(r"https?://[^\s)\]>]+")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")


def clean_url(url: str) -> str:
    url = url.rstrip(".,;:!?")
    try:
        p = urlsplit(url)
        return urlunsplit((p.scheme, p.netloc, p.path, "", ""))
    except Exception:
        return url.split("?", 1)[0]


def dedupe_urls(text: str) -> str:
    seen = set()
    def repl(m):
        url = clean_url(m.group(0))
        key = url.rstrip("/").lower()
        if key in seen:
            return ""
        seen.add(key)
        return url
    return URL_RE.sub(repl, text)


def polish_answer(answer: str, user_text: str) -> str:
    wants_source = bool(SOURCE_REQUEST_RE.search(user_text or ""))
    if wants_source:
        answer = MARKDOWN_LINK_RE.sub(lambda m: f"{m.group(1)}: {clean_url(m.group(2))}", answer)
        answer = URL_RE.sub(lambda m: clean_url(m.group(0)), answer)
        answer = dedupe_urls(answer)
    else:
        answer = MARKDOWN_LINK_RE.sub(lambda m: m.group(1), answer)
        answer = URL_RE.sub("", answer)
    answer = re.sub(r"\*\*([^*]+)\*\*", r"\1", answer)
    answer = re.sub(r"[ \t]+\n", "\n", answer)
    answer = re.sub(r"\n{3,}", "\n\n", answer)
    return answer.strip()


def card_summary(data: dict) -> str:
    photo_status = "получено" if data.get("photo") == "received" else "будет добавлено позже"
    return (
        "📱 Проверь данные для электронной визитки:\n\n"
        f"Имя: {data.get('name', '')}\nТелефон: {data.get('phone', '')}\n"
        f"Telegram: {data.get('telegram', '')}\nWhatsApp: {data.get('whatsapp', '')}\n"
        f"MAX: {data.get('max', '')}\nE-mail: {data.get('email', '')}\n"
        f"Instagram: {data.get('instagram', '')}\nФото: {photo_status}\n\n"
        f"Бренд: {BRAND_NAME}\nGREENLEAF CLUB.RU: {ECOSYSTEM_URL}\n\n"
        "Если всё верно — нажми «✅ Всё верно»."
    )


def invite_text(step: int, name: str, event_info: str = "") -> str:
    name = name.strip() or ""
    hello = f"{name}, привет!" if name else "Привет!"
    if step == 1:
        return (
            f"{hello} 😊 У меня сейчас много нового происходит — я развиваюсь в международном проекте Greenleaf. "
            "Хочу просто поделиться с тобой своей электронной визиткой: там можно спокойно посмотреть информацию о компании, продукции и возможностях. "
            "Посмотри, когда будет удобно, без обязательств 💚"
        )
    if step == 2:
        return f"{hello} 😊 Как твои впечатления от нашей корпорации? Что тебе откликнулось или заинтересовало больше всего?"
    return (
        f"{hello} 💚 Хочу пригласить тебя на наш субботний онлайн-эфир. Это хороший способ спокойно посмотреть, как всё устроено, "
        f"услышать информацию и задать вопросы. Начало в 10:00 по Москве.\n\n{event_info.strip()}"
    ).strip()


async def build_and_send_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data.get("card_data", {}).copy()
    photo_path = None
    pdf_path = None
    try:
        if context.user_data.get("card_photo_file_id"):
            tg_file = await context.bot.get_file(context.user_data["card_photo_file_id"])
            fd, photo_path = tempfile.mkstemp(prefix="greenleaf_photo_", suffix=".jpg")
            os.close(fd)
            await tg_file.download_to_drive(custom_path=photo_path)

        safe_name = re.sub(r"[^0-9A-Za-zА-Яа-яЁё_-]+", "_", data.get("name", "partner")).strip("_") or "partner"
        pdf_path = os.path.join(tempfile.gettempdir(), f"GREENLEAF_{safe_name}.pdf")
        generate_business_card(data, photo_path=photo_path, output_path=pdf_path)

        with open(pdf_path, "rb") as document:
            await update.message.reply_document(
                document=document,
                filename=f"GREENLEAF_{safe_name}.pdf",
                caption="💚 Готово! Твоя персональная электронная визитка GREENLEAF Leaders | Москва.\n\nВсе контактные кнопки и GREENLEAF CLUB.RU кликабельны.",
                reply_markup=TOOLS_KEYBOARD,
            )
        context.user_data["card_step"] = "ready"
    except Exception as exc:
        print(f"Business card generation error: {exc}")
        context.user_data["card_step"] = "confirm"
        await update.message.reply_text(
            "Не удалось собрать визитку с первого раза. Анкета сохранена — повторно заполнять её не нужно. Нажми «✅ Всё верно» ещё раз.",
            reply_markup=CARD_CONFIRM_KEYBOARD,
        )
    finally:
        for path in (photo_path, pdf_path):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["dialog_history"] = []
    await update.message.reply_text(
        "💚 Привет! Я Лия — персональный AI-тренер Greenleaf.\n\nЯ помогу разобраться в маркетинг-плане, подготовиться к встрече, потренировать диалог, проверить знания и использовать рабочие инструменты.",
        reply_markup=MAIN_KEYBOARD,
    )


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("card_step") != "photo":
        await update.message.reply_text("Фото получила. Чтобы использовать его для визитки, открой 🧰 Инструменты → 📱 Создать электронную визитку.", reply_markup=MAIN_KEYBOARD)
        return
    photos = update.message.photo
    context.user_data.setdefault("card_data", {})["photo"] = "received"
    context.user_data["card_photo_file_id"] = photos[-1].file_id
    context.user_data["card_step"] = "confirm"
    await update.message.reply_text(card_summary(context.user_data["card_data"]), reply_markup=CARD_CONFIRM_KEYBOARD)


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    context.user_data.setdefault("dialog_history", [])
    context.user_data.setdefault("training_history", [])

    if user_text == "⬅️ Главное меню":
        context.user_data.clear()
        context.user_data["dialog_history"] = []
        await update.message.reply_text("Главное меню:", reply_markup=MAIN_KEYBOARD)
        return

    if user_text == "🧰 Инструменты":
        context.user_data.pop("card_step", None)
        context.user_data.pop("invite_step", None)
        await update.message.reply_text("🧰 ИНСТРУМЕНТЫ\n\nЗдесь мы собираем готовые рабочие материалы нашей структуры. Выбери, что нужно:", reply_markup=TOOLS_KEYBOARD)
        return

    if user_text == "📱 Создать электронную визитку":
        context.user_data["card_data"] = {}
        context.user_data.pop("card_photo_file_id", None)
        context.user_data["card_index"] = 0
        context.user_data["card_step"] = CARD_FIELDS[0][0]
        await update.message.reply_text(
            "📱 ЭЛЕКТРОННАЯ ВИЗИТКА\n\nЯ соберу данные пошагово. В готовом материале будут обязательны бренд нашей структуры и единый QR GREENLEAF CLUB.RU.\n\n" + CARD_FIELDS[0][1],
            reply_markup=ReplyKeyboardMarkup([["⬅️ Главное меню"]], resize_keyboard=True, is_persistent=True),
        )
        return

    if user_text == "✏️ Заполнить заново":
        context.user_data["card_data"] = {}
        context.user_data.pop("card_photo_file_id", None)
        context.user_data["card_index"] = 0
        context.user_data["card_step"] = CARD_FIELDS[0][0]
        await update.message.reply_text(CARD_FIELDS[0][1])
        return

    if user_text == "✅ Всё верно" and context.user_data.get("card_step") == "confirm":
        await update.message.reply_text("⏳ Собираю персональную брендированную визитку…")
        await build_and_send_card(update, context)
        return

    card_step = context.user_data.get("card_step")
    if card_step and card_step not in {"confirm", "ready", "photo"}:
        index = context.user_data.get("card_index", 0)
        field_name, _ = CARD_FIELDS[index]
        context.user_data.setdefault("card_data", {})[field_name] = user_text.strip()
        index += 1
        context.user_data["card_index"] = index
        next_field, prompt = CARD_FIELDS[index]
        context.user_data["card_step"] = next_field
        await update.message.reply_text(prompt)
        return

    if card_step == "photo":
        if user_text.strip().lower() in {"пропустить", "пропускаю", "нет фото"}:
            context.user_data.setdefault("card_data", {})["photo"] = "skipped"
            context.user_data["card_step"] = "confirm"
            await update.message.reply_text(card_summary(context.user_data["card_data"]), reply_markup=CARD_CONFIRM_KEYBOARD)
        else:
            await update.message.reply_text("Отправь фотографию как фото в Telegram или напиши «пропустить».")
        return

    if user_text in {"🤝 3 шага приглашения партнёра", "🔄 Новое приглашение"}:
        context.user_data.pop("card_step", None)
        context.user_data["invite_step"] = "name"
        context.user_data["invite_data"] = {}
        await update.message.reply_text(
            "🤝 3 ШАГА ПРИГЛАШЕНИЯ\n\nЯ проведу тебя по трём касаниям и дам готовые сообщения, которые можно отправить человеку.\n\nДля начала напиши имя человека, которого хочешь пригласить.",
            reply_markup=ReplyKeyboardMarkup([["⬅️ Главное меню"]], resize_keyboard=True, is_persistent=True),
        )
        return

    invite_step = context.user_data.get("invite_step")
    if invite_step == "name":
        name = user_text.strip()
        context.user_data["invite_data"] = {"name": name}
        text = invite_text(1, name)
        context.user_data["invite_data"]["last_text"] = text
        context.user_data["invite_data"]["current_step"] = 1
        context.user_data["invite_step"] = "step1_ready"
        await update.message.reply_text(
            "1️⃣ ПЕРВОЕ КАСАНИЕ\n\nОтправь человеку свою электронную визитку и это сообщение:\n\n" + text + "\n\nЕсли текст подходит — переходи к шагу 2. Если хочешь другой тон, нажми «✏️ Изменить текст».",
            reply_markup=INVITE_STEP1_KEYBOARD,
        )
        return

    if user_text == "➡️ Шаг 2" and invite_step == "step1_ready":
        name = context.user_data.get("invite_data", {}).get("name", "")
        text = invite_text(2, name)
        context.user_data["invite_data"]["last_text"] = text
        context.user_data["invite_data"]["current_step"] = 2
        context.user_data["invite_step"] = "step2_ready"
        await update.message.reply_text(
            "2️⃣ ВТОРОЕ КАСАНИЕ\n\nЧерез 1–2 дня мягко вернись в диалог:\n\n" + text + "\n\nНе перегружай человека информацией — сначала выслушай его ответ.",
            reply_markup=INVITE_STEP2_KEYBOARD,
        )
        return

    if user_text == "➡️ Шаг 3" and invite_step == "step2_ready":
        context.user_data["invite_step"] = "event_info"
        await update.message.reply_text(
            "3️⃣ ТРЕТЬЕ КАСАНИЕ\n\nТеперь приглашение на субботний эфир в 10:00 по Москве.\n\nНапиши одним сообщением актуальную дату эфира и ссылку Zoom. Например:\n28 сентября\nhttps://...",
            reply_markup=ReplyKeyboardMarkup([["⬅️ Главное меню"]], resize_keyboard=True, is_persistent=True),
        )
        return

    if invite_step == "event_info":
        name = context.user_data.get("invite_data", {}).get("name", "")
        context.user_data["invite_data"]["event_info"] = user_text.strip()
        text = invite_text(3, name, user_text)
        context.user_data["invite_data"]["last_text"] = text
        context.user_data["invite_data"]["current_step"] = 3
        context.user_data["invite_step"] = "step3_ready"
        await update.message.reply_text(
            "3️⃣ ГОТОВОЕ ПРИГЛАШЕНИЕ\n\n" + text + "\n\n💚 Три касания готовы. Главное — не давить, а вести человека спокойно от знакомства к диалогу.",
            reply_markup=INVITE_STEP3_KEYBOARD,
        )
        return

    if user_text == "✏️ Изменить текст" and invite_step in {"step1_ready", "step2_ready", "step3_ready"}:
        context.user_data["invite_step_before_edit"] = invite_step
        context.user_data["invite_step"] = "edit_request"
        await update.message.reply_text(
            "Напиши, что именно изменить. Например: «короче», «теплее», «для близкой подруги», «более деловой тон» или опиши свой вариант.",
            reply_markup=ReplyKeyboardMarkup([["⬅️ Главное меню"]], resize_keyboard=True, is_persistent=True),
        )
        return

    if invite_step == "edit_request":
        data = context.user_data.get("invite_data", {})
        current_text = data.get("last_text", "")
        step_num = data.get("current_step", 1)
        edit_instruction = user_text.strip()
        response = client.responses.create(
            model="gpt-5.6",
            instructions=(
                "Ты редактируешь короткое личное сообщение для приглашения в Greenleaf. Сохрани смысл исходного сообщения, не добавляй обещаний дохода, давления, срочности или неподтверждённых фактов. "
                "Верни только готовый текст сообщения без пояснений, заголовков, кавычек и Markdown. Пиши естественно и по-человечески."
            ),
            input=f"Исходный текст:\n{current_text}\n\nПожелание пользователя:\n{edit_instruction}",
        )
        edited = response.output_text.strip()
        data["last_text"] = edited
        previous = context.user_data.pop("invite_step_before_edit", f"step{step_num}_ready")
        context.user_data["invite_step"] = previous
        keyboard = INVITE_STEP1_KEYBOARD if step_num == 1 else INVITE_STEP2_KEYBOARD if step_num == 2 else INVITE_STEP3_KEYBOARD
        await update.message.reply_text("✏️ Вот обновлённый вариант:\n\n" + edited, reply_markup=keyboard)
        return

    if user_text == "💬 Тренировка диалога":
        context.user_data["awaiting_training_level"] = True
        await update.message.reply_text("Выбери уровень сложности тренировки:", reply_markup=TRAINING_LEVEL_KEYBOARD)
        return

    if user_text in LEVELS:
        context.user_data["mode"] = "💬 Тренировка диалога"
        context.user_data["training_level_prompt"] = LEVELS[user_text]
        context.user_data["training_history"] = []
        context.user_data["dialog_history"] = []
        context.user_data["awaiting_training_level"] = False
        await update.message.reply_text(f"{user_text} уровень выбран.\n\nНачинаем тренировку. Напиши свою первую реплику потенциальному партнёру.", reply_markup=MAIN_KEYBOARD)
        return

    if user_text in MODES:
        if user_text == "🔍 Разбор тренировки":
            history = context.user_data.get("training_history", [])
            context.user_data.pop("mode", None)
            ai_input = MODES[user_text] + "\n\nПолный диалог последней тренировки:\n" + "\n".join(history)
            context.user_data["training_history"] = []
        else:
            context.user_data["mode"] = user_text
            context.user_data["dialog_history"] = []
            if user_text == "💬 Тренировка диалога":
                context.user_data["training_history"] = []
            ai_input = MODES[user_text]
    else:
        active_mode = context.user_data.get("mode")
        if active_mode == "💬 Тренировка диалога":
            context.user_data["training_history"].append("Пользователь: " + user_text)
        ai_input = MODES.get(active_mode, "Пользователь задаёт вопрос Лии.") + "\n\nНовая реплика пользователя: " + user_text

    today_str = date.today().strftime("%d.%m.%Y")
    final_instructions = (
        LIYA_PROMPT
        + "\n\nБАЗА МАРКЕТИНГ-ПЛАНА GREENLEAF:\n" + KNOWLEDGE
        + "\n\nБАЗА О КОМПАНИИ GREENLEAF:\n" + COMPANY_KNOWLEDGE
        + "\n\nДАТА ТЕКУЩЕЙ ПРОВЕРКИ: " + today_str
        + "\nЕсли реально использовала web_search и получила надёжные данные, финальная строка должна быть точно: 🌐 По актуальным данным официальных источников Greenleaf на " + today_str + "."
    )

    practice_modes = {"🤝 Подготовка к встрече", "💬 Тренировка диалога", "🔍 Разбор тренировки"}
    active = context.user_data.get("mode")
    if user_text in practice_modes:
        active = user_text
    if active in practice_modes:
        final_instructions += "\n\nБАЗА ПРАКТИЧЕСКИХ НАВЫКОВ ПАРТНЁРА:\n" + PRACTICE_KNOWLEDGE + "\nЭта база НЕ является маркетинг-планом."
    if active == "💬 Тренировка диалога":
        final_instructions += "\n\nНАСТРОЙКИ ТРЕНИРОВКИ:\n" + context.user_data.get("training_level_prompt", "")

    history = context.user_data.get("dialog_history", [])[-20:]
    model_input = ("ИСТОРИЯ ТЕКУЩЕГО ДИАЛОГА:\n" + "\n".join(history) + "\n\nТЕКУЩАЯ РЕПЛИКА/ИНСТРУКЦИЯ:\n" + ai_input) if history else ai_input

    response = client.responses.create(
        model="gpt-5.6",
        instructions=final_instructions,
        input=model_input,
        tools=[{"type": "web_search", "filters": {"allowed_domains": ["greenleaf-global.com", "global.green-leaf.shop", "prais-catalog.famall-obs.ru"]}}],
    )
    answer = polish_answer(response.output_text, user_text)
    context.user_data["dialog_history"].extend(["Пользователь: " + user_text, "Лия: " + answer])
    context.user_data["dialog_history"] = context.user_data["dialog_history"][-20:]
    if context.user_data.get("mode") == "💬 Тренировка диалога":
        context.user_data["training_history"].append("Лия: " + answer)
    await update.message.reply_text(answer, reply_markup=MAIN_KEYBOARD)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Liya bot is running")
    def log_message(self, format, *args):
        return


def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()


def main():
    threading.Thread(target=run_health_server, daemon=True).start()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling()


if __name__ == "__main__":
    main()
