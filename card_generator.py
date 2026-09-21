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
GREEN_2 = colors.HexColor("#0B7047")
GREEN_3 = colors.HexColor("#7CBF45")
DARK = colors.HexColor("#092E23")
LIGHT = colors.HexColor("#F7FAF4")
LINE = colors.HexColor("#DCEBDD")


def _register_fonts():
    candidates = [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
    ]
    for regular, bold in candidates:
        if os.path.exists(regular) and os.path.exists(bold):
            pdfmetrics.registerFont(TTFont("GLRegular", regular)); pdfmetrics.registerFont(TTFont("GLBold", bold))
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
def _soft_card(c,x,y,w,h,r=18):
    c.saveState(); c.setFillAlpha(.055); c.setFillColor(colors.black); c.roundRect(x+4,y-5,w,h,r,fill=1,stroke=0); c.restoreState()
    c.setFillColor(colors.white); c.setStrokeColor(LINE); c.setLineWidth(.8); c.roundRect(x,y,w,h,r,fill=1,stroke=1)
def _button(c,x,y,w,h,title,display,url,fill):
    c.saveState(); c.setFillAlpha(.06); c.setFillColor(colors.black); c.roundRect(x+3,y-4,w,h,16,fill=1,stroke=0); c.restoreState()
    c.setFillColor(fill); c.roundRect(x,y,w,h,16,fill=1,stroke=0)
    c.saveState(); c.setFillAlpha(.13); c.setFillColor(colors.white); c.roundRect(x+1,y+h-28,w-2,27,15,fill=1,stroke=0); c.restoreState()
    c.setFillColor(colors.white); c.setFont(FONT_BOLD,11); c.drawString(x+18,y+h-22,title)
    _fit(c,display,x+18,y+18,w-38,16,FONT,9)
    if url: c.linkURL(url,(x,y,x+w,y+h),relative=0)
def _logo_path(): return os.path.join(os.path.dirname(os.path.abspath(__file__)),BRAND_LOGO_FILE)
def _draw_watermark(c):
    path=_logo_path()
    if not os.path.exists(path): return
    try:
        img=ImageReader(path); iw,ih=img.getSize(); maxw,maxh=650,800; scale=min(maxw/iw,maxh/ih); dw,dh=iw*scale,ih*scale
        c.saveState(); c.setFillAlpha(.105); c.drawImage(img,(W-dw)/2,335+(820-dh)/2,dw,dh,mask="auto",preserveAspectRatio=True); c.restoreState()
    except Exception: pass
def _draw_leaf(c,x,y,s,alpha=.10,angle=0):
    c.saveState(); c.translate(x,y); c.rotate(angle); c.setFillAlpha(alpha); c.setFillColor(GREEN_3)
    p=c.beginPath(); p.moveTo(0,0); p.curveTo(s*.25,s*.72,s*.82,s*.78,s,0); p.curveTo(s*.75,-s*.30,s*.25,-s*.28,0,0); c.drawPath(p,fill=1,stroke=0)
    c.setStrokeAlpha(alpha*1.7); c.setStrokeColor(GREEN); c.setLineWidth(1); c.line(s*.08,0,s*.82,0); c.restoreState()
def _draw_background(c):
    c.setFillColor(LIGHT); c.rect(0,0,W,H,fill=1,stroke=0)
    c.saveState(); c.setFillAlpha(.60); c.setFillColor(colors.HexColor("#E7F2DC")); c.circle(660,1125,270,fill=1,stroke=0); c.setFillColor(colors.HexColor("#DDEED3")); c.circle(55,900,225,fill=1,stroke=0); c.restoreState()
    c.saveState(); c.setFillAlpha(.12); c.setFillColor(GREEN_3); c.circle(360,1040,250,fill=1,stroke=0); c.restoreState()
    _draw_leaf(c,28,1200,150,.08,-18); _draw_leaf(c,525,920,180,.07,150); _draw_leaf(c,35,360,165,.055,18); _draw_leaf(c,540,300,150,.055,160)
    _draw_watermark(c)
def _draw_qr_logo(c,cx,cy,size=54):
    path=_logo_path()
    if not os.path.exists(path): return
    try:
        img=ImageReader(path); iw,ih=img.getSize(); scale=min(size/iw,size/ih); dw,dh=iw*scale,ih*scale
        c.setFillColor(colors.white); c.circle(cx,cy,size*.58,fill=1,stroke=0); c.drawImage(img,cx-dw/2,cy-dh/2,dw,dh,mask="auto",preserveAspectRatio=True)
    except Exception: pass
def _draw_photo(c,photo_path):
    c.saveState(); c.setFillAlpha(.10); c.setFillColor(colors.black); c.circle(129,1095,81,fill=1,stroke=0); c.restoreState()
    c.setFillColor(colors.white); c.circle(125,1100,79,fill=1,stroke=0); c.setStrokeColor(GREEN); c.setLineWidth(4); c.circle(125,1100,76,fill=0,stroke=1)
    c.setStrokeColor(GREEN_3); c.setLineWidth(1.5); c.circle(125,1100,70,fill=0,stroke=1)
    if photo_path and os.path.exists(photo_path):
        try:
            img=ImageReader(photo_path); iw,ih=img.getSize(); box=136; scale=max(box/iw,box/ih); dw,dh=iw*scale,ih*scale
            c.saveState(); p=c.beginPath(); p.circle(125,1100,67); c.clipPath(p,stroke=0,fill=0); c.drawImage(img,125-dw/2,1100-dh/2,dw,dh,mask="auto"); c.restoreState()
        except Exception: pass

def generate_business_card(data,photo_path=None,output_path=None):
    if output_path is None:
        fd,output_path=tempfile.mkstemp(prefix="greenru_card_",suffix=".pdf"); os.close(fd)
    c=canvas.Canvas(output_path,pagesize=(W,H)); c.setTitle("GREENRU CLUB electronic business card")
    _draw_background(c)
    # Premium footer with a subtle top accent.
    c.setFillColor(GREEN); c.rect(0,0,W,175,fill=1,stroke=0); c.setFillColor(GREEN_3); c.rect(0,171,W,4,fill=1,stroke=0)
    _draw_photo(c,photo_path)

    # Brand lockup between photo and QR.
    c.setFillColor(GREEN); c.setFont(FONT_BOLD,22); c.drawCentredString(355,1112,"GREENLEAF")
    c.setFont(FONT,15); c.drawCentredString(355,1087,"Leaders | Москва")
    c.setStrokeColor(GREEN_3); c.setLineWidth(1.2); c.line(300,1075,410,1075)

    qr=qrcode.QRCode(version=None,box_size=7,border=2); qr.add_data(ECOSYSTEM_URL); qr.make(fit=True)
    qr_img=qr.make_image(fill_color="black",back_color="white").convert("RGB"); bio=io.BytesIO(); qr_img.save(bio,format="PNG"); bio.seek(0)
    _soft_card(c,475,945,205,280,20); c.drawImage(ImageReader(bio),493,1035,169,169); _draw_qr_logo(c,577.5,1119.5,54)
    c.setFillColor(GREEN); c.setFont(FONT_BOLD,14); c.drawCentredString(577,1008,CLUB_NAME); c.setFont(FONT,10); c.drawCentredString(577,988,"СКАНИРУЙ QR-КОД")
    c.setFillColor(GREEN_2); c.setFont(FONT_BOLD,10); c.drawCentredString(577,965,"ОТКРЫТЬ КЛУБ →"); c.setStrokeColor(GREEN_2); c.setLineWidth(.7); c.line(526,962,628,962)
    c.linkURL(ECOSYSTEM_URL,(500,950,655,978),relative=0); c.linkURL(ECOSYSTEM_URL,(475,1030,680,1225),relative=0)

    name=(data.get("name") or "Партнёр Greenleaf").strip(); c.setFillColor(DARK); _fit(c,name,48,895,400,39,FONT_BOLD,20)
    c.setFillColor(GREEN); c.setFont(FONT_BOLD,20); c.drawString(48,850,"ПАРТНЁР КОРПОРАЦИИ"); c.drawString(48,820,"GREENLEAF")
    c.setStrokeColor(GREEN_3); c.setLineWidth(2); c.line(48,797,155,797)

    phone=(data.get("phone") or "").strip(); _soft_card(c,48,650,624,82,16)
    c.setFillColor(GREEN); c.setFont(FONT_BOLD,11); c.drawString(78,705,"ТЕЛЕФОН"); c.setFillColor(DARK); _fit(c,phone,78,672,560,25,FONT_BOLD,14)
    if phone: c.linkURL("tel:"+phone.replace(" ",""),(48,650,672,732),relative=0)

    telegram=(data.get("telegram") or "").strip(); whatsapp=(data.get("whatsapp") or "").strip(); email=(data.get("email") or "").strip(); max_value=(data.get("max") or "").strip(); instagram=(data.get("instagram") or "").strip()
    _button(c,48,535,198,84,"TELEGRAM",_short_social(telegram,"telegram"),_telegram_url(telegram),colors.HexColor("#168CD8"))
    _button(c,261,535,198,84,"WHATSAPP",whatsapp,_whatsapp_url(whatsapp),colors.HexColor("#12A85B"))
    _button(c,474,535,198,84,"E-MAIL",email,"mailto:"+email if email else "",GREEN)
    _button(c,48,430,305,82,"MAX",_short_social(max_value,"max"),_max_url(max_value),colors.HexColor("#335C67"))
    _button(c,367,430,305,82,"INSTAGRAM",_short_social(instagram,"instagram"),_instagram_url(instagram),colors.HexColor("#B23A78"))

    # Branded ecosystem CTA, still airy and clickable.
    _soft_card(c,225,270,270,94,22); c.setFillColor(GREEN); c.setFont(FONT_BOLD,18); c.drawCentredString(W/2,326,CLUB_NAME); c.setFont(FONT,12); c.drawCentredString(W/2,299,"ВСЁ В ОДНОМ МЕСТЕ")
    c.setStrokeColor(GREEN_3); c.setLineWidth(1.2); c.line(292,288,428,288); c.linkURL(ECOSYSTEM_URL,(225,270,495,364),relative=0)

    c.setFillColor(colors.white); c.setFont(FONT_BOLD,18); c.drawString(48,120,"GREEN FUTURE TOGETHER"); c.setFont(FONT,11); c.drawString(48,92,BRAND_NAME)
    c.drawRightString(672,92,"МЕЖДУНАРОДНЫЙ БИЗНЕС"); c.drawRightString(672,74,"С РЕАЛЬНЫМИ ВОЗМОЖНОСТЯМИ")
    c.save(); return output_path
