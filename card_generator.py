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

    # Clean master: only dynamic content is added here.
    _cover_image(c,photo_path,67,1052,350,350,True)

    # QR panel: cover only the template QR sample, keeping the designed panel around it.
    qr=qrcode.QRCode(version=None,box_size=8,border=2,error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(ECOSYSTEM_URL); qr.make(fit=True)
    qr_img=qr.make_image(fill_color="black",back_color="white").convert("RGB")
    bio=io.BytesIO(); qr_img.save(bio,format="PNG"); bio.seek(0)
    c.setFillColor(colors.white); c.rect(752,1130,214,214,fill=1,stroke=0)
    c.drawImage(ImageReader(bio),752,1130,214,214)
    _draw_logo(c,859,1237,68)
    c.linkURL(ECOSYSTEM_URL,(720,960,995,1380),relative=0)

    name=(data.get("name") or "Партнёр Greenleaf").strip()
    c.setFillColor(DARK); _fit(c,name,78,925,560,43,FONT_BOLD,23)

    phone=(data.get("phone") or "").strip(); telegram=(data.get("telegram") or "").strip(); whatsapp=(data.get("whatsapp") or "").strip(); max_value=(data.get("max") or "").strip(); instagram=(data.get("instagram") or "").strip(); email=(data.get("email") or "").strip()
    fields=[
        (145,651,315,70,"ТЕЛЕФОН",phone,"tel:"+phone.replace(" ","") if phone else ""),
        (620,651,315,70,"WHATSAPP",whatsapp,_whatsapp_url(whatsapp)),
        (145,543,315,70,"TELEGRAM",_short(telegram,"telegram"),_telegram_url(telegram)),
        (620,543,315,70,"MAX",_short(max_value,"max"),_max_url(max_value)),
        (145,435,315,70,"INSTAGRAM",_short(instagram,"instagram"),_instagram_url(instagram)),
        (620,435,315,70,"E-MAIL",email,"mailto:"+email if email else ""),
    ]
    for x,y,w,h,title,value,url in fields:
        c.setFillColor(DARK); c.setFont(FONT_BOLD,15); c.drawString(x,y+38,title)
        _fit(c,value,x,y+10,w-15,18,FONT,10)
        if url: c.linkURL(url,(x-95,y-16,x+w+42,y+h+20),relative=0)

    c.linkURL(ECOSYSTEM_URL,(260,260,770,390),relative=0)
    c.save(); return output_path
