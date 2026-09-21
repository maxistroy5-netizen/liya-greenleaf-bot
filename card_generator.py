import io
import os
import re
import tempfile
from urllib.parse import quote

import qrcode
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ECOSYSTEM_URL = "https://t.me/addlist/JxquFZkrHw4yYTMy"
BRAND_NAME = "GREENLEAF Leaders | Москва"

W, H = 720, 1280
GREEN = colors.HexColor("#075B3A")
LIGHT = colors.HexColor("#F4F8F1")


def _register_fonts():
    candidates = [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
    ]
    for regular, bold in candidates:
        if os.path.exists(regular) and os.path.exists(bold):
            pdfmetrics.registerFont(TTFont("GLRegular", regular))
            pdfmetrics.registerFont(TTFont("GLBold", bold))
            return "GLRegular", "GLBold"
    return "Helvetica", "Helvetica-Bold"

FONT, FONT_BOLD = _register_fonts()


def _digits(value):
    return re.sub(r"\D", "", value or "")


def _telegram_url(value):
    value = (value or "").strip()
    if value.startswith(("http://", "https://")):
        return value
    if value.startswith("@"):
        return "https://t.me/" + value[1:]
    d = _digits(value)
    return "https://t.me/+" + d if d else "https://t.me/"


def _whatsapp_url(value):
    value = (value or "").strip()
    if value.startswith(("http://", "https://")):
        return value
    d = _digits(value)
    return "https://wa.me/" + d if d else "https://wa.me/"


def _instagram_url(value):
    value = (value or "").strip()
    if value.startswith(("http://", "https://")):
        return value
    return "https://instagram.com/" + value.lstrip("@")


def _max_url(value):
    value = (value or "").strip()
    if value.startswith(("http://", "https://")):
        return value
    return "https://max.ru/" + quote(value.lstrip("@"))


def _fit(c, text, x, y, max_width, size=28, font=None, min_size=10):
    font = font or FONT_BOLD
    text = str(text or "")
    s = size
    while s > min_size and c.stringWidth(text, font, s) > max_width:
        s -= 1
    c.setFont(font, s)
    c.drawString(x, y, text)


def _button(c, x, y, w, h, title, value, url, fill):
    c.setFillColor(fill)
    c.roundRect(x, y, w, h, 16, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 11)
    c.drawString(x + 18, y + h - 22, title)
    _fit(c, value, x + 18, y + 18, w - 38, 16, FONT, 9)
    if url:
        c.linkURL(url, (x, y, x + w, y + h), relative=0)


def _draw_brand_mark(c, cx, cy, r):
    c.setFillColor(colors.white)
    c.setStrokeColor(GREEN)
    c.setLineWidth(3)
    c.circle(cx, cy, r, fill=1, stroke=1)
    c.setFillColor(colors.HexColor("#66B82E"))
    for dx, dy in [(0, 25), (-24, 5), (24, 5), (-18, -22), (18, -22)]:
        c.circle(cx + dx, cy + dy, r * .23, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.setFont(FONT_BOLD, 10)
    c.drawCentredString(cx, cy - 4, "GREENLEAF")
    c.setFont(FONT, 8)
    c.drawCentredString(cx, cy - 16, "Leaders | Москва")


def _draw_photo(c, photo_path):
    c.setStrokeColor(GREEN)
    c.setLineWidth(5)
    c.circle(125, 1120, 78, fill=0, stroke=1)
    if photo_path and os.path.exists(photo_path):
        try:
            img = ImageReader(photo_path)
            iw, ih = img.getSize()
            box = 144
            scale = max(box / iw, box / ih)
            dw, dh = iw * scale, ih * scale
            c.saveState()
            p = c.beginPath()
            p.circle(125, 1120, 70)
            c.clipPath(p, stroke=0, fill=0)
            c.drawImage(img, 125 - dw / 2, 1120 - dh / 2, dw, dh, mask="auto")
            c.restoreState()
            return
        except Exception:
            pass
    _draw_brand_mark(c, 125, 1120, 70)


def generate_business_card(data, photo_path=None, output_path=None):
    if output_path is None:
        fd, output_path = tempfile.mkstemp(prefix="greenleaf_card_", suffix=".pdf")
        os.close(fd)

    c = canvas.Canvas(output_path, pagesize=(W, H))
    c.setTitle("GREENLEAF electronic business card")

    c.setFillColor(LIGHT)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#E6F0DE"))
    c.circle(640, 1140, 270, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#DCEAD2"))
    c.circle(90, 950, 210, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.rect(0, 0, W, 180, fill=1, stroke=0)

    _draw_photo(c, photo_path)

    c.setFillColor(GREEN)
    c.setFont(FONT_BOLD, 13)
    c.drawString(48, 1010, "PEOPLE  |  PRODUCTS  |  OPPORTUNITIES")
    c.setFont(FONT, 12)
    c.drawString(48, 990, "A BETTER TOMORROW")

    name = (data.get("name") or "Партнёр Greenleaf").strip()
    c.setFillColor(colors.HexColor("#092E23"))
    _fit(c, name, 48, 895, 390, 39, FONT_BOLD, 20)
    c.setFillColor(GREEN)
    c.setFont(FONT_BOLD, 20)
    c.drawString(48, 850, "ПАРТНЁР КОРПОРАЦИИ")
    c.drawString(48, 820, "GREENLEAF")
    c.setFont(FONT, 14)
    c.drawString(48, 770, "ЛУЧШИЕ ВОЗМОЖНОСТИ ДЛЯ ЛУЧШИХ ЛЮДЕЙ")

    qr = qrcode.QRCode(version=None, box_size=7, border=2)
    qr.add_data(ECOSYSTEM_URL)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    bio = io.BytesIO()
    qr_img.save(bio, format="PNG")
    bio.seek(0)
    c.setFillColor(colors.white)
    c.roundRect(462, 820, 220, 300, 18, fill=1, stroke=0)
    c.drawImage(ImageReader(bio), 482, 890, 180, 180)
    _draw_brand_mark(c, 572, 980, 28)
    c.setFillColor(GREEN)
    c.setFont(FONT_BOLD, 14)
    c.drawCentredString(572, 862, "GREENLEAF CLUB.RU")
    c.setFont(FONT, 10)
    c.drawCentredString(572, 842, "СКАНИРУЙ QR-КОД")
    c.linkURL(ECOSYSTEM_URL, (462, 820, 682, 1120), relative=0)

    c.setFillColor(colors.white)
    c.roundRect(48, 650, 624, 82, 16, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.setFont(FONT_BOLD, 11)
    c.drawString(78, 705, "ИМЯ")
    c.setFillColor(colors.HexColor("#092E23"))
    _fit(c, name, 78, 672, 560, 25, FONT_BOLD, 14)

    phone = (data.get("phone") or "").strip()
    c.setFillColor(colors.white)
    c.roundRect(48, 550, 624, 82, 16, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.setFont(FONT_BOLD, 11)
    c.drawString(78, 605, "ТЕЛЕФОН")
    c.setFillColor(colors.HexColor("#092E23"))
    _fit(c, phone, 78, 572, 560, 24, FONT_BOLD, 14)
    if phone:
        c.linkURL("tel:" + phone.replace(" ", ""), (48, 550, 672, 632), relative=0)

    telegram = (data.get("telegram") or "").strip()
    whatsapp = (data.get("whatsapp") or "").strip()
    email = (data.get("email") or "").strip()
    max_value = (data.get("max") or "").strip()
    instagram = (data.get("instagram") or "").strip()

    _button(c, 48, 445, 198, 84, "TELEGRAM", telegram, _telegram_url(telegram), colors.HexColor("#168CD8"))
    _button(c, 261, 445, 198, 84, "WHATSAPP", whatsapp, _whatsapp_url(whatsapp), colors.HexColor("#12A85B"))
    _button(c, 474, 445, 198, 84, "E-MAIL", email, "mailto:" + email if email else "", GREEN)
    _button(c, 48, 340, 305, 82, "MAX", max_value, _max_url(max_value), colors.HexColor("#335C67"))
    _button(c, 367, 340, 305, 82, "INSTAGRAM", instagram, _instagram_url(instagram), colors.HexColor("#B23A78"))

    c.setFillColor(GREEN)
    c.setFont(FONT_BOLD, 16)
    c.drawCentredString(W / 2, 285, "НАШИ ЦЕННОСТИ")
    c.setFont(FONT_BOLD, 13)
    c.drawCentredString(120, 245, "ЛЮДИ")
    c.drawCentredString(280, 245, "ПРОДУКТЫ")
    c.drawCentredString(445, 245, "ВОЗМОЖНОСТИ")
    c.drawCentredString(610, 245, "БУДУЩЕЕ")

    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 18)
    c.drawString(48, 125, "GREEN FUTURE TOGETHER")
    c.setFont(FONT, 11)
    c.drawString(48, 96, BRAND_NAME)
    c.drawRightString(672, 96, "МЕЖДУНАРОДНЫЙ БИЗНЕС")
    c.drawRightString(672, 78, "С РЕАЛЬНЫМИ ВОЗМОЖНОСТЯМИ")

    c.save()
    return output_path
