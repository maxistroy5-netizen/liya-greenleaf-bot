import os
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

LIYA_PROMPT = """
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
        "Напиши мне свой вопрос или скажи: «Я новичок»."
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    response = client.responses.create(
        model="gpt-5.6",
        instructions=LIYA_PROMPT,
        input=user_text
    )

    await update.message.reply_text(response.output_text)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
    )

    app.run_polling()

if __name__ == "__main__":
    main()
