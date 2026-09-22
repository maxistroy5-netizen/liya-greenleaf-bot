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
    _sender_by_chat = {}

    def _register_cyrillic_font():
        font_name = "GreenleafSans"
        if font_name in pdfmetrics.getRegisteredFontNames():
            return font_name
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
        for path in candidates:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont(font_name, path))
                return font_name
        for root in ("/usr/share/fonts", "/usr/local/share/fonts"):
            if not os.path.isdir(root):
                continue
            for dirpath, _, filenames in os.walk(root):
                for filename in filenames:
                    if filename.lower() in {"dejavusans.ttf", "notosans-regular.ttf", "freesans.ttf", "liberationsans-regular.ttf"}:
                        path = os.path.join(dirpath, filename)
                        try:
                            pdfmetrics.registerFont(TTFont(font_name, path))
                            return font_name
                        except Exception:
                            pass
        raise RuntimeError("Cyrillic TrueType font was not found on Render")

    def _recipient_from_text(text: str) -> str:
        # Works with: "Эрика, привет!" inside all three Liya messages.
        match = re.search(r"(?:^|\n)([^\n,]{1,60}),\s*привет!", text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _event_from_text(text: str):
        date_match = re.search(r"📅\s*([^\n]+)", text)
        time_match = re.search(r"🕙\s*([^\n]+)", text)
        urls = re.findall(r"https?://[^\s]+", text)
        zoom_url = ""
        for url in urls:
            if "zoom.us" in url:
                zoom_url = url.rstrip(".,;:!?")
                break
        if not zoom_url and urls:
            zoom_url = urls[0].rstrip(".,;:!?")
        return (
            date_match.group(1).strip() if date_match else "",
            time_match.group(1).strip() if time_match else "",
            zoom_url,
        )

    def _safe_name(value: str) -> str:
        return re.sub(r"[^0-9A-Za-zА-Яа-яЁё_-]+", "_", value or "").strip("_") or "partner"

    def _fit_text(c, text, font_name, max_size, min_size, max_width):
        size = max_size
        while size > min_size and pdfmetrics.stringWidth(text, font_name, size) > max_width:
            size -= 0.5
        c.setFont(font_name, size)

    def _make_personalized_pdf(step: int, recipient: str, sender: str = "", event_text: str = "") -> str:
        source_path = f"{step} шаг.pdf"
        if not os.path.exists(source_path):
            raise FileNotFoundError(source_path)

        reader = PdfReader(source_path)
        page = reader.pages[0]
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        font_name = _register_cyrillic_font()

        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=(width, height))
        c.setFillColorRGB(0.08, 0.34, 0.20)

        recipient = (recipient or "").strip()
        sender = (sender or "").strip()

        # A clearly visible personalized block in the upper part of each template.
        y = height * 0.91
        if recipient:
            label = f"Для: {recipient}"
            _fit_text(c, label, font_name, min(22, width * 0.021), 10, width * 0.72)
            c.drawString(width * 0.10, y, label)
            y -= height * 0.04
        if sender:
            label = f"От: {sender}"
            _fit_text(c, label, font_name, min(18, width * 0.017), 9, width * 0.72)
            c.drawString(width * 0.10, y, label)

        if step == 3:
            event_date, event_time, zoom_url = _event_from_text(event_text)
            lines = []
            if event_date:
                lines.append(f"Дата: {event_date}")
            if event_time:
                lines.append(f"Время: {event_time}")
            if zoom_url:
                lines.append(f"Zoom: {zoom_url}")
            y = height * 0.24
            for line in lines:
                _fit_text(c, line, font_name, min(15, width * 0.014), 7, width * 0.80)
                c.drawString(width * 0.10, y, line)
                y -= height * 0.038

        c.save()
        overlay_buffer.seek(0)
        overlay_page = PdfReader(overlay_buffer).pages[0]
        page.merge_page(overlay_page)

        writer = PdfWriter()
        writer.add_page(page)
        for extra_page in reader.pages[1:]:
            writer.add_page(extra_page)

        output_path = os.path.join(tempfile.gettempdir(), f"GREENLEAF_Шаг_{step}_{_safe_name(recipient)}.pdf")
        with open(output_path, "wb") as output:
            writer.write(output)
        return output_path

    async def _reply_document_with_greenleaf_followup(self, *args, **kwargs):
        result = await _original_reply_document(self, *args, **kwargs)
        filename = kwargs.get("filename") or ""
        if filename.startswith("GREENLEAF_") and filename.lower().endswith(".pdf") and "Шаг_" not in filename:
            stem = os.path.splitext(filename)[0]
            sender = stem[len("GREENLEAF_"):].replace("_", " ").strip()
            if sender:
                _sender_by_chat[self.chat_id] = sender
        return result

    async def _reply_text_with_invitation_pdf(self, text, *args, **kwargs):
        step = None
        if isinstance(text, str):
            if text.startswith("1️⃣ ПЕРВОЕ КАСАНИЕ"):
                step = 1
            elif text.startswith("2️⃣ ВТОРОЕ КАСАНИЕ"):
                step = 2
            elif text.startswith("3️⃣ ГОТОВОЕ ПРИГЛАШЕНИЕ"):
                step = 3

        if step:
            temp_pdf = None
            try:
                recipient = _recipient_from_text(text)
                sender = _sender_by_chat.get(self.chat_id, "")
                temp_pdf = _make_personalized_pdf(step, recipient, sender, text)
                with open(temp_pdf, "rb") as document:
                    await _original_reply_document(
                        self,
                        document=document,
                        filename=os.path.basename(temp_pdf),
                        caption=f"💚 ШАГ {step} — персональный PDF для {recipient or 'приглашения'}.",
                    )
            except Exception as exc:
                print(f"GREENLEAF PDF PERSONALIZATION FAILED step={step}: {type(exc).__name__}: {exc}", flush=True)
                # Deliberately do NOT send the empty template: it hides the real error.
                await _original_reply_text(
                    self,
                    f"⚠️ Не удалось персонализировать PDF шага {step}. Пустой шаблон не отправляю. Ошибка записана в Render Logs.",
                )
            finally:
                if temp_pdf and os.path.exists(temp_pdf):
                    try:
                        os.remove(temp_pdf)
                    except OSError:
                        pass

        return await _original_reply_text(self, text, *args, **kwargs)

    Message.reply_document = _reply_document_with_greenleaf_followup
    Message.reply_text = _reply_text_with_invitation_pdf
    print("GREENLEAF personalized PDF hook v2 loaded", flush=True)
except Exception as exc:
    print(f"GREENLEAF runtime hook not loaded: {type(exc).__name__}: {exc}", flush=True)
