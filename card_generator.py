import io
import os
import re
import tempfile
from urllib.parse import quote, urlparse

import qrcode
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ECOSYSTEM_URL = "https://t.me/addlist/OlNIwOt0mnI2ZmI6"
BRAND_NAME = "GREENLEAF Leaders | Москва"
CLUB_NAME = "GREENRU💚CLUB"
BRAND_LOGO_FILE = "ChatGPT Image 17 сент. 2026 г._ 19_12_45.png"
W, H = 720, 1280
GREEN = colors.HexColor("#075B3A")
DARK = colors.HexColor("#092E23")
LIGHT = colors.HexColor("#F8FBF5")
PALE = colors.HexColor("#EAF4E4")
GOLD = colors.HexColor("#C6A64A")


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

def _digits(value): return re.sub(r"\D", "", value or "")
def _telegram_url(value):
    value=(value or "").strip()
    if value.startswith(("http://","https://")): return value
    if value.startswith("@"): return "https://t.me/"+value[1:]
    d=_digits(value); return "https://t.me/+"+d if d else ""
def _whatsapp_url(value):
    value=(value or "").strip()
    if value.startswith(("http://","https://")): return value
    d=_digits(value); return "https://wa.me/"+d if d else ""
def _instagram_url(value):
    value=(value or "").strip()
    if value.startswith(("http://","https://")): return value
    return "https://instagram.com/"+value.lstrip("@") if value else ""
def _max_url(value):
    value=(value or "").strip()
    if value.startswith(("http://","https://")): return value
    return "https://max.ru/"+quote(value.lstrip("@")) if value else ""
def _short_social(value, kind):
    value=(value or "").strip()
    if not value: return ""
    if not value.startswith(("http://","https://")): return value
    try:
        p=urlparse(value); path=p.path.strip("/")
        if kind in ("instagram","telegram","max") and path: return "@"+path.split("/")[0]
        return p.netloc.replace("www.","")
    except Exception: return value

def _fit(c,text,x,y,max_width,size=28,font=None,min_size=9):
    font=font or FONT_BOLD; text=str(text or ""); s=size
    while s>min_size and c.stringWidth(text,font,s)>max_width: s-=1
    c.setFont(font,s); c.drawString(x,y,text)

def _button(c,x,y,w,h,title,display,url,fill):
    c.setFillColor(fill); c.roundRect(x,y,w,h,17,fill=1,stroke=0)
    c.setFillColor(colors.white); c.setFont(FONT_BOLD,11); c.drawString(x+18,y+h-23,title)
    _fit(c,display,x+18,y+18,w-38,16,FONT,9)
    c.setFont(FONT_BOLD,24); c.drawRightString(x+w-16,y+29,"›")
    if url: c.linkURL(url,(x,y,x+w,y+h),relative=0)

def _logo_path(): return os.path.join(os.path.dirname(os.path.abspath(__file__)),BRAND_LOGO_FILE)

def _draw_logo(c,x,y,w,h,alpha=1.0):
    path=_logo_path()
    if not os.path.exists(path): return
    try:
        img=ImageReader(path); iw,ih=img.getSize(); scale=min(w/iw,h/ih); dw,dh=iw*scale,ih*scale
        c.saveState(); c.setFillAlpha(alpha)
        c.drawImage(img,x+(w-dw)/2,y+(h-dh)/2,dw,dh,mask="auto",preserveAspectRatio=True)
        c.restoreState()
    except Exception: pass

def _draw_watermark(c):
    _draw_logo(c,110,420,500,650,0.055)
    c.saveState(); c.setStrokeColor(colors.HexColor("#B9D9B0")); c.setStrokeAlpha(0.32); c.setLineWidth(1)
    c.circle(360,770,270,fill=0,stroke=1); c.circle(360,770,225,fill=0,stroke=1)
    c.restoreState()

def _draw_qr_logo(c,cx,cy,size=50):
    c.setFillColor(colors.white); c.circle(cx,cy,size*.58,fill=1,stroke=0)
    _draw_logo(c,cx-size/2,cy-size/2,size,size,1.0)

def _draw_photo(c,photo_path):
    c.setStrokeColor(GREEN); c.setLineWidth(4); c.circle(122,1098,75,fill=0,stroke=1)
    c.setStrokeColor(GOLD); c.setLineWidth(1); c.circle(122,1098,68,fill=0,stroke=1)
    if photo_path and os.path.exists(photo_path):
        try:
            img=ImageReader(photo_path); iw,ih=img.getSize(); box=130; scale=max(box/iw,box/ih); dw,dh=iw*scale,ih*scale
            c.saveState(); p=c.beginPath(); p.circle(122,1098,64); c.clipPath(p,stroke=0,fill=0)
            c.drawImage(img,122-dw/2,1098-dh/2,dw,dh,mask="auto"); c.restoreState(); return
        except Exception: pass
    c.setFillColor(colors.white); c.circle(122,1098,64,fill=1,stroke=0)

def generate_business_card(data,photo_path=None,output_path=None):
    if output_path is None:
        fd,output_path=tempfile.mkstemp(prefix="greenru_card_",suffix=".pdf"); os.close(fd)
    c=canvas.Canvas(output_path,pagesize=(W,H)); c.setTitle("GREENRU CLUB electronic business card")
    c.setFillColor(LIGHT); c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(PALE); c.circle(650,1170,240,fill=1,stroke=0); c.circle(30,960,180,fill=1,stroke=0)
    _draw_watermark(c)

    # Premium footer with soft wave lines.
    c.setFillColor(GREEN); c.rect(0,0,W,170,fill=1,stroke=0)
    c.setStrokeColor(GOLD); c.setLineWidth(1.2); c.bezier(0,185,190,145,420,205,720,175)
    c.setStrokeColor(colors.HexColor("#7CBF7A")); c.setLineWidth(2); c.bezier(0,196,220,160,470,215,720,188)

    _draw_photo(c,photo_path)
    # Always use the exact repository logo asset; never redraw it.
    _draw_logo(c,260,1042,190,150,1.0)

    qr=qrcode.QRCode(version=None,box_size=7,border=2); qr.add_data(ECOSYSTEM_URL); qr.make(fit=True)
    qr_img=qr.make_image(fill_color="black",back_color="white").convert("RGB")
    bio=io.BytesIO(); qr_img.save(bio,format="PNG"); bio.seek(0)
    c.setFillColor(colors.white); c.roundRect(500,960,175,265,18,fill=1,stroke=0)
    c.drawImage(ImageReader(bio),513,1060,149,149)
    _draw_qr_logo(c,587.5,1134.5,48)
    c.setFillColor(GREEN); c.setFont(FONT_BOLD,13); c.drawCentredString(587,1036,CLUB_NAME)
    c.setFont(FONT,9); c.drawCentredString(587,1018,"СКАНИРУЙ QR-КОД")
    c.setFont(FONT_BOLD,10); c.drawCentredString(587,990,"ОТКРЫТЬ КЛУБ →")
    c.linkURL(ECOSYSTEM_URL,(518,978,657,1002),relative=0); c.linkURL(ECOSYSTEM_URL,(500,1055,675,1225),relative=0)

    name=(data.get("name") or "Партнёр Greenleaf").strip()
    c.setFillColor(DARK); _fit(c,name,48,900,425,40,FONT_BOLD,21)
    c.setStrokeColor(GOLD); c.setLineWidth(2); c.line(48,880,118,880)
    c.setFillColor(GREEN); c.setFont(FONT,21); c.drawString(48,842,"ПАРТНЁР КОРПОРАЦИИ"); c.setFont(FONT_BOLD,21); c.drawString(48,812,"GREENLEAF")

    phone=(data.get("phone") or "").strip()
    c.setFillColor(colors.white); c.roundRect(48,685,624,80,17,fill=1,stroke=0)
    c.setStrokeColor(colors.HexColor("#B9D9B0")); c.setLineWidth(.8); c.roundRect(48,685,624,80,17,fill=0,stroke=1)
    c.setFillColor(GREEN); c.setFont(FONT_BOLD,11); c.drawString(78,738,"ТЕЛЕФОН")
    c.setFillColor(DARK); _fit(c,phone,78,705,540,25,FONT_BOLD,14)
    c.setFont(FONT_BOLD,28); c.setFillColor(GREEN); c.drawRightString(645,710,"›")
    if phone: c.linkURL("tel:"+phone.replace(" ",""),(48,685,672,765),relative=0)

    telegram=(data.get("telegram") or "").strip(); whatsapp=(data.get("whatsapp") or "").strip(); email=(data.get("email") or "").strip(); max_value=(data.get("max") or "").strip(); instagram=(data.get("instagram") or "").strip()
    _button(c,48,580,300,82,"TELEGRAM",_short_social(telegram,"telegram"),_telegram_url(telegram),colors.HexColor("#168CD8"))
    _button(c,372,580,300,82,"WHATSAPP",whatsapp,_whatsapp_url(whatsapp),colors.HexColor("#12A85B"))
    _button(c,48,475,300,82,"MAX",_short_social(max_value,"max"),_max_url(max_value),colors.HexColor("#335C67"))
    _button(c,372,475,300,82,"INSTAGRAM",_short_social(instagram,"instagram"),_instagram_url(instagram),colors.HexColor("#B23A78"))
    _button(c,48,370,624,82,"E-MAIL",email,"mailto:"+email if email else "",GREEN)

    c.setStrokeColor(colors.HexColor("#A9CFA2")); c.setLineWidth(.8); c.line(110,318,245,318); c.line(475,318,610,318)
    c.setFillColor(GREEN); c.setFont(FONT_BOLD,20); c.drawCentredString(W/2,310,CLUB_NAME)
    c.setFont(FONT,13); c.drawCentredString(W/2,284,"ВСЁ В ОДНОМ МЕСТЕ")
    c.linkURL(ECOSYSTEM_URL,(245,265,475,330),relative=0)

    c.setFillColor(colors.white); c.setFont(FONT_BOLD,19); c.drawString(48,108,"GREEN FUTURE TOGETHER")
    c.setFont(FONT,11); c.drawString(48,82,BRAND_NAME)
    c.drawRightString(672,102,"МЕЖДУНАРОДНЫЙ БИЗНЕС"); c.drawRightString(672,82,"С РЕАЛЬНЫМИ ВОЗМОЖНОСТЯМИ")
    c.save(); return output_path
