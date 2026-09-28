"""Correct lesson 5 to match the uploaded Mentor Bonus slide."""
import os
from telegram.ext import ApplicationHandlerStop
import usercustomize as uc

_original_router = uc.marketing_lesson_router

async def marketing_lesson_router_fixed(update, context):
    message = getattr(update, "message", None)
    if not message or not message.text:
        return await _original_router(update, context)

    text = message.text.strip()
    stage = context.user_data.get("marketing_lesson_stage")

    # Lesson 4 -> Lesson 5: the uploaded 5/7 slide is Mentor Bonus.
    if text == "➡️ Следующий блок" and stage == "lesson_04_done":
        image_path = os.path.join(os.path.dirname(__file__), uc.LESSON_IMAGE_05)
        if not os.path.exists(image_path):
            await message.reply_text(
                "Пятый учебный блок пока не найден на сервере. Попробуй ещё раз после обновления.",
                reply_markup=uc.NEXT_BLOCK_MENU,
            )
            raise ApplicationHandlerStop

        context.user_data["marketing_lesson_stage"] = "lesson_05"
        context.user_data.pop("marketing_quiz_step", None)
        with open(image_path, "rb") as image:
            await message.reply_photo(
                photo=image,
                caption=(
                    "🎓 УРОК 5 | БОНУС НАСТАВНИКА\n\n"
                    "Теперь подробно разбираем бонус наставника. Он начисляется, когда ты лично пригласила нового партнёра, и он приобрёл стартовый набор.\n\n"
                    "На слайде показан пример: 275 PV × 5% × 70 ₽ × 0,95 = 914 ₽.\n\n"
                    "Когда всё рассмотрела — нажми «📝 Проверить пятый блок»."
                ),
            )
        await message.reply_text(
            "Обрати внимание 💚 Главное здесь — личное приглашение партнёра и покупка им стартового набора.",
            reply_markup=uc.LESSON_05_MENU,
        )
        raise ApplicationHandlerStop

    if text == "📝 Проверить пятый блок":
        context.user_data["marketing_lesson_stage"] = "quiz_05_mentor"
        context.user_data["marketing_quiz_step"] = 1
        await message.reply_text(
            "💬 ПРОВЕРИМ ПОНИМАНИЕ — 1/3\n\n"
            "За что начисляется бонус наставника?\n\n"
            "A — За общий объём всей команды\n"
            "B — За лично приглашённого партнёра, который приобрёл стартовый набор\n"
            "C — Только за личную покупку",
            reply_markup=uc.CHECK_MENU,
        )
        raise ApplicationHandlerStop

    if stage == "quiz_05_mentor" and text.upper() in {"A", "B", "C", "А", "Б", "В"}:
        normalized = {"А": "A", "Б": "B", "В": "C"}.get(text.upper(), text.upper())
        step = context.user_data.get("marketing_quiz_step", 1)
        correct = {1: "B", 2: "B", 3: "C"}[step]

        if normalized != correct:
            hints = {
                1: "Не совсем 💚 Бонус наставника связан с лично приглашённым партнёром, который приобрёл стартовый набор. Попробуй ещё раз.",
                2: "Не совсем 💚 На слайде в примере указан бонус наставника 5%. Попробуй ещё раз.",
                3: "Не совсем 💚 В примере на слайде расчёт даёт 914 ₽. Попробуй ещё раз.",
            }
            await message.reply_text(hints[step], reply_markup=uc.CHECK_MENU)
            raise ApplicationHandlerStop

        if step == 1:
            context.user_data["marketing_quiz_step"] = 2
            await message.reply_text(
                "Верно! 💚\n\n💬 ПРОВЕРИМ ПОНИМАНИЕ — 2/3\n\n"
                "Какой процент бонуса наставника указан в примере на слайде?\n\n"
                "A — 4%\nB — 5%\nC — 10%",
                reply_markup=uc.CHECK_MENU,
            )
            raise ApplicationHandlerStop

        if step == 2:
            context.user_data["marketing_quiz_step"] = 3
            await message.reply_text(
                "Верно! 💚\n\n💬 ПРОВЕРИМ ПОНИМАНИЕ — 3/3\n\n"
                "Какой результат показан в примере расчёта 275 PV × 5% × 70 ₽ × 0,95?\n\n"
                "A — 560 ₽\nB — 1 828 ₽\nC — 914 ₽",
                reply_markup=uc.CHECK_MENU,
            )
            raise ApplicationHandlerStop

        context.user_data["marketing_lesson_stage"] = "lesson_05_done"
        context.user_data.pop("marketing_quiz_step", None)
        await message.reply_text(
            "Отлично! 💚 Пятый блок пройден.\n\n"
            "Теперь ты понимаешь:\n"
            "• за что начисляется бонус наставника;\n"
            "• что он связан с лично приглашённым партнёром и стартовым набором;\n"
            "• как выглядит пример расчёта на слайде.\n\n"
            "Готова двигаться дальше? 👇",
            reply_markup=uc.NEXT_BLOCK_MENU,
        )
        raise ApplicationHandlerStop

    return await _original_router(update, context)

uc.marketing_lesson_router = marketing_lesson_router_fixed
print("GREENLEAF lesson 5 mentor bonus fix loaded", flush=True)
