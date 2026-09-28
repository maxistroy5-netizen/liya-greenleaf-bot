"""Direct lesson navigation for Liya marketing-plan training.
Lets returning learners open any existing lesson without replaying earlier lessons.
"""
from telegram import ReplyKeyboardMarkup
from telegram.ext import ApplicationHandlerStop
import usercustomize as uc

_original_router = uc.marketing_lesson_router

LESSONS_MENU = ReplyKeyboardMarkup([
    ["1️⃣ Урок 1", "2️⃣ Урок 2"],
    ["3️⃣ Урок 3", "4️⃣ Урок 4"],
    ["5️⃣ Урок 5", "6️⃣ Урок 6"],
    ["7️⃣ Урок 7", "8️⃣ Урок 8"],
    ["🎓 Начать обучение с нуля"],
    ["💬 Задать вопрос по маркетинг-плану"],
    ["⬅️ Главное меню"],
], resize_keyboard=True, is_persistent=True)

MARKETING_ENTRY_MENU = ReplyKeyboardMarkup([
    ["📚 Выбрать урок"],
    ["🎓 Начать обучение с нуля"],
    ["💬 Задать вопрос по маркетинг-плану"],
    ["⬅️ Главное меню"],
], resize_keyboard=True, is_persistent=True)

LESSON_TARGETS = {
    "1️⃣ Урок 1": ("🎓 Начать обучение с нуля", None),
    "2️⃣ Урок 2": ("➡️ Урок 2 — Первые бонусы", None),
    # Lessons 3–8 are entered through the same tested Next-block chain.
    # We set the exact completed stage immediately before each target lesson.
    "3️⃣ Урок 3": ("➡️ Следующий блок", "lesson_02_done"),
    "4️⃣ Урок 4": ("➡️ Следующий блок", "depth_bonus_03_done"),
    "5️⃣ Урок 5": ("➡️ Следующий блок", "mentor_bonus_04_done"),
    "6️⃣ Урок 6": ("➡️ Следующий блок", "width_bonus_05_done"),
    "7️⃣ Урок 7": ("➡️ Следующий блок", "three_bonuses_06_done"),
    "8️⃣ Урок 8": ("➡️ Следующий блок", "linear_marketing_07_done"),
}

async def lesson_navigation_router(update, context):
    message = getattr(update, "message", None)
    if not message or not message.text:
        return await _original_router(update, context)

    text = message.text.strip()

    if text == "📊 Маркетинг-план":
        context.user_data.pop("marketing_lesson_stage", None)
        context.user_data.pop("marketing_quiz_step", None)
        await message.reply_text(
            "📊 МАРКЕТИНГ-ПЛАН GREENLEAF\n\n"
            "Если ты здесь впервые — начинай обучение с нуля.\n\n"
            "Если уже проходила уроки или хочешь повторить конкретную тему — нажми «📚 Выбрать урок». "
            "Не нужно каждый раз начинать сначала 💚",
            reply_markup=MARKETING_ENTRY_MENU,
        )
        raise ApplicationHandlerStop

    if text == "📚 Выбрать урок":
        await message.reply_text(
            "📚 ВЫБЕРИ НУЖНЫЙ УРОК\n\n"
            "Можно открыть любой из уже подключённых уроков и продолжить обучение с нужного места 👇",
            reply_markup=LESSONS_MENU,
        )
        raise ApplicationHandlerStop

    if text in LESSON_TARGETS:
        routed_text, prerequisite_stage = LESSON_TARGETS[text]
        context.user_data.pop("marketing_quiz_step", None)
        if prerequisite_stage is not None:
            context.user_data["marketing_lesson_stage"] = prerequisite_stage
        # Reuse the already-tested lesson handlers instead of duplicating lesson logic.
        original_text = message.text
        try:
            message.text = routed_text
            return await _original_router(update, context)
        finally:
            message.text = original_text

    return await _original_router(update, context)

uc.marketing_lesson_router = lesson_navigation_router
print("GREENLEAF direct lesson navigation loaded", flush=True)
