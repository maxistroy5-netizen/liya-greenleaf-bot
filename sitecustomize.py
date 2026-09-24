"""Runtime hooks for GREENLEAF business-card and 3-step invitation flows."""

import io
import os
import re
import tempfile
import time

try:
    import fitz
    from PIL import Image, ImageDraw, ImageFont
    from telegram import Message
    from telegram.ext import MessageHandler

    _original_reply_document = Message.reply_document
    _original_reply_text = Message.reply_text
    _original_message_handler_init = MessageHandler.__init__
    _sender_by_chat = {}
    _last_step_reply = {}

    def _font_path():
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
        for path in candidates:
            if os.path.exists(path): return path
        raise RuntimeError("Cyrillic TrueType font was not found on Render")

    def _recipient_from_text(text: str) -> str:
        match = re.search(r"(?:^|\n)([^\n,]{1,60}),\s*(?:привет|приглашаю)", text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _event_from_text(text: str):
        date_match = re.search(r"📅\s*([^\n]+)", text)
        time_match = re.search(r"🕙\s*([^\n]+)", text)
        if not date_match: date_match = re.search(r"\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b", text)
        if not time_match: time_match = re.search(r"\b(\d{1,2}:\d{2})\b", text)
        urls = re.findall(r"https?://[^\s<]+", text); zoom_url = ""
        for url in urls:
            if "zoom.us" in url: zoom_url = url.rstrip(".,;:!?)"); break
        return (date_match.group(1).strip() if date_match else "", time_match.group(1).strip() if time_match else "", zoom_url)

    def _safe_name(value: str) -> str:
        return re.sub(r"[^0-9A-Za-zА-Яа-яЁё_-]+", "_", value or "").strip("_") or "partner"

    def _fit_pil_font(draw, text, font_path, start_size, min_size, max_width):
        size = start_size
        while size > min_size:
            font = ImageFont.truetype(font_path, size); box = draw.textbbox((0,0), text, font=font)
            if box[2]-box[0] <= max_width: return font
            size -= 1
        return ImageFont.truetype(font_path, min_size)

    def _draw_centered(draw, text, font_path, box_xy, start_size, min_size, fill):
        left, top, right, bottom = box_xy; bw, bh = right-left, bottom-top
        font = _fit_pil_font(draw,text,font_path,start_size,min_size,int(bw*.88)); tb=draw.textbbox((0,0),text,font=font)
        tw,th=tb[2]-tb[0],tb[3]-tb[1]; x=left+(bw-tw)/2-tb[0]; y=top+(bh-th)/2-tb[1]
        draw.text((x,y),text,font=font,fill=fill)

    def _make_personalized_pdf(step:int, recipient:str, sender:str="", event_text:str="") -> str:
        source_path=f"{step} шаг.pdf"
        if not os.path.exists(source_path): raise FileNotFoundError(source_path)
        recipient=(recipient or "").strip(); sender=(sender or "").strip(); font_path=_font_path()
        src=fitz.open(source_path); src_page=src[0]; pix=src_page.get_pixmap(matrix=fitz.Matrix(2.0,2.0),alpha=False)
        image=Image.frombytes("RGB",(pix.width,pix.height),pix.samples); draw=ImageDraw.Draw(image); w,h=image.size; green=(20,77,46)
        if recipient:
            if step==1: field=(int(w*.143),int(h*.174),int(w*.319),int(h*.226))
            elif step==2: field=(int(w*.103),int(h*.178),int(w*.414),int(h*.230))
            elif step==3: field=(int(w*.047),int(h*.177),int(w*.299),int(h*.226))
            _draw_centered(draw,recipient,font_path,field,max(18,int(w*.018)),13,green)
        if step==2 and sender:
            sender_field=(int(w*.174),int(h*.724),int(w*.467),int(h*.766))
            _draw_centered(draw,sender,font_path,sender_field,max(16,int(w*.014)),11,green)
        zoom_url = ""
        if step==3:
            event_date,event_time,zoom_url=_event_from_text(event_text)
            white=(255,255,255)
            date_field=(int(w*.247),int(h*.447),int(w*.480),int(h*.480))
            time_field=(int(w*.260),int(h*.507),int(w*.476),int(h*.540))
            zoom_field=(int(w*.188),int(h*.812),int(w*.545),int(h*.854))
            for box in (date_field,time_field,zoom_field): draw.rectangle(box,fill=white)
            if event_date:
                clean_date=re.search(r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}",event_date)
                clean_date=clean_date.group(0) if clean_date else event_date
                _draw_centered(draw,clean_date,font_path,date_field,max(17,int(w*.014)),11,green)
            if event_time:
                clean_time=re.search(r"\d{1,2}:\d{2}",event_time)
                clean_time=clean_time.group(0) if clean_time else event_time
                _draw_centered(draw,clean_time,font_path,time_field,max(17,int(w*.014)),11,green)
            if zoom_url:
                _draw_centered(draw,"ПОДКЛЮЧИТЬСЯ К ZOOM",font_path,zoom_field,max(16,int(w*.013)),10,green)
        png_buffer=io.BytesIO(); image.save(png_buffer,format="PNG",compress_level=3); out_doc=fitz.open(); rect=src_page.rect
        out_page=out_doc.new_page(width=rect.width,height=rect.height); out_page.insert_image(out_page.rect,stream=png_buffer.getvalue())
        if step==3 and zoom_url:
            link_rect=fitz.Rect(rect.width*.188,rect.height*.812,rect.width*.545,rect.height*.854)
            out_page.insert_link({"kind":fitz.LINK_URI,"from":link_rect,"uri":zoom_url})
        output_path=os.path.join(tempfile.gettempdir(),f"GREENLEAF_Шаг_{step}_{_safe_name(recipient)}.pdf")
        out_doc.save(output_path,garbage=4,deflate=True); out_doc.close(); src.close(); return output_path

    def _telegram_sender_name(message):
        try:
            user=message.from_user
            return (user.full_name or "").strip() if user else ""
        except Exception: return ""

    async def _reply_document_with_greenleaf_followup(self,*args,**kwargs):
        result=await _original_reply_document(self,*args,**kwargs); filename=kwargs.get("filename") or ""
        if filename.startswith("GREENLEAF_") and filename.lower().endswith(".pdf") and "Шаг_" not in filename:
            stem=os.path.splitext(filename)[0]; sender=stem[len("GREENLEAF_"):].replace("_"," ").strip()
            if sender: _sender_by_chat[self.chat_id]=sender
        return result

    def _is_stray_step_reply(text:str)->bool:
        n=re.sub(r"\s+"," ",(text or "").strip().lower())
        stray_fragments=("переходим к шагу 2","готова перейти к шагу 2","готов перейти к шагу 2","в истории диалога нет","нет содержания шага 1","уточните, пожалуйста, какое обучение","уточните, пожалуйста, к какому обучению","какую тему или задание мы разбираем","какое обучение или задание вы проходите","что вы хотите узнать об эрике","что хотите узнать об эрике")
        return any(fragment in n for fragment in stray_fragments)

    def _add_yutta_to_step3(text: str) -> str:
        if "Ютта Гай" in text: return text
        trainer = "🎓 <b>Обучение от Ютты Гай</b> — ТОП-лидера нашей команды, доктора и клинического психолога."
        marker = "\n\nБудет возможность спокойно посмотреть"
        if marker in text: return text.replace(marker, "\n\n" + trainer + marker, 1)
        return text + "\n\n" + trainer

    def _is_duplicate_step(chat_id, step, recipient, text):
        now=time.monotonic(); normalized=re.sub(r"\s+"," ",(text or "").strip())
        key=(chat_id,step,(recipient or "").strip().lower(),normalized)
        previous=_last_step_reply.get(key); _last_step_reply[key]=now
        for old_key, ts in list(_last_step_reply.items()):
            if now-ts > 60: _last_step_reply.pop(old_key,None)
        return previous is not None and now-previous < 20

    async def _reply_text_with_invitation_pdf(self,text,*args,**kwargs):
        if isinstance(text,str) and _is_stray_step_reply(text):
            print(f"GREENLEAF suppressed stray step reply: {text[:120]!r}",flush=True); return None
        step=None
        if isinstance(text,str):
            if text.startswith("1️⃣ ПЕРВОЕ КАСАНИЕ"): step=1
            elif text.startswith("2️⃣ ВТОРОЕ КАСАНИЕ"): step=2
            elif text.startswith("3️⃣ ГОТОВОЕ ПРИГЛАШЕНИЕ"):
                step=3; text=_add_yutta_to_step3(text); kwargs.setdefault("parse_mode","HTML")
        if not step: return await _original_reply_text(self,text,*args,**kwargs)
        recipient=_recipient_from_text(text)
        if _is_duplicate_step(self.chat_id,step,recipient,text):
            print(f"GREENLEAF suppressed duplicate step={step} recipient={recipient!r}",flush=True); return None
        if step == 3:
            result = await _original_reply_text(self,text,*args,**kwargs); temp_pdf=None
            try:
                sender=_sender_by_chat.get(self.chat_id,"") or _telegram_sender_name(self)
                if sender: _sender_by_chat[self.chat_id]=sender
                temp_pdf=_make_personalized_pdf(step,recipient,sender,text)
                with open(temp_pdf,"rb") as document:
                    await _original_reply_document(self,document=document,filename=os.path.basename(temp_pdf),caption=f"💚 ШАГ {step} — персональный PDF для {recipient or 'приглашения'}.")
            except Exception as exc: print(f"GREENLEAF PDF PERSONALIZATION FAILED step={step}: {type(exc).__name__}: {exc}",flush=True)
            finally:
                if temp_pdf and os.path.exists(temp_pdf):
                    try: os.remove(temp_pdf)
                    except OSError: pass
            return result
        temp_pdf=None
        try:
            sender=_sender_by_chat.get(self.chat_id,"") or _telegram_sender_name(self)
            if sender: _sender_by_chat[self.chat_id]=sender
            temp_pdf=_make_personalized_pdf(step,recipient,sender,text)
            with open(temp_pdf,"rb") as document:
                await _original_reply_document(self,document=document,filename=os.path.basename(temp_pdf),caption=f"💚 ШАГ {step} — персональный PDF для {recipient or 'приглашения'}.")
        except Exception as exc:
            print(f"GREENLEAF PDF PERSONALIZATION FAILED step={step}: {type(exc).__name__}: {exc}",flush=True)
            await _original_reply_text(self,f"⚠️ PDF шага {step} сейчас не собрался, но текст приглашения готов.")
        finally:
            if temp_pdf and os.path.exists(temp_pdf):
                try: os.remove(temp_pdf)
                except OSError: pass
        return await _original_reply_text(self,text,*args,**kwargs)

    def _message_handler_init_with_fast_newcomer(self, filters, callback, block=True):
        if getattr(callback, "__name__", "") == "chat":
            original_callback = callback
            async def fast_newcomer_callback(update, context):
                text = ((update.message.text if update and update.message else "") or "").strip().lower()
                if context.user_data.get("mode") == "🚀 С чего начать":
                    if any(word in text for word in ("знакомлюсь", "знакомлю", "не партнер", "не партнёр", "пока знаком")):
                        context.user_data["newcomer_stage"] = "exploring"
                        await update.message.reply_text(
                            "💚 Отлично. Тогда начнём со знакомства, без перегруза.\n\nGreenleaf — это компания, с которой можно знакомиться в своём темпе: сначала понять саму компанию и продукцию, а уже потом — партнёрские возможности и маркетинг-план.\n\nВыбери, что посмотреть первым:\n🌿 О компании Greenleaf\n💚 Продукция и направления\n🌍 Возможности Greenleaf\n\nНажми нужную кнопку ниже 👇"
                        )
                        return
                    if any(word in text for word in ("уже партнер", "уже партнёр", "я партнер", "я партнёр")):
                        context.user_data["newcomer_stage"] = "partner"
                        await update.message.reply_text(
                            "💚 Отлично. Тогда пойдём как для нового партнёра — коротко и по шагам.\n\nПервое: не нужно учить всё сразу. Начни с понимания компании и продукции, затем разберём базовые понятия маркетинг-плана и простые ежедневные действия.\n\nС чего хочешь начать: с компании, продукции или маркетинг-плана?"
                        )
                        return
                return await original_callback(update, context)
            callback = fast_newcomer_callback
        return _original_message_handler_init(self, filters, callback, block=block)

    Message.reply_document=_reply_document_with_greenleaf_followup
    Message.reply_text=_reply_text_with_invitation_pdf
    MessageHandler.__init__=_message_handler_init_with_fast_newcomer
    print("GREENLEAF runtime hook v31 fast newcomer branch",flush=True)
except Exception as exc:
    print(f"GREENLEAF runtime hook not loaded: {type(exc).__name__}: {exc}",flush=True)
