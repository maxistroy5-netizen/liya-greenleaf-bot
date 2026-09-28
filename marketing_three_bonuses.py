"""Lesson 6: combine the three first Greenleaf bonuses in one training example."""
import os
from telegram import ReplyKeyboardMarkup
from telegram.ext import ApplicationHandlerStop
import usercustomize as uc

_original_router = uc.marketing_lesson_router
COMBINED_IMAGE = "marketing_lesson_07.png.png"
COMBINED_MENU = ReplyKeyboardMarkup([
    ["📝 Проверить шестой блок"],
    ["💬 Задать вопрос по маркетинг-плану"],
    ["⬅️ Главное меню"],
], resize_keyboard=True, is_persistent=True)

async def three_bonuses_router(update, context):
    message = getattr(update, "message", None)
    if not message or not message.text:
        return await _original_router(update, context)

    text = message.text.strip()
    stage = context.user_data.get("marketing_lesson_stage")

    if text == "➡️ Следующий блок" and stage == "bonus_width_05_done":
        image_path = os.path.join(os.path.dirname(__file__), COMBINED_IMAGE)
        if not os.path.exists(image_path):
            await message.reply_text(
                "Слайд «Три бонуса вместе» пока не найден на сервере. После загрузки изображения нажми «➡️ Следующий блок» ещё раз.",
                reply_markup=uc.NEXT_BLOCK_MENU,
            )
            raise ApplicationHandlerStop
        context.user_data["marketing_lesson_stage"] = "three_bonuses_06"
        context.user_data.pop("marketing_quiz_step", None)
        with open(image_path, "rb") as image:
            await message.reply_photo(photo=image, caption=(
                "🎓 УРОК 6 | ТРИ БОНУСА ВМЕСТЕ\n\n"
                "Теперь собираем три уже изученных бонуса в одну понятную картину.\n\n"
                "В учебном примере: бонус наставника — 1 828 ₽, бонус глубины — 5 852 ₽, бонус ширины — 1 828 ₽. Общий результат примера — 9 508 ₽.\n\n"
                "Это учебный пример из маркетинг-плана, а не обещание дохода. Фактические выплаты зависят от выполнения условий маркетинг-плана.\n\n"
                "Когда всё рассмотрела — нажми «📝 Проверить шестой блок»."
            ))
        await message.reply_text(
            "Здесь главное увидеть связь 💚 Одно развитие структуры может одновременно создать основания для разных видов бонусов — если выполнены условия каждого из них.",
            reply_markup=COMBINED_MENU,
        )
        raise ApplicationHandlerStop

    if text == "📝 Проверить шестой блок" and stage == "three_bonuses_06":
        context.user_data["marketing_lesson_stage"] = "quiz_three_bonuses_06"
        context.user_data["marketing_quiz_step"] = 1
        await message.reply_text(
            "💬 ПРОВЕРИМ ПОНИМАНИЕ — 1/3\n\nЗа какое действие в этом примере начисляется бонус наставника?\n\nA — За лично приглашённого партнёра со стартовым набором\nB — За товарооборот меньшей группы\nC — За новую бинарную глубину",
            reply_markup=uc.CHECK_MENU,
        )
        raise ApplicationHandlerStop

    if stage == "quiz_three_bonuses_06" and text.upper() in {"A","B","C","А","Б","В"}:
        normalized = {"А":"A","Б":"B","В":"C"}.get(text.upper(), text.upper())
        step = context.user_data.get("marketing_quiz_step", 1)
        correct = {1:"A", 2:"B", 3:"C"}[step]
        if normalized != correct:
            hints = {
                1:"Не совсем 💚 Бонус наставника связан с лично приглашённым партнёром, который приобрёл стартовый набор.",
                2:"Не совсем 💚 Бонус глубины в этом примере связан с формированием новой бинарной глубины — по новому партнёру слева и справа.",
                3:"Не совсем 💚 9 508 ₽ в этом учебном примере складываются из бонуса наставника, бонуса глубины и бонуса ширины.",
            }
            await message.reply_text(hints[step] + " Попробуй ещё раз.", reply_markup=uc.CHECK_MENU)
            raise ApplicationHandlerStop
        if step == 1:
            context.user_data["marketing_quiz_step"] = 2
            await message.reply_text(
                "Верно! 💚\n\n💬 ПРОВЕРИМ ПОНИМАНИЕ — 2/3\n\nЗа что в этом примере начисляется бонус глубины?\n\nA — За две личные покупки\nB — За новую бинарную глубину: новый партнёр слева и новый партнёр справа\nC — Только за объём меньшей группы",
                reply_markup=uc.CHECK_MENU,
            )
            raise ApplicationHandlerStop
        if step == 2:
            context.user_data["marketing_quiz_step"] = 3
            await message.reply_text(
                "Верно! 💚\n\n💬 ПРОВЕРИМ ПОНИМАНИЕ — 3/3\n\nИз каких трёх бонусов складывается сумма 9 508 ₽ в этом учебном примере?\n\nA — Только бонус глубины и личные покупки\nB — Бонус наставника и бонус ширины\nC — Бонус наставника + бонус глубины + бонус ширины",
                reply_markup=uc.CHECK_MENU,
            )
            raise ApplicationHandlerStop

        context.user_data["marketing_lesson_stage"] = "three_bonuses_06_done"
        context.user_data.pop("marketing_quiz_step", None)
        await message.reply_text(
            "Отлично! 💚 Шестой блок пройден.\n\nТеперь три первых бонуса сложились в единую картину:\n• бонус наставника;\n• бонус глубины;\n• бонус ширины.\n\nСледующим шагом переходим к линейному маркетингу 👇",
            reply_markup=uc.NEXT_BLOCK_MENU,
        )
        raise ApplicationHandlerStop

    # Move the postponed linear-marketing lesson here, after the three bonus lessons.
    if text == "➡️ Следующий блок" and stage == "three_bonuses_06_done":
        image_path = os.path.join(os.path.dirname(__file__), uc.LESSON_IMAGE_03)
        if not os.path.exists(image_path):
            await message.reply_text("Слайд «Линейный маркетинг» пока не найден на сервере.", reply_markup=uc.NEXT_BLOCK_MENU)
            raise ApplicationHandlerStop
        context.user_data["marketing_lesson_stage"] = "linear_marketing_07"
        context.user_data.pop("marketing_quiz_step", None)
        with open(image_path, "rb") as image:
            await message.reply_photo(photo=image, caption=(
                "🎓 УРОК 7 | ЛИНЕЙНЫЙ МАРКЕТИНГ\n\n"
                "После трёх первых бонусов переходим к следующей части маркетинг-плана — линейному маркетингу до 50 уровней глубины.\n\n"
                "На слайде: 1–5 уровни — 4%, 6–10 — 3%, 11–30 — 1%, 31–50 — 0,5%.\n\n"
                "Когда всё рассмотрела — нажми «📝 Проверить седьмой блок»."
            ))
        linear_menu = ReplyKeyboardMarkup([
            ["📝 Проверить седьмой блок"],
            ["💬 Задать вопрос по маркетинг-плану"],
            ["⬅️ Главное меню"],
        ], resize_keyboard=True, is_persistent=True)
        await message.reply_text("Теперь расширяем картину 💚 Смотри, как вознаграждение распределяется по уровням структуры.", reply_markup=linear_menu)
        raise ApplicationHandlerStop

    if text == "📝 Проверить седьмой блок" and stage == "linear_marketing_07":
        context.user_data["marketing_lesson_stage"] = "quiz_linear_07"
        await message.reply_text(
            "💬 ПРОВЕРИМ ПОНИМАНИЕ\n\nДо какого количества уровней может рассчитываться линейный маркетинг на этом слайде?\n\nA — До 5 уровней\nB — До 10 уровней\nC — До 50 уровней",
            reply_markup=uc.CHECK_MENU,
        )
        raise ApplicationHandlerStop

    if stage == "quiz_linear_07" and text.upper() in {"A","B","C","А","Б","В"}:
        normalized = {"А":"A","Б":"B","В":"C"}.get(text.upper(), text.upper())
        if normalized != "C":
            await message.reply_text("Не совсем 💚 Посмотри на последний диапазон на слайде: линейный маркетинг показан до 50 уровней. Попробуй ещё раз.", reply_markup=uc.CHECK_MENU)
            raise ApplicationHandlerStop
        context.user_data["marketing_lesson_stage"] = "linear_marketing_07_done"
        await message.reply_text("Верно! 💚 Линейный маркетинг на этом слайде показан до 50 уровней глубины. Седьмой блок пройден.", reply_markup=uc.NEXT_BLOCK_MENU)
        raise ApplicationHandlerStop

    return await _original_router(update, context)

uc.marketing_lesson_router = three_bonuses_router
print("GREENLEAF three bonuses lesson loaded", flush=True)
