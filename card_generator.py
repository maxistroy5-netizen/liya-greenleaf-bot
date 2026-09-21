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
TEMPLATE_FILE = "business_card_template.png.png"
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
    template=os.path.join(BASE,TEMPLATE_FILE)
    if os.path.exists(template):
        c.drawImage(ImageReader(template),0,0,W,H,mask="auto",preserveAspectRatio=False)
    else:
        c.setFillColor(colors.HexColor("#F7FBF4")); c.rect(0,0,W,H,fill=1,stroke=0)

    # Final template is 1024x1536. Photo is cropped into its exact circular opening.
    _cover_image(c,photo_path,63,1055,355,355,True)

    # Replace the template's sample QR with the real ecosystem QR.
    qr=qrcode.QRCode(version=None,box_size=8,border=2,error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(ECOSYSTEM_URL); qr.make(fit=True)
    qr_img=qr.make_image(fill_color="black",back_color="white").convert("RGB")
    bio=io.BytesIO(); qr_img.save(bio,format="PNG"); bio.seek(0)
    c.setFillColor(colors.white); c.roundRect(726,965,265,405,20,fill=1,stroke=0)
    c.drawImage(ImageReader(bio),748,1135,220,220)
    _draw_logo(c,858,1245,70)
    c.setFillColor(DARK); c.setFont(FONT_BOLD,20); c.drawCentredString(858,1108,"GREENRU💚CLUB")
    c.setFont(FONT,15); c.drawCentredString(858,1081,"СКАНИРУЙ QR-КОД")
    c.setFont(FONT,15); c.drawCentredString(858,1055,"ИЛИ")
    c.setFillColor(GREEN); c.roundRect(744,987,230,53,22,fill=1,stroke=0)
    c.setFillColor(colors.white); c.setFont(FONT_BOLD,15); c.drawCentredString(859,1006,"ПЕРЕЙТИ В КЛУБ →")
    c.linkURL(ECOSYSTEM_URL,(726,965,991,1370),relative=0)

    # Cover only placeholder copy, not the surrounding approved design.
    c.setFillColor(colors.Color(0.97,0.99,0.96,alpha=0.94)); c.rect(72,815,570,160,fill=1,stroke=0)
    name=(data.get("name") or "Партнёр Greenleaf").strip()
    c.setFillColor(DARK); _fit(c,name,76,925,555,43,FONT_BOLD,23)
    c.setStrokeColor(colors.HexColor("#C6A64A")); c.setLineWidth(2); c.line(76,900,166,900)
    c.setFillColor(GREEN); c.setFont(FONT,24); c.drawString(76,856,"ПАРТНЁР КОРПОРАЦИИ")
    c.setFont(FONT_BOLD,27); c.drawString(76,818,"GREENLEAF")

    phone=(data.get("phone") or "").strip(); telegram=(data.get("telegram") or "").strip(); whatsapp=(data.get("whatsapp") or "").strip(); max_value=(data.get("max") or "").strip(); instagram=(data.get("instagram") or "").strip(); email=(data.get("email") or "").strip()
    fields=[
        (188,653,260,55,"ТЕЛЕФОН",phone,"tel:"+phone.replace(" ","") if phone else ""),
        (666,653,260,55,"WHATSAPP",whatsapp,_whatsapp_url(whatsapp)),
        (188,544,260,55,"TELEGRAM",_short(telegram,"telegram"),_telegram_url(telegram)),
        (666,544,260,55,"MAX",_short(max_value,"max"),_max_url(max_value)),
        (188,435,260,55,"INSTAGRAM",_short(instagram,"instagram"),_instagram_url(instagram)),
        (666,435,260,55,"E-MAIL",email,"mailto:"+email if email else ""),
    ]
    for x,y,w,h,title,value,url in fields:
        c.setFillColor(colors.white); c.rect(x,y,w,h,fill=1,stroke=0)
        c.setFillColor(DARK); c.setFont(FONT_BOLD,15); c.drawString(x,y+34,title)
        _fit(c,value,x,y+8,w-8,18,FONT,10)
        if url: c.linkURL(url,(x-125,y-22,x+w+45,y+h+25),relative=0)

    c.linkURL(ECOSYSTEM_URL,(255,260,770,390),relative=0)
    c.save(); return output_path
