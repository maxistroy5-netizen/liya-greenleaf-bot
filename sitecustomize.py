"""Runtime hooks for GREENLEAF business-card and 3-step invitation flows."""

import io
import os
import re
import tempfile

try:
    from telegram import Message, ReplyKeyboardMarkup
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from pypdf import PdfReader, PdfWriter

    _original_reply_document = Message.reply_document
    _original_reply_text = Message.reply_text

    def _register_cyrillic_font():
        font_name = "DejaVuSans"
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, path))
                    return font_name
                except Exception:
                    pass
        return "Helvetica"

    def _recipient_from_step1_text(text: str) -> str:
        # invite_text() begins with: "Имя, привет!"
        match = re.search(r"(?:сообщение:\s*)?\n*([^\n,]{1,40}),\s*привет!", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def _make_personalized_step1_pdf(recipient: str) -> str:
        source_path = "1 шаг.pdf"
        if not os.path.exists(source_path):
            raise FileNotFoundError(source_path)

        reader = PdfReader(source_path)
        page = reader.pages[0]
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)

        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=(width, height))
        font_name = _register_cyrillic_font()

        # The source design has a dedicated green name field after «Привет,».
        # Coordinates are proportional so the placement remains stable if the
        # PDF page dimensions differ from the preview dimensions.
        x = width * 0.145
        y = height * 0.802
        field_width = width * 0.175
        font_size = min(22, max(12, width * 0.020))
        c.setFont(font_name, font_size)
        c.setFillColorRGB(0.08, 0.34, 0.20)

        name = (recipient or "").strip()
        if name:
            while font_size > 10 and pdfmetrics.stringWidth(name, font_name, font_size) > field_width:
                font_size -= 1
                c.setFont(font_name, font_size)
            c.drawString(x, y, name)

        c.save()
        overlay_buffer.seek(0)
        overlay_page = PdfReader(overlay_buffer).pages[0]
        page.merge_page(overlay_page)

        writer = PdfWriter()
        writer.add_page(page)
        for extra_page in reader.pages[1:]:
            writer.add_page(extra_page)

        safe_name = re.sub(r"[^0-9A-Za-zА-Яа-яЁё_-]+", "_", name).strip("_") or "partner"
        output_path = os.path.join(tempfile.gettempdir(), f"GREENLEAF_Шаг_1_{safe_name}.pdf")
        with open(output_path, "wb") as output:
            writer.write(output)
        return output_path

    async def _reply_document_with_greenleaf_followup(self, *args, **kwargs):
        result = await _original_reply_document(self, *args, **kwargs)
        filename = kwargs.get("filename") or ""
        if filename.startswith("GREENLEAF_") and filename.lower().endswith(".pdf") and "Шаг_1_" not in filename:
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
            temp_pdf = None
            try:
                if step == 1:
                    recipient = _recipient_from_step1_text(text)
                    temp_pdf = _make_personalized_step1_pdf(recipient)
                    pdf_path = temp_pdf
                    send_name = os.path.basename(temp_pdf)
                    caption = f"💚 ШАГ 1 — персональный материал для {recipient}." if recipient else "💚 ШАГ 1 — персональный материал для приглашения."
                else:
                    pdf_path = f"{step} шаг.pdf"
                    send_name = pdf_path
                    caption = f"💚 ШАГ {step} — готовый материал для приглашения."

                if os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as document:
                        await _original_reply_document(
                            self,
                            document=document,
                            filename=send_name,
                            caption=caption,
                        )
                else:
                    print(f"GREENLEAF invitation PDF not found: {pdf_path}")
            except Exception as exc:
                print(f"GREENLEAF invitation PDF error (step {step}): {exc}")
                # If personalization fails, do not break the invitation flow.
                fallback = f"{step} шаг.pdf"
                if os.path.exists(fallback):
                    try:
                        with open(fallback, "rb") as document:
                            await _original_reply_document(
                                self,
                                document=document,
                                filename=fallback,
                                caption=f"💚 ШАГ {step} — готовый материал для приглашения.",
                            )
                    except Exception as fallback_exc:
                        print(f"GREENLEAF fallback PDF error ({fallback}): {fallback_exc}")
            finally:
                if temp_pdf and os.path.exists(temp_pdf):
                    try:
                        os.remove(temp_pdf)
                    except OSError:
                        pass

        return await _original_reply_text(self, text, *args, **kwargs)

    Message.reply_document = _reply_document_with_greenleaf_followup
    Message.reply_text = _reply_text_with_invitation_pdf
except Exception as exc:
    print(f"GREENLEAF runtime hook not loaded: {exc}")
