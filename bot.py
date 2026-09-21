import os
import re
import threading
from datetime import date
from urllib.parse import urlsplit, urlunsplit
from http.server import BaseHTTPRequestHandler, HTTPServer
from openai import OpenAI
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

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
7. ОБЫЧНЫЙ ВОПРОС: дай чистый ответ без URL, без Markdown-ссылок, без технических параметров и без перечня источников. Даже если web_search вернул ссылки, не вставляй их в текст автоматически.
8. ИСТОЧНИК ПО ПРОСЬБЕ: только если пользователь прямо просит «источник», «ссылку», «где посмотреть», «откуда информация» или аналогичное — дай 1–3 наиболее конкретные официальные ссылки. Не дублируй одну ссылку в разных форматах. Никогда не добавляй utm_source, ysclid и другие рекламные/технические параметры.
9. Если пользователь просит источник конкретного факта, сначала коротко назови источник человеческим языком, затем дай прямую чистую ссылку. Не добавляй лишние документы, если один источник уже подтверждает факт.
10. Не используй Markdown со звёздочками (**текст**) и подчёркиваниями. Для акцента используй короткие заголовки, переносы строк и эмодзи.

ОБУЧЕНИЕ:
11. Новичка обучай маленькими уроками; после важного понятия задавай один вопрос и проверяй понимание. При ошибке объясни её и не переходи дальше, пока тема не понята.
12. Всегда учитывай историю текущего диалога. Если ты задала вопрос А/Б/В/Г, короткий ответ «А», «б», «Б)», «в.» трактуй как ответ на последний вопрос. Принимай и текстовый эквивалент варианта.
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
    "🧰 Инструменты": "Коротко сообщи, что здесь готовятся персональные инструменты партнёра: «📱 Создать электронную визитку» и «🤝 3 шага приглашения партнёра». Не утверждай, что генерация уже доступна: модуль подключается."
}

LEVELS = {
    "🟢 Лёгкий": "УРОВЕНЬ ЛЁГКИЙ: доброжелательный собеседник, простой интерес, мягкие возражения.",
    "🟡 Средний": "УРОВЕНЬ СРЕДНИЙ: сомневайся, уточняй; возражения: дорого, нет времени, надо подумать, сомнения к сетевому бизнесу.",
    "🔴 Сложный": "УРОВЕНЬ СЛОЖНЫЙ: опытный требовательный скептик, конкретные неудобные вопросы, проси подтверждать утверждения; не груби."
}

SOURCE_REQUEST_RE = re.compile(r"(?i)\b(источник|источники|ссылк\w*|где\s+(?:это\s+)?посмотреть|откуда\s+(?:ты\s+)?(?:взял\w*|информац\w*)|подтвержден\w*|официальн\w+\s+источник)\b")
URL_RE = re.compile(r"https?://[^\s)\]>]+")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")


def clean_url(url: str) -> str:
    url = url.rstrip(".,;:!?")
    try:
        parts = urlsplit(url)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    except Exception:
        return url.split("?", 1)[0]


def polish_answer(answer: str, user_text: str) -> str:
    wants_source = bool(SOURCE_REQUEST_RE.search(user_text or ""))
    if wants_source:
        answer = MARKDOWN_LINK_RE.sub(lambda m: f"{m.group(1)}: {clean_url(m.group(2))}", answer)
        answer = URL_RE.sub(lambda m: clean_url(m.group(0)), answer)
    else:
        answer = MARKDOWN_LINK_RE.sub(lambda m: m.group(1), answer)
        answer = URL_RE.sub("", answer)
        answer = re.sub(r"\(\s*\)", "", answer)
        answer = re.sub(r"\[\s*\]", "", answer)
    answer = re.sub(r"\*\*([^*]+)\*\*", r"\1", answer)
    answer = re.sub(r"[ \t]+\n", "\n", answer)
    answer = re.sub(r"\n{3,}", "\n\n", answer)
    return answer.strip()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["dialog_history"] = []
    await update.message.reply_text(
        "💚 Привет! Я Лия — персональный AI-тренер Greenleaf.\n\nЯ помогу разобраться в маркетинг-плане, подготовиться к встрече, потренировать диалог, проверить знания и использовать рабочие инструменты.",
        reply_markup=MAIN_KEYBOARD)


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    context.user_data.setdefault("dialog_history", [])
    context.user_data.setdefault("training_history", [])

    if user_text == "⬅️ Главное меню":
        context.user_data.clear()
        context.user_data["dialog_history"] = []
        await update.message.reply_text("Главное меню:", reply_markup=MAIN_KEYBOARD)
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
        ai_input = (MODES.get(active_mode, "Пользователь задаёт вопрос Лии.") + "\n\nНовая реплика пользователя: " + user_text)

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
        tools=[{"type": "web_search", "filters": {"allowed_domains": ["greenleaf-global.com", "global.green-leaf.shop", "prais-catalog.famall-obs.ru"]}}]
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling()


if __name__ == "__main__":
    main()