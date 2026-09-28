"""Connect Width Bonus without guessing a user's progress after a Render restart.

Important: context.user_data is in-memory in the current bot setup. If Render restarts,
the stage can be None while Telegram still shows an old persistent keyboard. We must
not interpret that as permission to send lesson 5 again, because that rewinds users
who have already completed later lessons.
"""
import os
from telegram import ReplyKeyboardMarkup
from telegram.ext import ApplicationHandlerStop
import usercustomize as uc

_original_router = uc.marketing_lesson_router
WIDTH_IMAGE = "marketing_lesson_06.png.png.png"
WIDTH_MENU = ReplyKeyboardMarkup([["📝 Проверить пятый блок"],["💬 Задать вопрос по маркетинг-плану"],["⬅️ Главное меню"]], resize_keyboard=True, is_persistent=True)

async def width_recovery_router(update, context):
    message = getattr(update, "message", None)
    if not message or not message.text:
        return await _original_router(update, context)
    text = message.text.strip()
    stage = context.user_data.get("marketing_lesson_stage")

    # Only advance to Width Bonus from a stage that explicitly precedes it.
    # Never use stage=None as a fallback: after a Render restart that would
    # incorrectly rewind users who had already reached lessons 6, 7 or 8.
    if text == "➡️ Следующий блок" and stage in {"lesson_05_done", "bonus_mentor_04_done"}:
        image_path = os.path.join(os.path.dirname(__file__), WIDTH_IMAGE)
        if not os.path.exists(image_path):
            await message.reply_text("Слайд «Бонус ширины» пока не найден на сервере.", reply_markup=uc.NEXT_BLOCK_MENU)
            raise ApplicationHandlerStop
        context.user_data["marketing_lesson_stage"] = "bonus_width_05"
        context.user_data.pop("marketing_quiz_step", None)
        with open(image_path, "rb") as image:
            await message.reply_photo(photo=image, caption=(
                "🎓 УРОК 5 | БОНУС ШИРИНЫ\n\n"
                "Теперь подробно разбираем бонус ширины. Он рассчитывается от товарооборота меньшей группы по стартовым наборам.\n\n"
                "Процент зависит от твоего пакета: Платина — 10%, Бриллиант — 12%, Корона — 15%.\n\n"
                "На слайде показан пример для Платины: 275 PV × 10% × 70 ₽ × 0,95 = 1 828 ₽.\n\n"
                "Когда всё рассмотрела — нажми «📝 Проверить пятый блок»."
            ))
        await message.reply_text("Обрати внимание 💚 В расчёт берётся меньшая группа, а процент бонуса зависит от стартового пакета.", reply_markup=WIDTH_MENU)
        raise ApplicationHandlerStop

    return await _original_router(update, context)

uc.marketing_lesson_router = width_recovery_router
print("GREENLEAF width bonus connector loaded", flush=True)
