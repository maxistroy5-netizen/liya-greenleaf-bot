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

ECOSYSTEM_URL = "https://t.me/addlist/JxquFZkrHw4yYTMy"
BRAND_NAME = "GREENLEAF Leaders | Москва"
CLUB_NAME = "GREENRU💚CLUB"
BRAND_LOGO_FILE = "ChatGPT Image 17 сент. 2026 г._ 19_12_45.png"
W, H = 720, 1280
GREEN = colors.HexColor("#075B3A")
DARK = colors.HexColor("#092E23")
LIGHT = colors.HexColor("#F7FAF4")


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
    c.setFillColor(fill); c.roundRect(x,y,w,h,16,fill=1,stroke=0)
    c.setFillColor(colors.white); c.setFont(FONT_BOLD,11); c.drawString(x+18,y+h-22,title)
    _fit(c,display,x+18,y+18,w-38,16,FONT,9)
    if url: c.linkURL(url,(x,y,x+w,y+h),relative=0)

def _logo_path(): return os.path.join(os.path.dirname(os.path.abspath(__file__)),BRAND_LOGO_FILE)

def _draw_watermark(c):
    path=_logo_path()
    if not os.path.exists(path): return
    try:
        img=ImageReader(path); iw,ih=img.getSize(); maxw,maxh=620,780
        scale=min(maxw/iw,maxh/ih); dw,dh=iw*scale,ih*scale
        c.saveState(); c.setFillAlpha(0.10)
        c.drawImage(img,(W-dw)/2,360+(780-dh)/2,dw,dh,mask="auto",preserveAspectRatio=True)
        c.restoreState()
    except Exception: pass

def _draw_qr_logo(c,cx,cy,size=54):
    path=_logo_path()
    if not os.path.exists(path): return
    try:
        img=ImageReader(path); iw,ih=img.getSize(); scale=min(size/iw,size/ih)
        dw,dh=iw*scale,ih*scale
        c.setFillColor(colors.white); c.circle(cx,cy,size*.56,fill=1,stroke=0)
        c.drawImage(img,cx-dw/2,cy-dh/2,dw,dh,mask="auto",preserveAspectRatio=True)
    except Exception: pass

def _draw_photo(c,photo_path):
    c.setStrokeColor(GREEN); c.setLineWidth(5); c.circle(125,1100,78,fill=0,stroke=1)
    if photo_path and os.path.exists(photo_path):
        try:
            img=ImageReader(photo_path); iw,ih=img.getSize(); box=144
            scale=max(box/iw,box/ih); dw,dh=iw*scale,ih*scale
            c.saveState(); p=c.beginPath(); p.circle(125,1100,70); c.clipPath(p,stroke=0,fill=0)
            c.drawImage(img,125-dw/2,1100-dh/2,dw,dh,mask="auto"); c.restoreState(); return
        except Exception: pass
    c.setFillColor(colors.white); c.circle(125,1100,70,fill=1,stroke=0)

def generate_business_card(data,photo_path=None,output_path=None):
    if output_path is None:
        fd,output_path=tempfile.mkstemp(prefix="greenru_card_",suffix=".pdf"); os.close(fd)
    c=canvas.Canvas(output_path,pagesize=(W,H)); c.setTitle("GREENRU CLUB electronic business card")
    c.setFillColor(LIGHT); c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(colors.HexColor("#E9F4DF")); c.circle(640,1130,250,fill=1,stroke=0)
    c.setFillColor(colors.HexColor("#E1F0D8")); c.circle(80,920,210,fill=1,stroke=0)
    _draw_watermark(c)
    c.setFillColor(GREEN); c.rect(0,0,W,175,fill=1,stroke=0)

    _draw_photo(c,photo_path)
    c.setFillColor(GREEN); c.setFont(FONT_BOLD,12); c.drawString(48,1000,"PEOPLE  |  PRODUCTS  |  OPPORTUNITIES")
    c.setFont(FONT,11); c.drawString(48,980,"A BETTER TOMORROW")

    # QR is aligned with the partner photo and carries the only full-colour logo.
    qr=qrcode.QRCode(version=None,box_size=7,border=2); qr.add_data(ECOSYSTEM_URL); qr.make(fit=True)
    qr_img=qr.make_image(fill_color="black",back_color="white").convert("RGB")
    bio=io.BytesIO(); qr_img.save(bio,format="PNG"); bio.seek(0)
    c.setFillColor(colors.white); c.roundRect(475,965,205,260,18,fill=1,stroke=0)
    c.drawImage(ImageReader(bio),493,1030,169,169)
    _draw_qr_logo(c,577.5,1114.5,54)
    c.setFillColor(GREEN); c.setFont(FONT_BOLD,14); c.drawCentredString(577,1005,CLUB_NAME)
    c.setFont(FONT,10); c.drawCentredString(577,984,"СКАНИРУЙ QR-КОД")
    c.linkURL(ECOSYSTEM_URL,(475,965,680,1225),relative=0)

    name=(data.get("name") or "Партнёр Greenleaf").strip()
    c.setFillColor(DARK); _fit(c,name,48,895,400,39,FONT_BOLD,20)
    c.setFillColor(GREEN); c.setFont(FONT_BOLD,20); c.drawString(48,850,"ПАРТНЁР КОРПОРАЦИИ"); c.drawString(48,820,"GREENLEAF")
    c.setFont(FONT,13); c.drawString(48,775,"ЛЮДИ • ПРОДУКТЫ • ВОЗМОЖНОСТИ • БУДУЩЕЕ")

    phone=(data.get("phone") or "").strip()
    c.setFillColor(colors.white); c.roundRect(48,650,624,82,16,fill=1,stroke=0)
    c.setFillColor(GREEN); c.setFont(FONT_BOLD,11); c.drawString(78,705,"ТЕЛЕФОН")
    c.setFillColor(DARK); _fit(c,phone,78,672,560,25,FONT_BOLD,14)
    if phone: c.linkURL("tel:"+phone.replace(" ",""),(48,650,672,732),relative=0)

    telegram=(data.get("telegram") or "").strip(); whatsapp=(data.get("whatsapp") or "").strip()
    email=(data.get("email") or "").strip(); max_value=(data.get("max") or "").strip(); instagram=(data.get("instagram") or "").strip()
    _button(c,48,535,198,84,"TELEGRAM",_short_social(telegram,"telegram"),_telegram_url(telegram),colors.HexColor("#168CD8"))
    _button(c,261,535,198,84,"WHATSAPP",whatsapp,_whatsapp_url(whatsapp),colors.HexColor("#12A85B"))
    _button(c,474,535,198,84,"E-MAIL",email,"mailto:"+email if email else "",GREEN)
    _button(c,48,430,305,82,"MAX",_short_social(max_value,"max"),_max_url(max_value),colors.HexColor("#335C67"))
    _button(c,367,430,305,82,"INSTAGRAM",_short_social(instagram,"instagram"),_instagram_url(instagram),colors.HexColor("#B23A78"))

    c.setFillColor(GREEN); c.setFont(FONT_BOLD,16); c.drawCentredString(W/2,355,"НАШИ ЦЕННОСТИ")
    c.setFont(FONT_BOLD,13)
    for x,t in [(120,"ЛЮДИ"),(280,"ПРОДУКТЫ"),(445,"ВОЗМОЖНОСТИ"),(610,"БУДУЩЕЕ")]: c.drawCentredString(x,315,t)
    c.setFont(FONT,11); c.drawCentredString(W/2,265,CLUB_NAME+" — ВСЁ В ОДНОМ МЕСТЕ")
    c.linkURL(ECOSYSTEM_URL,(170,240,550,290),relative=0)

    c.setFillColor(colors.white); c.setFont(FONT_BOLD,18); c.drawString(48,120,"GREEN FUTURE TOGETHER")
    c.setFont(FONT,11); c.drawString(48,92,BRAND_NAME)
    c.drawRightString(672,92,"МЕЖДУНАРОДНЫЙ БИЗНЕС"); c.drawRightString(672,74,"С РЕАЛЬНЫМИ ВОЗМОЖНОСТЯМИ")
    c.save(); return output_path
