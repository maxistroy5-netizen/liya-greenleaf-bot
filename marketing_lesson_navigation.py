"""Direct lesson navigation for Liya marketing-plan training.
Opens any of the eight lessons directly and keeps the existing quiz logic.
"""
import os
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

LESSON_MENUS = {
    1: uc.LESSON_MENU,
    2: uc.LESSON_02_MENU,
    3: uc.LESSON_03_MENU,
    4: uc.LESSON_04_MENU,
    5: ReplyKeyboardMarkup([["📝 Проверить пятый блок"],["💬 Задать вопрос по маркетинг-плану"],["⬅️ Главное меню"]], resize_keyboard=True, is_persistent=True),
    6: ReplyKeyboardMarkup([["📝 Проверить шестой блок"],["💬 Задать вопрос по маркетинг-плану"],["⬅️ Главное меню"]], resize_keyboard=True, is_persistent=True),
    7: ReplyKeyboardMarkup([["📝 Проверить седьмой блок"],["💬 Задать вопрос по маркетинг-плану"],["⬅️ Главное меню"]], resize_keyboard=True, is_persistent=True),
    8: ReplyKeyboardMarkup([["📝 Проверить восьмой блок"],["💬 Задать вопрос по маркетинг-плану"],["⬅️ Главное меню"]], resize_keyboard=True, is_persistent=True),
}

LESSONS = {
    1: {
        "image": "marketing_lesson_01.png.png", "stage": "lesson_01",
        "caption": "🎓 УРОК 1 | ОСНОВА МАРКЕТИНГ-ПЛАНА\n\nПосмотри первый блок: как устроен маркетинг-план, что такое PV и как формируются левая и правая группы.\n\nКогда будешь готова — нажми «📝 Проверить первый блок».",
        "note": "Я рядом 💚 Можно увеличить изображение и спокойно всё рассмотреть."
    },
    2: {
        "image": "marketing_lesson_02.png.png", "stage": "lesson_02",
        "caption": "🎓 УРОК 2 | ПЕРВЫЕ БОНУСЫ\n\nЗдесь разбираем три базовых вида бонусов: бонус наставника, бонус глубины и бинарный бонус (бонус ширины).\n\nВнимательно посмотри слайд. Когда будешь готова — нажми «📝 Проверить второй блок».",
        "note": "Не спеши 💚 Сначала разберись, за какое действие начисляется каждый из трёх бонусов."
    },
    3: {
        "image": "marketing_lesson_04.png.png", "stage": "bonus_depth_03",
        "caption": "🎓 УРОК 3 | БОНУС ГЛУБИНЫ\n\nТеперь подробно разбираем первый из трёх бонусов — бонус глубины: когда он возникает и как рассчитывается.\n\nЗа новую бинарную глубину предусмотрена фиксированная сумма 88 $. На слайде показан пример расчёта: 88 $ × 70 ₽ × 0,95 = 5 852 ₽.\n\nКогда всё рассмотрела — нажми «📝 Проверить третий блок».",
        "note": "Посмотри внимательно 💚 Главное здесь — понять, что считается новой бинарной глубиной и когда возникает право на этот бонус."
    },
    4: {
        "image": "marketing_lesson_05.png.png", "stage": "bonus_mentor_04",
        "caption": "🎓 УРОК 4 | БОНУС НАСТАВНИКА\n\nТеперь подробно разбираем бонус наставника. Ты получаешь его за лично приглашённого нового партнёра, который приобретает стартовый набор.\n\nНа слайде показан пример: 275 PV × 5% × 70 ₽ × 0,95 = 914 ₽.\n\nКогда всё рассмотрела — нажми «📝 Проверить четвёртый блок».",
        "note": "Обрати внимание 💚 Здесь ключевое условие — партнёра пригласила лично ты, и он приобрёл стартовый набор."
    },
    5: {
        "image": "marketing_lesson_06.png.png.png", "stage": "bonus_width_05",
        "caption": "🎓 УРОК 5 | БОНУС ШИРИНЫ\n\nТеперь подробно разбираем бонус ширины. Он рассчитывается от товарооборота меньшей группы по стартовым наборам.\n\nПроцент зависит от твоего пакета: Платина — 10%, Бриллиант — 12%, Корона — 15%.\n\nНа слайде показан пример для Платины: 275 PV × 10% × 70 ₽ × 0,95 = 1 828 ₽.\n\nКогда всё рассмотрела — нажми «📝 Проверить пятый блок».",
        "note": "Обрати внимание 💚 В расчёт берётся меньшая группа по стартовым наборам, а процент зависит от стартового пакета."
    },
    6: {
        "image": "marketing_lesson_07.png.png.png", "stage": "three_bonuses_06",
        "caption": "🎓 УРОК 6 | ТРИ БОНУСА ВМЕСТЕ\n\nТеперь собираем три уже изученных бонуса в одну понятную картину.\n\nВ учебном примере: бонус наставника — 1 828 ₽, бонус глубины — 5 852 ₽, бонус ширины — 1 828 ₽. Общий результат примера — 9 508 ₽.\n\nЭто учебный пример из маркетинг-плана, а не обещание дохода. Фактические выплаты зависят от выполнения условий маркетинг-плана.\n\nКогда всё рассмотрела — нажми «📝 Проверить шестой блок».",
        "note": "Здесь главное увидеть связь 💚 Разные бонусы работают только при выполнении условий каждого из них."
    },
    7: {
        "image": "marketing_lesson_03.png.png", "stage": "linear_marketing_07",
        "caption": "🎓 УРОК 7 | ЛИНЕЙНЫЙ МАРКЕТИНГ\n\nПосле трёх первых бонусов переходим к следующей части маркетинг-плана — линейному маркетингу до 50 уровней глубины.\n\nНа слайде: 1–5 уровни — 4%, 6–10 — 3%, 11–30 — 1%, 31–50 — 0,5%.\n\nКогда всё рассмотрела — нажми «📝 Проверить седьмой блок».",
        "note": "Теперь расширяем картину 💚 Смотри, как вознаграждение распределяется по уровням структуры."
    },
    8: {
        "image": "marketing_lesson_08.png.png", "stage": "income_growth_08",
        "caption": "🎓 УРОК 8 | КАК РАСТЁТ ТВОЙ ДОХОД ВМЕСТЕ СО СТРУКТУРОЙ\n\nТеперь соединяем изученные элементы маркетинг-плана в общую систему.\n\nПо мере развития структуры могут подключаться разные виды вознаграждений: бонус наставника, бонус глубины, бонус ширины, линейный маркетинг и другие бонусы — при выполнении соответствующих условий маркетинг-плана.\n\nВажно: рост структуры сам по себе не является гарантией дохода. Выплаты зависят от фактического товарооборота и выполнения условий конкретных бонусов.\n\nКогда всё рассмотрела — нажми «📝 Проверить восьмой блок».",
        "note": "Здесь мы уже смотрим на маркетинг-план целиком 💚 Не отдельный бонус, а связь между развитием структуры и доступными видами вознаграждений."
    },
}

async def open_lesson(message, context, lesson_number):
    lesson = LESSONS[lesson_number]
    image_path = os.path.join(os.path.dirname(__file__), lesson["image"])
    if not os.path.exists(image_path):
        await message.reply_text(f"Слайд урока {lesson_number} пока не найден на сервере.", reply_markup=LESSONS_MENU)
        raise ApplicationHandlerStop
    context.user_data["marketing_lesson_stage"] = lesson["stage"]
    context.user_data.pop("marketing_quiz_step", None)
    with open(image_path, "rb") as image:
        await message.reply_photo(photo=image, caption=lesson["caption"])
    await message.reply_text(lesson["note"], reply_markup=LESSON_MENUS[lesson_number])
    raise ApplicationHandlerStop

async def lesson_navigation_router(update, context):
    message = getattr(update, "message", None)
    if not message or not message.text:
        return await _original_router(update, context)

    text = message.text.strip()

    if text == "📊 Маркетинг-план":
        context.user_data.pop("marketing_lesson_stage", None)
        context.user_data.pop("marketing_quiz_step", None)
        await message.reply_text(
            "📊 МАРКЕТИНГ-ПЛАН GREENLEAF\n\nЕсли ты здесь впервые — начинай обучение с нуля.\n\nЕсли уже проходила уроки или хочешь повторить конкретную тему — нажми «📚 Выбрать урок». Не нужно каждый раз начинать сначала 💚",
            reply_markup=MARKETING_ENTRY_MENU,
        )
        raise ApplicationHandlerStop

    if text == "📚 Выбрать урок":
        await message.reply_text("📚 ВЫБЕРИ НУЖНЫЙ УРОК\n\nМожно открыть любой урок и продолжить обучение с нужного места 👇", reply_markup=LESSONS_MENU)
        raise ApplicationHandlerStop

    direct = {
        "1️⃣ Урок 1": 1, "2️⃣ Урок 2": 2, "3️⃣ Урок 3": 3, "4️⃣ Урок 4": 4,
        "5️⃣ Урок 5": 5, "6️⃣ Урок 6": 6, "7️⃣ Урок 7": 7, "8️⃣ Урок 8": 8,
    }
    if text in direct:
        return await open_lesson(message, context, direct[text])

    return await _original_router(update, context)

uc.marketing_lesson_router = lesson_navigation_router
print("GREENLEAF direct lesson navigation v2 loaded: all 8 lessons open directly", flush=True)
