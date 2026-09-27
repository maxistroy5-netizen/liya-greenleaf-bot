"""Liya marketing-plan visual lesson extension."""
import os
from telegram import ReplyKeyboardMarkup
from telegram.ext import Application, ApplicationHandlerStop, MessageHandler, filters

MARKETING_MENU = ReplyKeyboardMarkup([["🎓 Начать обучение с нуля"],["💬 Задать вопрос по маркетинг-плану"],["⬅️ Главное меню"]], resize_keyboard=True, is_persistent=True)
LESSON_MENU = ReplyKeyboardMarkup([["📝 Проверить первый блок"],["💬 Задать вопрос по маркетинг-плану"],["⬅️ Главное меню"]], resize_keyboard=True, is_persistent=True)
NEXT_LESSON_MENU = ReplyKeyboardMarkup([["➡️ Урок 2 — Первые бонусы"],["💬 Задать вопрос по маркетинг-плану"],["⬅️ Главное меню"]], resize_keyboard=True, is_persistent=True)
LESSON_02_MENU = ReplyKeyboardMarkup([["📝 Проверить второй блок"],["💬 Задать вопрос по маркетинг-плану"],["⬅️ Главное меню"]], resize_keyboard=True, is_persistent=True)
NEXT_BLOCK_MENU = ReplyKeyboardMarkup([["➡️ Следующий блок"],["💬 Задать вопрос по маркетинг-плану"],["⬅️ Главное меню"]], resize_keyboard=True, is_persistent=True)
CHECK_MENU = ReplyKeyboardMarkup([["A", "B", "C"], ["⬅️ Главное меню"]], resize_keyboard=True, is_persistent=True)
LESSON_IMAGE = "marketing_lesson_01.png.png"
LESSON_IMAGE_02 = "marketing_lesson_02.png.png"

async def marketing_lesson_router(update, context):
    message = getattr(update, "message", None)
    if not message or not message.text: return
    text = message.text.strip(); stage = context.user_data.get("marketing_lesson_stage")
    if text == "📊 Маркетинг-план":
        context.user_data.pop("marketing_lesson_stage", None); context.user_data.pop("marketing_quiz_step", None)
        await message.reply_text("📊 МАРКЕТИНГ-ПЛАН GREENLEAF\n\nЗдесь можно пройти обучение с самого начала — спокойно, небольшими блоками и с проверкой понимания.\n\nИли задать Лии свой вопрос по маркетинг-плану. Выбери, как продолжим 👇", reply_markup=MARKETING_MENU); raise ApplicationHandlerStop
    if text == "🎓 Начать обучение с нуля":
        image_path=os.path.join(os.path.dirname(__file__),LESSON_IMAGE)
        if not os.path.exists(image_path): await message.reply_text("Первый учебный блок пока не найден на сервере. Попробуй ещё раз после обновления.",reply_markup=MARKETING_MENU); raise ApplicationHandlerStop
        context.user_data["marketing_lesson_stage"]="lesson_01"; context.user_data.pop("marketing_quiz_step",None)
        with open(image_path,"rb") as image: await message.reply_photo(photo=image,caption="🎓 УРОК 1 | ОСНОВА МАРКЕТИНГ-ПЛАНА\n\nПосмотри первый блок: как устроен маркетинг-план, что такое PV и как формируются левая и правая группы.\n\nКогда будешь готова — нажми «📝 Проверить первый блок».")
        await message.reply_text("Я рядом 💚 Можно увеличить изображение и спокойно всё рассмотреть.",reply_markup=LESSON_MENU); raise ApplicationHandlerStop
    if text == "📝 Проверить первый блок":
        context.user_data["marketing_lesson_stage"]="quiz_01"; context.user_data["marketing_quiz_step"]=1
        await message.reply_text("💬 ПРОВЕРИМ ПОНИМАНИЕ — 1/3\n\nНа чём основан маркетинг-план Greenleaf?\n\nA — Только на продаже продукции\nB — На покупке продукции и развитии команды\nC — Только на привлечении новых партнёров",reply_markup=CHECK_MENU); raise ApplicationHandlerStop
    if stage=="quiz_01" and text.upper() in {"A","B","C","А","Б","В"}:
        normalized={"А":"A","Б":"B","В":"C"}.get(text.upper(),text.upper()); step=context.user_data.get("marketing_quiz_step",1); correct={1:"B",2:"B",3:"C"}[step]
        if normalized!=correct:
            hints={1:"Не совсем 💚 Маркетинг-план связан и с покупкой продукции, и с развитием команды. Попробуй ещё раз.",2:"Не совсем 💚 PV — это условные баллы объёма, присваиваемые товарам, а не деньги. Попробуй ещё раз.",3:"Не совсем 💚 Структура включает левую и правую группы. Попробуй ещё раз."}; await message.reply_text(hints[step],reply_markup=CHECK_MENU); raise ApplicationHandlerStop
        if step==1:
            context.user_data["marketing_quiz_step"]=2; await message.reply_text("Верно! 💚\n\n💬 ПРОВЕРИМ ПОНИМАНИЕ — 2/3\n\nЧто такое PV в Greenleaf?\n\nA — Деньги, которые сразу выплачиваются\nB — Условные баллы, присваиваемые товарам\nC — Размер скидки на продукцию",reply_markup=CHECK_MENU); raise ApplicationHandlerStop
        if step==2:
            context.user_data["marketing_quiz_step"]=3; await message.reply_text("Верно! 💚\n\n💬 ПРОВЕРИМ ПОНИМАНИЕ — 3/3\n\nКак устроена структура в Greenleaf?\n\nA — Только левая группа\nB — Только правая группа\nC — Левая и правая группы",reply_markup=CHECK_MENU); raise ApplicationHandlerStop
        context.user_data["marketing_lesson_stage"]="lesson_01_done"; context.user_data.pop("marketing_quiz_step",None)
        await message.reply_text("Супер! 💚 Первый блок пройден.\n\nТы разобралась в трёх базовых вещах:\n• на чём основан маркетинг-план;\n• что такое PV;\n• как устроены левая и правая группы.\n\nТеперь можно переходить к первым бонусам 👇",reply_markup=NEXT_LESSON_MENU); raise ApplicationHandlerStop
    if text == "➡️ Урок 2 — Первые бонусы":
        image_path=os.path.join(os.path.dirname(__file__),LESSON_IMAGE_02)
        if not os.path.exists(image_path): await message.reply_text("Второй учебный блок пока не найден на сервере. Попробуй ещё раз после обновления.",reply_markup=NEXT_LESSON_MENU); raise ApplicationHandlerStop
        context.user_data["marketing_lesson_stage"]="lesson_02"; context.user_data.pop("marketing_quiz_step",None)
        with open(image_path,"rb") as image: await message.reply_photo(photo=image,caption="🎓 УРОК 2 | ПЕРВЫЕ БОНУСЫ\n\nЗдесь разбираем три базовых вида бонусов: бонус наставника, бонус глубины и бинарный бонус (бонус ширины).\n\nВнимательно посмотри слайд. Когда будешь готова — нажми «📝 Проверить второй блок».")
        await message.reply_text("Не спеши 💚 Сначала разберись, за какое действие начисляется каждый из трёх бонусов.",reply_markup=LESSON_02_MENU); raise ApplicationHandlerStop
    if text == "📝 Проверить второй блок":
        context.user_data["marketing_lesson_stage"]="quiz_02"; context.user_data["marketing_quiz_step"]=1
        await message.reply_text("💬 ПРОВЕРИМ ПОНИМАНИЕ — 1/3\n\nЗа какое действие начисляется бонус наставника?\n\nA — За товарооборот меньшей группы\nB — За лично приглашённого партнёра, который приобрёл стартовый набор\nC — За любую личную покупку",reply_markup=CHECK_MENU); raise ApplicationHandlerStop
    if stage=="quiz_02" and text.upper() in {"A","B","C","А","Б","В"}:
        normalized={"А":"A","Б":"B","В":"C"}.get(text.upper(),text.upper()); step=context.user_data.get("marketing_quiz_step",1); correct={1:"B",2:"B",3:"B"}[step]
        if normalized!=correct:
            hints={1:"Не совсем 💚 Бонус наставника связан с твоим лично приглашённым партнёром и покупкой им стартового набора. Попробуй ещё раз.",2:"Не совсем 💚 Бонус глубины появляется, когда партнёры твоей структуры приглашают новых партнёров и команда развивается в глубину. Попробуй ещё раз.",3:"Не совсем 💚 Бинарный бонус (бонус ширины) зависит от товарооборота меньшей группы по стартовым наборам и условий твоего пакета. Попробуй ещё раз."}; await message.reply_text(hints[step],reply_markup=CHECK_MENU); raise ApplicationHandlerStop
        if step==1:
            context.user_data["marketing_quiz_step"]=2; await message.reply_text("Верно! 💚\n\n💬 ПРОВЕРИМ ПОНИМАНИЕ — 2/3\n\nКогда возникает бонус глубины?\n\nA — Когда ты сама покупаешь продукцию\nB — Когда партнёры твоей структуры приглашают новых партнёров и команда развивается в глубину\nC — Только когда растёт меньшая группа",reply_markup=CHECK_MENU); raise ApplicationHandlerStop
        if step==2:
            context.user_data["marketing_quiz_step"]=3; await message.reply_text("Верно! 💚\n\n💬 ПРОВЕРИМ ПОНИМАНИЕ — 3/3\n\nОт чего зависит бинарный бонус (бонус ширины)?\n\nA — Только от количества лично приглашённых партнёров\nB — От товарооборота меньшей группы (стартовые наборы) и условий пакета\nC — Только от личных покупок",reply_markup=CHECK_MENU); raise ApplicationHandlerStop
        context.user_data["marketing_lesson_stage"]="lesson_02_done"; context.user_data.pop("marketing_quiz_step",None)
        await message.reply_text("Отлично! 💚 Второй блок пройден.\n\nТеперь ты различаешь три первых вида бонусов:\n• бонус наставника;\n• бонус глубины;\n• бинарный бонус (бонус ширины).\n\nГотова двигаться дальше? 👇",reply_markup=NEXT_BLOCK_MENU); raise ApplicationHandlerStop
    if text == "➡️ Следующий блок":
        await message.reply_text("Следующий учебный блок сейчас подключаем 💚", reply_markup=NEXT_BLOCK_MENU); raise ApplicationHandlerStop
    if text == "💬 Задать вопрос по маркетинг-плану":
        context.user_data.pop("marketing_lesson_stage",None); context.user_data.pop("marketing_quiz_step",None); context.user_data["mode"]="📊 Маркетинг-план"; context.user_data["dialog_history"]=[]
        await message.reply_text("💬 Напиши свой вопрос по маркетинг-плану Greenleaf. Лия ответит по подтверждённой CURRENT-базе и не будет додумывать отсутствующие правила.",reply_markup=MARKETING_MENU); raise ApplicationHandlerStop

_original_add_handler=Application.add_handler; _marketing_router_registered=set()
def patched_add_handler(self,handler,group=0):
    callback=getattr(handler,"callback",None); callback_name=getattr(callback,"__name__",""); app_key=id(self)
    if callback_name in {"chat","fast_newcomer_callback"} and app_key not in _marketing_router_registered:
        _original_add_handler(self,MessageHandler(filters.TEXT & ~filters.COMMAND,marketing_lesson_router),group=-1); _marketing_router_registered.add(app_key); print(f"GREENLEAF marketing router registered before {callback_name}",flush=True)
    return _original_add_handler(self,handler,group=group)
Application.add_handler=patched_add_handler
print("GREENLEAF marketing lesson router v6 loaded",flush=True)
