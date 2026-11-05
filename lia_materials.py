"""Localized test-only files. No production imports, API calls or stored contacts."""
import io
import json
import re
from pathlib import Path
from urllib.parse import urlsplit, quote
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.utils import ImageReader
import qrcode
import pymupdf as fitz

BASE = Path(__file__).resolve().parent
COPY = json.loads((BASE / 'materials/copy.json').read_text())
SUPPORTED = frozenset(COPY)
# Preserve the destination used by the existing card generator, independently of language.
ECOSYSTEM_URL = 'https://t.me/addlist/OlNIwOt0mnI2ZmI6'
FIELDS = ('name', 'phone', 'telegram', 'whatsapp', 'max', 'email', 'instagram')
GREEN = colors.HexColor('#123F35')
CREAM = colors.HexColor('#F6F7EF')
GOLD = colors.HexColor('#B39A60')


def words(code):
    if code not in SUPPORTED:
        raise ValueError('Material language unavailable')
    return COPY[code]


def fonts():
    regular = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    bold = regular.with_name('DejaVuSans-Bold.ttf')
    if not regular.exists() or not bold.exists():
        raise RuntimeError('Unicode fonts unavailable; refusing incomplete PDF')
    if 'LiaText' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('LiaText', str(regular)))
        pdfmetrics.registerFont(TTFont('LiaBold', str(bold)))


def validate(field, value):
    value = str(value).strip()
    if len(value) > (160 if field == 'name' else 300) or any(ord(c) < 32 for c in value):
        raise ValueError('Invalid contact')
    if field == 'name' and not value:
        raise ValueError('Name required')
    if '://' in value and urlsplit(value).scheme not in ('https', 'http'):
        raise ValueError('Invalid contact URL')
    return value


def contact_url(field, value):
    value = validate(field, value)
    if not value:
        return ''
    if field == 'phone':
        digits = re.sub(r'[^+0-9]', '', value)
        if len(re.sub(r'\D', '', digits)) < 5:
            return ''
        return 'tel:' + digits
    if field == 'email':
        return 'mailto:' + quote(value, safe='@.+') if re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value) else ''
    if field in ('telegram', 'whatsapp', 'max', 'instagram'):
        if value.startswith(('https://', 'http://')):
            p = urlsplit(value)
            if not p.netloc or p.username or p.password:
                raise ValueError('Invalid contact URL')
            return value
        if field == 'whatsapp':
            digits = re.sub(r'\D', '', value)
            return 'https://wa.me/' + digits if digits else ''
        if field == 'telegram' and re.fullmatch(r'\+?[0-9 ()-]+', value):
            return 'https://t.me/+' + re.sub(r'\D', '', value)
        if not re.fullmatch(r'@?[\w.\-]+', value):
            raise ValueError('Invalid contact handle')
        prefix = {'telegram': 'https://t.me/', 'instagram': 'https://instagram.com/', 'max': 'https://max.ru/'}[field]
        return prefix + quote(value.lstrip('@'))
    return ''


def paragraph(c, value, x, top, width, size=13, bold=False, color=GREEN, bottom=65):
    style = ParagraphStyle('lia', fontName='LiaBold' if bold else 'LiaText', fontSize=size,
                           leading=size*1.45, textColor=color, splitLongWords=True)
    content = escape(str(value)).replace('\n', '<br/>')
    p = Paragraph(content, style)
    _, height = p.wrap(width, 10000)
    if top - height < bottom:
        raise ValueError('Content exceeds page; layout must be reviewed')
    p.drawOn(c, x, top-height)
    return top-height-14


def frame(c, title, code, page=1, total=1):
    c.setFillColor(CREAM); c.rect(0, 0, 720, 1080, stroke=0, fill=1)
    c.setFillColor(GREEN); c.rect(0, 987, 720, 93, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont('LiaBold', 17); c.drawString(42, 1028, 'GREENLEAF  |  LIA')
    c.setFont('LiaText', 10); c.drawRightString(678, 1031, code.upper())
    y = paragraph(c, title, 42, 953, 636, 23, True)
    c.setStrokeColor(GOLD); c.line(42, y+2, 678, y+2)
    c.setFont('LiaText', 8); c.setFillColor(GREEN)
    c.drawString(42, 29, words(code)['source'])
    c.drawRightString(678, 29, f'{page}/{total}')
    return y-20


def png_from_pdf(pdf, page=0):
    with fitz.open(stream=pdf, filetype='pdf') as doc:
        return doc[page].get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False).tobytes('png')


def business_card(code, data, photo=None):
    w = words(code); fonts()
    data = {field: validate(field, data.get(field, '')) for field in FIELDS}
    stream = io.BytesIO(); c = canvas.Canvas(stream, pagesize=(720,1080))
    c.setTitle(f'Greenleaf | {w["card"]}')
    frame(c, w['motto'], code)
    if photo:
        image = ImageReader(io.BytesIO(photo)); iw, ih = image.getSize()
        if iw * ih > 40000000:
            raise ValueError('Photo too large')
        c.saveState(); p=c.beginPath(); p.circle(120, 792, 74); c.clipPath(p, stroke=0)
        scale = max(148/iw, 148/ih)
        c.drawImage(image,120-iw*scale/2,792-ih*scale/2,iw*scale,ih*scale,mask='auto');c.restoreState()
    else:
        c.setFillColor(GREEN); c.circle(120,792,74,stroke=0,fill=1)
        c.setFillColor(colors.white);c.setFont('LiaBold',36);c.drawCentredString(120,780,'LIA')
    paragraph(c, data['name'], 225, 848, 453, 25, True, bottom=688)
    paragraph(c, w['partner'], 225, 730, 453, 15)
    y=657
    for field in FIELDS[1:]:
        value=data[field]
        if not value: continue
        next_y=paragraph(c,w[field],42,y,160,11,True,bottom=270)
        bottom=paragraph(c,value,216,y,462,14,bottom=270)
        c.setStrokeColor(colors.HexColor('#D4DED1')); c.line(42,bottom+5,678,bottom+5)
        url=contact_url(field,value)
        if url:c.linkURL(url,(210,bottom+12,680,y+2),relative=0)
        y=min(next_y,bottom)-7
    qr=qrcode.make(ECOSYSTEM_URL); pic=io.BytesIO();qr.save(pic,format='PNG');pic.seek(0)
    c.drawImage(ImageReader(pic),42,82,174,174)
    c.linkURL(ECOSYSTEM_URL,(42,82,216,256),relative=0)
    paragraph(c,'GREENRU CLUB',246,231,432,20,True)
    paragraph(c,w['club'],246,186,432,15)
    c.linkURL(ECOSYSTEM_URL,(240,130,680,235),relative=0)
    c.save();return stream.getvalue()


def compact_zoom_invitation(event):
    """Keep participant-facing details from a copied Zoom invitation."""
    if '\n' not in event:
        return event

    labels = re.compile(
        r'^(?:Тема|Время|Идентификатор конференции|Код доступа|'
        r'Topic|Time|Meeting ID|Passcode):\s*.+$', re.IGNORECASE
    )
    details = [line.strip() for line in event.splitlines() if labels.fullmatch(line.strip())]
    if not details:
        return event

    for candidate in re.findall(r'https?://[^\s<>]+', event):
        url = candidate.rstrip('.,;!?)')
        parts = urlsplit(url)
        host = (parts.hostname or '').lower()
        if not any(host == domain or host.endswith('.' + domain)
                   for domain in ('zoom.us', 'zoom.com')):
            continue
        if re.fullmatch(r'/(?:j/[0-9]+|my/[^/]+)', parts.path.rstrip('/')):
            return '\n'.join([*details, url])
    return event


def invitations(code, recipient, sender='', event=''):
    w=words(code);fonts()
    recipient=validate('name',recipient);sender=validate('name',sender) if sender else ''
    event = compact_zoom_invitation(event)
    if len(event)>1800:raise ValueError('Event details too long')
    result=[]
    for i,(title,body) in enumerate(zip(w['step_titles'],w['step_bodies']),1):
        stream=io.BytesIO();c=canvas.Canvas(stream,pagesize=(720,1080))
        c.setTitle(f'{i} | {title}')
        y=frame(c,f'{i} | {title}',code)
        y=paragraph(c,body.format(recipient=recipient),42,y,636,19)
        if i==3:
            y=paragraph(c,w['details'],42,y-15,636,16,True)
            details=re.sub(r'https?://[^\s<>]+','',event).strip()
            if details or not event:
                y=paragraph(c,details or w['missing'],42,y,636,15)
            # Explicit user details only; no inferred date, time, speaker or default Zoom.
            for url in re.findall(r'https?://[^\s<>]+',event):
                url=url.rstrip('.,;!?)')
                if urlsplit(url).netloc:
                    top=y
                    y=paragraph(c,url,42,y,636,11)
                    c.linkURL(url,(42,y+12,678,top),relative=0)
        if sender:paragraph(c,w['sender']+': '+sender,42,min(y-25,260),636,14)
        if code!='ru':paragraph(c,w['draft'],42,80,636,9,bottom=40)
        c.save();result.append(stream.getvalue())
    return result


def lesson_pdf(code, lesson_id=None):
    w=words(code);fonts()
    catalog=json.loads((BASE/'course'/f'{code}.json').read_text())
    lessons=catalog['lessons']
    if lesson_id is not None:
        lessons=[x for x in lessons if x['id']==str(lesson_id)]
        if not lessons:raise ValueError('Unknown lesson')
    stream=io.BytesIO();c=canvas.Canvas(stream,pagesize=(720,1080))
    c.setTitle('LIA | '+w['lessons'])
    for page,item in enumerate(lessons,1):
        y=frame(c,f'{w["lesson"]} {item["id"]} | {item["title"]}',code,page,len(lessons))
        # Controlled text-course source, not an automatic rewrite of a raster slide.
        y=paragraph(c,item['body'],42,y,636,18)
        y=paragraph(c,w['check'],42,y-8,636,18,True)
        for q in item['quiz']:
            y=paragraph(c,q['prompt'],42,y,636,15,True)
            y=paragraph(c,'\n'.join(f'{k} - {v}' for k,v in q['options'].items()),52,y,626,14)
        paragraph(c,w['note'],42,min(y-8,138),636,10,bottom=68)
        if code!='ru':paragraph(c,w['draft'],42,57,636,8,bottom=38)
        c.showPage()
    c.save();return stream.getvalue()
