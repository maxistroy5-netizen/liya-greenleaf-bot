"""Small runtime hook: after a GREENLEAF business-card PDF is sent, offer the next training step."""

try:
    from telegram import Message, ReplyKeyboardMarkup

    _original_reply_document = Message.reply_document

    async def _reply_document_with_greenleaf_followup(self, *args, **kwargs):
        result = await _original_reply_document(self, *args, **kwargs)
        filename = kwargs.get("filename") or ""
        if filename.startswith("GREENLEAF_") and filename.lower().endswith(".pdf"):
            keyboard = ReplyKeyboardMarkup(
                [
                    ["🤝 3 шага приглашения партнёра"],
                    ["⬅️ Главное меню"],
                ],
                resize_keyboard=True,
                is_persistent=True,
            )
            await self.reply_text(
                "💚 Визитка готова!\n\n"
                "Следующий шаг — научиться правильно приглашать человека без давления и навязывания.\n\n"
                "Лия проведёт тебя по готовому алгоритму:\n"
                "1️⃣ первое касание — визитка\n"
                "2️⃣ второе касание — обратная связь\n"
                "3️⃣ третье касание — приглашение на Zoom\n\n"
                "Хочешь пройти 3 шага прямо сейчас? Нажми кнопку ниже 👇",
                reply_markup=keyboard,
            )
        return result

    Message.reply_document = _reply_document_with_greenleaf_followup
except Exception as exc:
    print(f"GREENLEAF follow-up hook not loaded: {exc}")
