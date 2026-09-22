"""Runtime hooks for GREENLEAF business-card and 3-step invitation flows."""

import os

try:
    from telegram import Message, ReplyKeyboardMarkup

    _original_reply_document = Message.reply_document
    _original_reply_text = Message.reply_text

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
            await _original_reply_text(
                self,
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

    async def _reply_text_with_invitation_pdf(self, text, *args, **kwargs):
        step = None
        if isinstance(text, str):
            if text.startswith("1️⃣ ПЕРВОЕ КАСАНИЕ"):
                step = 1
            elif text.startswith("2️⃣ ВТОРОЕ КАСАНИЕ"):
                step = 2
            elif text.startswith("3️⃣ ТРЕТЬЕ КАСАНИЕ"):
                step = 3

        if step:
            pdf_path = f"{step} шаг.pdf"
            if os.path.exists(pdf_path):
                try:
                    with open(pdf_path, "rb") as document:
                        await _original_reply_document(
                            self,
                            document=document,
                            filename=pdf_path,
                            caption=f"💚 ШАГ {step} — готовый материал для приглашения.",
                        )
                except Exception as exc:
                    print(f"GREENLEAF invitation PDF error ({pdf_path}): {exc}")
            else:
                print(f"GREENLEAF invitation PDF not found: {pdf_path}")

        return await _original_reply_text(self, text, *args, **kwargs)

    Message.reply_document = _reply_document_with_greenleaf_followup
    Message.reply_text = _reply_text_with_invitation_pdf
except Exception as exc:
    print(f"GREENLEAF runtime hook not loaded: {exc}")
