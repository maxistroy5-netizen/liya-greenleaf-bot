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
TEMPLATE_FILE = "ChatGPT Image 22 сент. 2026 г., 01_05_25.png"
BRAND_LOGO_FILE = "ChatGPT Image 17 сент. 2026 г._ 19_12_45.png"
W, H = 1024, 1536
DARK = colors.HexColor("#073B32")
GREEN = colors.HexColor("#075B3A")


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
BASE = os.path.dirname(os.path.abspath(__file__))


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
def _short(value,kind):
    value=(value or "").strip()
    if not value: return ""
    if not value.startswith(("http://","https://")): return value
    try:
        p=urlparse(value); path=p.path.strip("/")
        if kind in ("telegram","instagram","max") and path: return "@"+path.split("/")[0]
        return value
    except Exception: return value


def _fit(c,text,x,y,max_width,size=28,font=None,min_size=12):
    font=font or FONT_BOLD; text=str(text or ""); s=size
    while s>min_size and c.stringWidth(text,font,s)>max_width: s-=1
    c.setFont(font,s); c.drawString(x,y,text)


def _cover_image(c,path,x,y,w,h,clip_circle=False):
    if not path or not os.path.exists(path): return
    try:
        img=ImageReader(path); iw,ih=img.getSize(); scale=max(w/iw,h/ih); dw,dh=iw*scale,ih*scale
        c.saveState()
        if clip_circle:
            p=c.beginPath(); p.circle(x+w/2,y+h/2,min(w,h)/2); c.clipPath(p,stroke=0,fill=0)
        else:
            p=c.beginPath(); p.rect(x,y,w,h); c.clipPath(p,stroke=0,fill=0)
        c.drawImage(img,x+(w-dw)/2,y+(h-dh)/2,dw,dh,mask="auto")
        c.restoreState()
    except Exception: pass


def _draw_logo(c,cx,cy,size):
    path=os.path.join(BASE,BRAND_LOGO_FILE)
    if not os.path.exists(path): return
    c.setFillColor(colors.white); c.circle(cx,cy,size*.58,fill=1,stroke=0)
    _cover_image(c,path,cx-size/2,cy-size/2,size,size,True)


def generate_business_card(data,photo_path=None,output_path=None):
    if output_path is None:
        fd,output_path=tempfile.mkstemp(prefix="greenru_card_",suffix=".pdf"); os.close(fd)
    c=canvas.Canvas(output_path,pagesize=(W,H)); c.setTitle("GREENRU CLUB electronic business card")

    # Approved design is a single immutable master image. The generator only adds personal data and links.
    template=os.path.join(BASE,TEMPLATE_FILE)
    if os.path.exists(template):
        c.drawImage(ImageReader(template),0,0,W,H,mask="auto",preserveAspectRatio=False)
    else:
        c.setFillColor(colors.HexColor("#F7FBF4")); c.rect(0,0,W,H,fill=1,stroke=0)

    # Partner photo — exact circular placeholder in the approved template.
    _cover_image(c,photo_path,72,1054,350,350,True)

    # Real QR replaces the visual sample in the template and always points to GREENRU CLUB.
    qr=qrcode.QRCode(version=None,box_size=8,border=2,error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(ECOSYSTEM_URL); qr.make(fit=True)
    qr_img=qr.make_image(fill_color="black",back_color="white").convert("RGB")
    bio=io.BytesIO(); qr_img.save(bio,format="PNG"); bio.seek(0)
    c.setFillColor(colors.white); c.roundRect(744,1134,230,300,22,fill=1,stroke=0)
    c.drawImage(ImageReader(bio),765,1221,188,188)
    _draw_logo(c,859,1315,62)
    c.setFillColor(DARK); c.setFont(FONT_BOLD,18); c.drawCentredString(859,1194,"GREENRU💚CLUB")
    c.setFont(FONT,12); c.drawCentredString(859,1171,"СКАНИРУЙ QR-КОД")
    c.setFont(FONT_BOLD,13); c.drawCentredString(859,1148,"ПЕРЕЙТИ В КЛУБ →")
    c.linkURL(ECOSYSTEM_URL,(744,1134,974,1434),relative=0)

    # Personal identity area. Cover the placeholder text before writing real data.
    c.setFillColor(colors.Color(0.97,0.99,0.96,alpha=0.93)); c.roundRect(62,804,610,190,12,fill=1,stroke=0)
    name=(data.get("name") or "Партнёр Greenleaf").strip()
    c.setFillColor(DARK); _fit(c,name,78,918,565,44,FONT_BOLD,23)
    c.setStrokeColor(colors.HexColor("#C6A64A")); c.setLineWidth(2); c.line(78,897,168,897)
    c.setFillColor(GREEN); c.setFont(FONT,24); c.drawString(78,852,"ПАРТНЁР КОРПОРАЦИИ")
    c.setFont(FONT_BOLD,26); c.drawString(78,814,"GREENLEAF")

    phone=(data.get("phone") or "").strip(); telegram=(data.get("telegram") or "").strip(); whatsapp=(data.get("whatsapp") or "").strip(); max_value=(data.get("max") or "").strip(); instagram=(data.get("instagram") or "").strip(); email=(data.get("email") or "").strip()

    # White inner zones preserve the approved icons and borders while replacing placeholder copy.
    fields=[
        (190,663,260,54,"ТЕЛЕФОН",phone,"tel:"+phone.replace(" ","") if phone else ""),
        (665,663,260,54,"WHATSAPP",whatsapp,_whatsapp_url(whatsapp)),
        (190,554,260,54,"TELEGRAM",_short(telegram,"telegram"),_telegram_url(telegram)),
        (665,554,260,54,"MAX",_short(max_value,"max"),_max_url(max_value)),
        (190,446,260,54,"INSTAGRAM",_short(instagram,"instagram"),_instagram_url(instagram)),
        (665,446,260,54,"E-MAIL",email,"mailto:"+email if email else ""),
    ]
    for x,y,w,h,title,value,url in fields:
        c.setFillColor(colors.white); c.rect(x,y,w,h,fill=1,stroke=0)
        c.setFillColor(DARK); c.setFont(FONT_BOLD,15); c.drawString(x,y+33,title)
        _fit(c,value,x,y+7,w-8,18,FONT,10)
        if url: c.linkURL(url,(x-120,y-20,x+w+45,y+h+25),relative=0)

    # Club badge remains visually part of the master and is also clickable.
    c.linkURL(ECOSYSTEM_URL,(260,260,765,390),relative=0)
    c.save(); return output_path
