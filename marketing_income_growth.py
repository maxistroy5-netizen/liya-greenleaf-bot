"""Lesson 8: how income grows together with the Greenleaf structure."""
import os
from telegram import ReplyKeyboardMarkup
from telegram.ext import ApplicationHandlerStop
import usercustomize as uc

_original_router = uc.marketing_lesson_router
INCOME_GROWTH_IMAGE = "marketing_lesson_08.png"
LESSON_MENU = ReplyKeyboardMarkup([
    ["📝 Проверить восьмой блок"],
    ["💬 Задать вопрос по маркетинг-плану"],
    ["⬅️ Главное меню"],
], resize_keyboard=True, is_persistent=True)

async def income_growth_router(update, context):
    message = getattr(update, "message", None)
    if not message or not message.text:
        return await _original_router(update, context)

    text = message.text.strip()
    stage = context.user_data.get("marketing_lesson_stage")

    if text == "➡️ Следующий блок" and stage == "linear_marketing_07_done":
        image_path = os.path.join(os.path.dirname(__file__), INCOME_GROWTH_IMAGE)
        if not os.path.exists(image_path):
            await message.reply_text(
                "Слайд «Как растёт твой доход вместе со структурой» пока не найден на сервере. После загрузки изображения нажми «➡️ Следующий блок» ещё раз.",
                reply_markup=uc.NEXT_BLOCK_MENU,
            )
            raise ApplicationHandlerStop
        context.user_data["marketing_lesson_stage"] = "income_growth_08"
        context.user_data.pop("marketing_quiz_step", None)
        with open(image_path, "rb") as image:
            await message.reply_photo(photo=image, caption=(
                "🎓 УРОК 8 | КАК РАСТЁТ ТВОЙ ДОХОД ВМЕСТЕ СО СТРУКТУРОЙ\n\n"
                "Теперь соединяем изученные элементы маркетинг-плана в общую систему.\n\n"
                "По мере развития структуры могут подключаться разные виды вознаграждений: бонус наставника, бонус глубины, бонус ширины, линейный маркетинг и другие бонусы — при выполнении соответствующих условий маркетинг-плана.\n\n"
                "Важно: рост структуры сам по себе не является гарантией дохода. Выплаты зависят от фактического товарооборота и выполнения условий конкретных бонусов.\n\n"
                "Когда всё рассмотрела — нажми «📝 Проверить восьмой блок»."
            ))
        await message.reply_text(
            "Здесь мы уже смотрим на маркетинг-план целиком 💚 Не отдельный бонус, а связь между развитием структуры и доступными видами вознаграждений.",
            reply_markup=LESSON_MENU,
        )
        raise ApplicationHandlerStop

    if text == "📝 Проверить восьмой блок" and stage == "income_growth_08":
        context.user_data["marketing_lesson_stage"] = "quiz_income_growth_08"
        context.user_data["marketing_quiz_step"] = 1
        await message.reply_text(
            "💬 ПРОВЕРИМ ПОНИМАНИЕ — 1/3\n\nКакие бонусы начинают работать, когда ты лично приглашаешь новых партнёров?\n\nA — Бонус наставника\nB — Только линейный маркетинг\nC — Только бонус ширины",
            reply_markup=uc.CHECK_MENU,
        )
        raise ApplicationHandlerStop

    if stage == "quiz_income_growth_08" and text.upper() in {"A", "B", "C", "А", "Б", "В"}:
        normalized = {"А": "A", "Б": "B", "В": "C"}.get(text.upper(), text.upper())
        step = context.user_data.get("marketing_quiz_step", 1)
        correct = {1: "A", 2: "B", 3: "C"}[step]
        if normalized != correct:
            hints = {
                1: "Не совсем 💚 Личное приглашение партнёра со стартовым набором связано с бонусом наставника.",
                2: "Не совсем 💚 Когда формируются левая и правая группы, в общей системе начинают работать механики глубины и ширины — при выполнении их условий.",
                3: "Не совсем 💚 В долгосрочной перспективе важны развитие активной структуры, товарооборот и выполнение условий маркетинг-плана.",
            }
            await message.reply_text(hints[step] + " Попробуй ещё раз.", reply_markup=uc.CHECK_MENU)
            raise ApplicationHandlerStop

        if step == 1:
            context.user_data["marketing_quiz_step"] = 2
            await message.reply_text(
                "Верно! 💚\n\n💬 ПРОВЕРИМ ПОНИМАНИЕ — 2/3\n\nЧто подключается по мере формирования и развития левой и правой групп?\n\nA — Только личные покупки\nB — Механики бонусов глубины и ширины при выполнении их условий\nC — Никакие новые бонусы",
                reply_markup=uc.CHECK_MENU,
            )
            raise ApplicationHandlerStop

        if step == 2:
            context.user_data["marketing_quiz_step"] = 3
            await message.reply_text(
                "Верно! 💚\n\n💬 ПРОВЕРИМ ПОНИМАНИЕ — 3/3\n\nОт чего зависит рост дохода в долгосрочной перспективе?\n\nA — Только от количества зарегистрированных людей\nB — От одного выбранного бонуса\nC — От развития активной структуры, товарооборота и выполнения условий маркетинг-плана",
                reply_markup=uc.CHECK_MENU,
            )
            raise ApplicationHandlerStop

        context.user_data["marketing_lesson_stage"] = "income_growth_08_done"
        context.user_data.pop("marketing_quiz_step", None)
        await message.reply_text(
            "Отлично! 💚 Восьмой блок пройден.\n\nТеперь ты видишь маркетинг-план не как набор отдельных выплат, а как систему: личные действия → развитие двух групп → рост структуры → товарооборот → доступные бонусы при выполнении их условий.\n\nСледующим шагом разберём следующий элемент маркетинг-плана 👇",
            reply_markup=uc.NEXT_BLOCK_MENU,
        )
        raise ApplicationHandlerStop

    return await _original_router(update, context)

uc.marketing_lesson_router = income_growth_router
print("GREENLEAF income growth lesson loaded", flush=True)
