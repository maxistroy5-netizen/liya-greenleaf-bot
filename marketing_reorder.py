"""Reorder Greenleaf marketing lessons: bonuses first, linear marketing later."""
import os
from telegram import ReplyKeyboardMarkup
from telegram.ext import ApplicationHandlerStop
import usercustomize as uc

_original_router = uc.marketing_lesson_router

LESSON_IMAGE_06 = "marketing_lesson_06.png.png.png"
LESSON_05_WIDTH_MENU = ReplyKeyboardMarkup([["📝 Проверить пятый блок"],["💬 Задать вопрос по маркетинг-плану"],["⬅️ Главное меню"]], resize_keyboard=True, is_persistent=True)

async def reordered_marketing_lesson_router(update, context):
    message = getattr(update, "message", None)
    if not message or not message.text:
        return await _original_router(update, context)

    text = message.text.strip()
    stage = context.user_data.get("marketing_lesson_stage")

    if text == "➡️ Следующий блок" and stage == "lesson_02_done":
        image_path = os.path.join(os.path.dirname(__file__), uc.LESSON_IMAGE_04)
        if not os.path.exists(image_path):
            await message.reply_text("Третий учебный блок пока не найден на сервере. Попробуй ещё раз после обновления.", reply_markup=uc.NEXT_BLOCK_MENU)
            raise ApplicationHandlerStop
        context.user_data["marketing_lesson_stage"] = "bonus_depth_03"
        context.user_data.pop("marketing_quiz_step", None)
        with open(image_path, "rb") as image:
            await message.reply_photo(photo=image, caption="🎓 УРОК 3 | БОНУС ГЛУБИНЫ\n\nТеперь подробно разбираем первый из трёх бонусов — бонус глубины: когда он возникает и как рассчитывается.\n\nЗа новую бинарную глубину предусмотрена фиксированная сумма 88 $. На слайде показан пример расчёта: 88 $ × 70 ₽ × 0,95 = 5 852 ₽.\n\nКогда всё рассмотрела — нажми «📝 Проверить третий блок».")
        await message.reply_text("Посмотри внимательно 💚 Главное здесь — понять, что считается новой бинарной глубиной и когда возникает право на этот бонус.", reply_markup=uc.LESSON_03_MENU)
        raise ApplicationHandlerStop

    if text == "📝 Проверить третий блок" and stage == "bonus_depth_03":
        context.user_data["marketing_lesson_stage"] = "quiz_depth_03"
        context.user_data["marketing_quiz_step"] = 1
        await message.reply_text("💬 ПРОВЕРИМ ПОНИМАНИЕ — 1/3\n\nКогда ты получаешь бонус глубины?\n\nA — Когда лично приглашаешь одного нового партнёра\nB — Когда в структуре появляется новый партнёр и в левой, и в правой группе — новая бинарная глубина\nC — Только при личной покупке продукции", reply_markup=uc.CHECK_MENU)
        raise ApplicationHandlerStop

    if stage == "quiz_depth_03" and text.upper() in {"A","B","C","А","Б","В"}:
        normalized = {"А":"A","Б":"B","В":"C"}.get(text.upper(), text.upper())
        step = context.user_data.get("marketing_quiz_step", 1)
        correct = {1:"B",2:"B",3:"C"}[step]
        if normalized != correct:
            hints = {1:"Не совсем 💚 Бонус глубины возникает при появлении новой бинарной глубины — по новому партнёру в левой и правой группе. Попробуй ещё раз.",2:"Не совсем 💚 На слайде указана фиксированная сумма 88 $ за новую бинарную глубину. Попробуй ещё раз.",3:"Не совсем 💚 Для новой бинарной глубины нужен новый партнёр и в левой, и в правой группе. Попробуй ещё раз."}
            await message.reply_text(hints[step], reply_markup=uc.CHECK_MENU)
            raise ApplicationHandlerStop
        if step == 1:
            context.user_data["marketing_quiz_step"] = 2
            await message.reply_text("Верно! 💚\n\n💬 ПРОВЕРИМ ПОНИМАНИЕ — 2/3\n\nКакая фиксированная сумма указана за новую бинарную глубину?\n\nA — 70 $\nB — 88 $\nC — 95 $", reply_markup=uc.CHECK_MENU)
            raise ApplicationHandlerStop
        if step == 2:
            context.user_data["marketing_quiz_step"] = 3
            await message.reply_text("Верно! 💚\n\n💬 ПРОВЕРИМ ПОНИМАНИЕ — 3/3\n\nЧто должно произойти для образования новой бинарной глубины?\n\nA — Новый партнёр только в левой группе\nB — Новый партнёр только в правой группе\nC — Новый партнёр и в левой, и в правой группе", reply_markup=uc.CHECK_MENU)
            raise ApplicationHandlerStop
        context.user_data["marketing_lesson_stage"] = "bonus_depth_03_done"
        context.user_data.pop("marketing_quiz_step", None)
        await message.reply_text("Отлично! 💚 Бонус глубины разобрали.\n\nТеперь переходим ко второму бонусу — бонусу наставника 👇", reply_markup=uc.NEXT_BLOCK_MENU)
        raise ApplicationHandlerStop

    if text == "➡️ Следующий блок" and stage == "bonus_depth_03_done":
        image_path = os.path.join(os.path.dirname(__file__), uc.LESSON_IMAGE_05)
        if not os.path.exists(image_path):
            await message.reply_text("Четвёртый учебный блок пока не найден на сервере. Попробуй ещё раз после обновления.", reply_markup=uc.NEXT_BLOCK_MENU)
            raise ApplicationHandlerStop
        context.user_data["marketing_lesson_stage"] = "bonus_mentor_04"
        context.user_data.pop("marketing_quiz_step", None)
        with open(image_path, "rb") as image:
            await message.reply_photo(photo=image, caption="🎓 УРОК 4 | БОНУС НАСТАВНИКА\n\nТеперь подробно разбираем бонус наставника. Ты получаешь его за лично приглашённого нового партнёра, который приобретает стартовый набор.\n\nНа слайде показан пример: 275 PV × 5% × 70 ₽ × 0,95 = 914 ₽.\n\nКогда всё рассмотрела — нажми «📝 Проверить четвёртый блок».")
        await message.reply_text("Обрати внимание 💚 Здесь ключевое условие — партнёра пригласила лично ты, и он приобрёл стартовый набор.", reply_markup=uc.LESSON_04_MENU)
        raise ApplicationHandlerStop

    if text == "📝 Проверить четвёртый блок" and stage == "bonus_mentor_04":
        context.user_data["marketing_lesson_stage"] = "quiz_mentor_04"
        context.user_data["marketing_quiz_step"] = 1
        await message.reply_text("💬 ПРОВЕРИМ ПОНИМАНИЕ — 1/3\n\nЗа что начисляется бонус наставника?\n\nA — За лично приглашённого партнёра, который приобрёл стартовый набор\nB — За товарооборот меньшей группы\nC — За любую личную покупку", reply_markup=uc.CHECK_MENU)
        raise ApplicationHandlerStop

    if stage == "quiz_mentor_04" and text.upper() in {"A","B","C","А","Б","В"}:
        normalized = {"А":"A","Б":"B","В":"C"}.get(text.upper(), text.upper())
        step = context.user_data.get("marketing_quiz_step", 1)
        correct = {1:"A",2:"B",3:"C"}[step]
        if normalized != correct:
            hints = {1:"Не совсем 💚 Бонус наставника начисляется за лично приглашённого партнёра, который приобрёл стартовый набор.",2:"Не совсем 💚 В примере на слайде указан бонус наставника 5%.",3:"Не совсем 💚 В примере на слайде расчёт даёт 914 ₽."}
            await message.reply_text(hints[step] + " Попробуй ещё раз.", reply_markup=uc.CHECK_MENU)
            raise ApplicationHandlerStop
        if step == 1:
            context.user_data["marketing_quiz_step"] = 2
            await message.reply_text("Верно! 💚\n\n💬 ПРОВЕРИМ ПОНИМАНИЕ — 2/3\n\nКакой процент бонуса наставника указан в примере на слайде?\n\nA — 3%\nB — 5%\nC — 10%", reply_markup=uc.CHECK_MENU)
            raise ApplicationHandlerStop
        if step == 2:
            context.user_data["marketing_quiz_step"] = 3
            await message.reply_text("Верно! 💚\n\n💬 ПРОВЕРИМ ПОНИМАНИЕ — 3/3\n\nКакой результат показан в примере 275 PV × 5% × 70 ₽ × 0,95?\n\nA — 585 ₽\nB — 1 828 ₽\nC — 914 ₽", reply_markup=uc.CHECK_MENU)
            raise ApplicationHandlerStop
        context.user_data["marketing_lesson_stage"] = "bonus_mentor_04_done"
        context.user_data.pop("marketing_quiz_step", None)
        await message.reply_text("Супер! 💚 Бонус наставника разобрали.\n\nТеперь переходим к третьему бонусу — бонусу ширины 👇", reply_markup=uc.NEXT_BLOCK_MENU)
        raise ApplicationHandlerStop

    if text == "➡️ Следующий блок" and stage == "bonus_mentor_04_done":
        image_path = os.path.join(os.path.dirname(__file__), LESSON_IMAGE_06)
        if not os.path.exists(image_path):
            await message.reply_text("Пятый учебный блок пока не найден на сервере. Попробуй ещё раз после обновления.", reply_markup=uc.NEXT_BLOCK_MENU)
            raise ApplicationHandlerStop
        context.user_data["marketing_lesson_stage"] = "bonus_width_05"
        context.user_data.pop("marketing_quiz_step", None)
        with open(image_path, "rb") as image:
            await message.reply_photo(photo=image, caption="🎓 УРОК 5 | БОНУС ШИРИНЫ\n\nТеперь подробно разбираем бонус ширины. Он рассчитывается от товарооборота меньшей группы по стартовым наборам.\n\nПроцент зависит от твоего пакета: Платина — 10%, Бриллиант — 12%, Корона — 15%.\n\nНа слайде показан пример для Платины: 275 PV × 10% × 70 ₽ × 0,95 = 1 828 ₽.\n\nКогда всё рассмотрела — нажми «📝 Проверить пятый блок».")
        await message.reply_text("Обрати внимание 💚 Здесь важно запомнить две вещи: в расчёт берётся меньшая группа, а процент бонуса зависит от стартового пакета.", reply_markup=LESSON_05_WIDTH_MENU)
        raise ApplicationHandlerStop

    if text == "📝 Проверить пятый блок" and stage == "bonus_width_05":
        context.user_data["marketing_lesson_stage"] = "quiz_width_05"
        context.user_data["marketing_quiz_step"] = 1
        await message.reply_text("💬 ПРОВЕРИМ ПОНИМАНИЕ — 1/3\n\nОт товарооборота какой группы рассчитывается бонус ширины?\n\nA — Большей группы\nB — Меньшей группы\nC — Только от личного товарооборота", reply_markup=uc.CHECK_MENU)
        raise ApplicationHandlerStop

    if stage == "quiz_width_05" and text.upper() in {"A","B","C","А","Б","В"}:
        normalized = {"А":"A","Б":"B","В":"C"}.get(text.upper(), text.upper())
        step = context.user_data.get("marketing_quiz_step", 1)
        correct = {1:"B",2:"B",3:"C"}[step]
        if normalized != correct:
            hints = {1:"Не совсем 💚 Бонус ширины рассчитывается от товарооборота меньшей группы по стартовым наборам.",2:"Не совсем 💚 Для пакета Бриллиант на слайде указан бонус ширины 12%.",3:"Не совсем 💚 В примере для Платины расчёт даёт 1 828 ₽."}
            await message.reply_text(hints[step] + " Попробуй ещё раз.", reply_markup=uc.CHECK_MENU)
            raise ApplicationHandlerStop
        if step == 1:
            context.user_data["marketing_quiz_step"] = 2
            await message.reply_text("Верно! 💚\n\n💬 ПРОВЕРИМ ПОНИМАНИЕ — 2/3\n\nКакой процент бонуса ширины указан для пакета Бриллиант — 825 PV?\n\nA — 10%\nB — 12%\nC — 15%", reply_markup=uc.CHECK_MENU)
            raise ApplicationHandlerStop
        if step == 2:
            context.user_data["marketing_quiz_step"] = 3
            await message.reply_text("Верно! 💚\n\n💬 ПРОВЕРИМ ПОНИМАНИЕ — 3/3\n\nКакой результат показан в примере для Платины: 275 PV × 10% × 70 ₽ × 0,95?\n\nA — 914 ₽\nB — 5 852 ₽\nC — 1 828 ₽", reply_markup=uc.CHECK_MENU)
            raise ApplicationHandlerStop
        context.user_data["marketing_lesson_stage"] = "bonus_width_05_done"
        context.user_data.pop("marketing_quiz_step", None)
        await message.reply_text("Отлично! 💚 Бонус ширины разобрали.\n\nТеперь у тебя отдельно пройдены три первых бонуса:\n• бонус глубины;\n• бонус наставника;\n• бонус ширины.\n\nСледующим блоком подключим линейный маркетинг 👇", reply_markup=uc.NEXT_BLOCK_MENU)
        raise ApplicationHandlerStop

    return await _original_router(update, context)

uc.marketing_lesson_router = reordered_marketing_lesson_router
print("GREENLEAF marketing lesson reorder loaded: depth -> mentor -> width -> linear later", flush=True)
