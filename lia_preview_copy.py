"""Draft copy for the isolated multilingual dialogue prototype."""

# menu title, learn, practice, quiz, ask, language, sources, error, test notice
COPY = {
    "ru": ("Выберите раздел", "📊 Обучение", "💬 Тренировка диалога", "🎓 Проверить знания", "✍️ Задать вопрос", "🌐 Сменить язык", "📖 Источники", "Не удалось получить ответ. Попробуйте ещё раз.", "Тестовая версия: диалоговое обучение. Готовые уроки, визитки и PDF пока доступны в основной Лии."),
    "uz": ("Bo‘limni tanlang", "📊 O‘rganish", "💬 Suhbat mashqi", "🎓 Bilimni tekshirish", "✍️ Savol berish", "🌐 Tilni o‘zgartirish", "📖 Manbalar", "Javobni olishning imkoni bo‘lmadi. Qayta urinib ko‘ring.", "Sinov versiyasi: suhbat orqali o‘rganish. Tayyor darslar, tashrif kartalari va PDF fayllar hozircha asosiy Liyada mavjud."),
    "tg": ("Бахшро интихоб кунед", "📊 Омӯзиш", "💬 Машқи муколама", "🎓 Санҷиши дониш", "✍️ Савол додан", "🌐 Иваз кардани забон", "📖 Манбаъҳо", "Ҷавоб гирифта нашуд. Боз кӯшиш кунед.", "Нусхаи озмоишӣ: омӯзиш тавассути муколама. Дарсҳои омода, кортҳои шиносоӣ ва PDF ҳоло дар Лияи асосӣ дастрасанд."),
    "ky": ("Бөлүмдү тандаңыз", "📊 Үйрөнүү", "💬 Диалог машыгуусу", "🎓 Билимди текшерүү", "✍️ Суроо берүү", "🌐 Тилди өзгөртүү", "📖 Булактар", "Жооп алынган жок. Кайра аракет кылыңыз.", "Сыноо версиясы: диалог аркылуу үйрөнүү. Даяр сабактар, визиткалар жана PDF файлдар азырынча негизги Лияда жеткиликтүү."),
    "tr": ("Bir bölüm seçin", "📊 Eğitim", "💬 Diyalog pratiği", "🎓 Bilgi kontrolü", "✍️ Soru sor", "🌐 Dili değiştir", "📖 Kaynaklar", "Yanıt alınamadı. Lütfen tekrar deneyin.", "Test sürümü: diyalog yoluyla öğrenme. Hazır dersler, kartvizitler ve PDF dosyaları şimdilik ana Liya botunda mevcuttur."),
    "az": ("Bölmə seçin", "📊 Təlim", "💬 Dialoq məşqi", "🎓 Bilik yoxlaması", "✍️ Sual ver", "🌐 Dili dəyiş", "📖 Mənbələr", "Cavab almaq mümkün olmadı. Yenidən cəhd edin.", "Sınaq versiyası: dialoq vasitəsilə öyrənmə. Hazır dərslər, vizit kartları və PDF faylları hələlik əsas Liya botunda mövcuddur."),
    "en": ("Choose a section", "📊 Learn", "💬 Practise a dialogue", "🎓 Check knowledge", "✍️ Ask a question", "🌐 Change language", "📖 Sources", "Could not get a response. Please try again.", "Test version: dialogue-based learning. Prepared lessons, business cards and PDFs remain in the main Liya bot."),
    "fr": ("Choisissez une rubrique", "📊 Apprendre", "💬 Pratiquer un dialogue", "🎓 Vérifier ses connaissances", "✍️ Poser une question", "🌐 Changer de langue", "📖 Sources", "Impossible d’obtenir une réponse. Veuillez réessayer.", "Version de test : apprentissage par le dialogue. Les cours préparés, cartes de visite et PDF restent disponibles dans le bot Liya principal."),
    "de": ("Wähle einen Bereich", "📊 Lernen", "💬 Dialog üben", "🎓 Wissen prüfen", "✍️ Frage stellen", "🌐 Sprache ändern", "📖 Quellen", "Die Antwort konnte nicht abgerufen werden. Bitte versuche es erneut.", "Testversion: Lernen im Dialog. Vorbereitete Lektionen, Visitenkarten und PDFs sind weiterhin im Hauptbot Liya verfügbar."),
}
KEYS = {key: i for i, key in enumerate(("title", "learn", "practice", "quiz", "ask", "language", "sources", "error", "notice"))}


def copy(code, key):
    return COPY[code][KEYS[key]]
