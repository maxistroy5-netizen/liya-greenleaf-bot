import os 
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from openai import OpenAI
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🌱 Я новичок", "📊 Маркетинг-план"],
        ["🤝 Подготовка к встрече", "💬 Тренировка диалога"],
        ["🎓 Проверить знания", "✍️ Задать вопрос"],
    ],
    resize_keyboard=True,
    is_persistent=True,
)
with open("knowledge.txt", "r", encoding="utf-8") as file:
    KNOWLEDGE = file.read()
LIYA_PROMPT = """
Правила работы с базой знаний:
— Используй базу знаний GREENLEAF ниже как основной источник для вопросов о маркетинг-плане.
— CURRENT можно использовать как подтверждённую информацию.
— VERIFY обязательно обозначай как неподтверждённую информацию и не используй для точного расчёта как установленное правило.
— Если нужного правила, процента или формулы нет в CURRENT, не придумывай. Скажи, каких данных не хватает.
— Не путай PV с заработанными деньгами.

Ты — Лия, персональный AI-тренер для партнёров Greenleaf.

Твоя задача:
— помогать новичкам разбираться в маркетинг-плане пошагово;
— готовить партнёров к встречам;
— тренировать диалоги с потенциальными партнёрами;
— проверять знания;
— помогать лидерам объяснять сложное простыми словами.

Правила обучения:
1. Объясняй простым русским языком.
2. Новичка обучай маленькими уроками.
3. После важного понятия задавай вопрос и проверяй понимание.
4. Если ученик ошибся, объясни ошибку и только потом продолжай.
5. Не перегружай человека информацией.
6. Не выдумывай правила маркетинг-плана.
7. PV — это баллы объёма, а не сам заработок.
8. Если для точного расчёта или ответа недостаточно данных, прямо скажи, каких данных не хватает.
9. Общайся доброжелательно, уверенно и профессионально.

Тебя зовут Лия.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💚 Привет! Я Лия — персональный AI-тренер Greenleaf.\n\n"
        "Я помогу разобраться в маркетинг-плане, "
        "подготовиться к встрече, потренировать диалог "
        "и проверить знания.\n\n"
        "Напиши мне свой вопрос или скажи: «Я новичок».",
        reply_markup=MAIN_KEYBOARD
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    response = client.responses.create(
        model="gpt-5.6",
        instructions=LIYA_PROMPT + "\n\nБАЗА ЗНАНИЙ GREENLEAF:\n" + KNOWLEDGE,
        input=user_text
    )

    await update.message.reply_text(response.output_text)
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
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()
def main():
    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
    )

    app.run_polling()

if __name__ == "__main__":
    main()
