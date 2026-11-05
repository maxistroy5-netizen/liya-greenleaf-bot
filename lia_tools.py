"""Private, isolated material workflow; contact data never goes to the language model."""
import io
import logging
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from lia_materials import (SUPPORTED, FIELDS, words, validate, contact_url,
                           business_card, invitations, lesson_pdf, png_from_pdf)

LOG=logging.getLogger(__name__)
TOOL_LABELS={'ru':'🧰 Инструменты','uz':'🧰 Vositalar','tg':'🧰 Воситаҳо','ky':'🧰 Куралдар',
             'tr':'🧰 Araçlar','az':'🧰 Alətlər','en':'🧰 Tools','fr':'🧰 Outils','de':'🧰 Werkzeuge'}


def buttons(items):
    return InlineKeyboardMarkup([[InlineKeyboardButton(label,callback_data=payload)] for label,payload in items])


def controls(code,skip=False):
    w=words(code);items=[]
    if skip:items.append((w['skip'],'tool:skip'))
    items.append((w['cancel'],'tool:cancel'))
    return buttons(items)


async def send_document(message,data,filename,**kwargs):
    stream=io.BytesIO(data);stream.name=filename
    await message.reply_document(document=stream,filename=filename,**kwargs)


async def prompt(message,flow):
    w=words(flow['language']);field=flow.get('field')
    if field=='photo':body=w['photo']
    elif field=='recipient':body=w['recipient']
    elif field=='sender':body=w['sender_prompt']
    elif field=='event':body=w['event']
    elif field=='name':body=w['required']
    elif field=='max':body=w['max_prompt']
    else:body=w['prompt'].format(field=w[field])
    await message.reply_text(body,reply_markup=controls(flow['language'],field!='name' and field!='recipient'))


async def preview_card(message,flow):
    w=words(flow['language'])
    body='\n'.join(f'{w[k]}: {v}' for k,v in flow['data'].items() if v)
    await message.reply_text(w['ready']+'\n\n'+body,reply_markup=buttons([
        (w['create'],'tool:create'),(w['restart'],'tool:card'),(w['cancel'],'tool:cancel')]))
    flow['field']='confirm'


async def advance(message,flow,value):
    field=flow['field'];code=flow['language'];w=words(code)
    if field in FIELDS:
        value=validate(field,value)
        if field!='name' and value and not contact_url(field,value):
            raise ValueError('Contact cannot be linked')
        flow['data'][field]=value
        idx=FIELDS.index(field)+1
        flow['field']=FIELDS[idx] if idx<len(FIELDS) else 'photo'
        return await prompt(message,flow)
    if field=='photo':return await preview_card(message,flow)
    if field=='recipient':
        flow['recipient']=validate('name',value);flow['field']='sender'
        return await prompt(message,flow)
    if field=='sender':
        flow['sender']=validate('name',value) if value else '';flow['field']='event'
        return await prompt(message,flow)
    if field=='event':
        pdfs=await asyncio.to_thread(invitations,code,flow['recipient'],flow.get('sender',''),value)
        for i,pdf in enumerate(pdfs,1):await send_document(message,pdf,f'LIA_invitation_{code}_{i}.pdf')
        flow.clear()
        return
    await preview_card(message,flow)


async def handle_callback(update,context,code):
    payload=update.callback_query.data
    if not payload.startswith('tool:'):return False
    message=update.effective_message
    if code not in SUPPORTED:
        await message.reply_text(words('ru')['unavailable']+'\n\nEnglish: PDF materials are currently available in Russian and Uzbek only.')
        return True
    w=words(code)
    flow=context.user_data.get('material_flow')
    if flow and flow.get('language')!=code:
        context.user_data.pop('material_flow',None);flow=None
    try:
        if payload in ('tool:menu','tool:cancel'):
            context.user_data.pop('material_flow',None)
            context.user_data['surface']='dialogue'
            await message.reply_text(w['tools'],reply_markup=buttons([(w['card'],'tool:card'),(w['steps'],'tool:steps'),(w['home'],'nav:home')]))
        elif payload=='tool:card':
            flow={'language':code,'kind':'card','field':'name','data':{}}
            context.user_data['material_flow']=flow;context.user_data['surface']='tools'
            await prompt(message,flow)
        elif payload=='tool:steps':
            # Sender is collected explicitly; never infer another person's name from the chat.
            flow={'language':code,'kind':'steps','field':'recipient','sender':''}
            context.user_data['material_flow']=flow;context.user_data['surface']='tools'
            await prompt(message,flow)
        elif payload=='tool:skip' and flow and flow.get('field') not in ('name','recipient','confirm'):
            await advance(message,flow,'')
        elif payload=='tool:create' and flow and flow.get('field')=='confirm':
            pdf=await asyncio.to_thread(business_card,code,flow['data'],flow.get('photo'))
            await send_document(
                message, pdf, f'LIA_card_{code}.pdf',
                reply_markup=buttons([(w['steps'], 'tool:steps')]),
            )
            context.user_data.pop('material_flow',None)
        elif payload=='tool:lessons':
            context.user_data.pop('material_flow',None)
            await send_document(message,await asyncio.to_thread(lesson_pdf,code),f'LIA_8_lessons_{code}.pdf')
        elif payload.startswith('tool:lesson:'):
            lesson_id=payload.removeprefix('tool:lesson:')
            if lesson_id not in {str(i) for i in range(1,9)}:return True
            context.user_data.pop('material_flow',None)
            pdf=await asyncio.to_thread(lesson_pdf,code,lesson_id)
            await send_document(message,pdf,f'LIA_lesson_{code}_{lesson_id}.pdf')
            png=await asyncio.to_thread(png_from_pdf,pdf)
            await send_document(message,png,f'LIA_lesson_{code}_{lesson_id}.png')
    except Exception as exc:
        LOG.warning('Material generation failed: %s',type(exc).__name__)
        await message.reply_text(w['build_error'],reply_markup=controls(code))
    return True


async def handle_message(update,context,code):
    flow=context.user_data.get('material_flow')
    if not flow:
        context.user_data.pop('material_flow',None)
        return False
    message=update.effective_message
    if flow.get('language')!=code:
        context.user_data.pop('material_flow',None);return False
    try:
        if flow['field']=='photo' and getattr(message,'photo',None):
            photo=message.photo[-1]
            if photo.file_size and photo.file_size>10*1024*1024:raise ValueError('Photo size limit')
            file=await context.bot.get_file(photo.file_id)
            flow['photo']=bytes(await file.download_as_bytearray())
            await preview_card(message,flow)
        elif flow['field']=='photo':
            await prompt(message,flow)
        elif getattr(message,'text',None):
            await advance(message,flow,message.text)
        else:await prompt(message,flow)
    except ValueError:
        if flow['field'] == 'max':
            await prompt(message, flow)
            return True
        await message.reply_text(words(code)['invalid'],reply_markup=controls(code,flow['field'] not in ('name','recipient','confirm')))
    except Exception as exc:
        LOG.warning('Material input failed: %s',type(exc).__name__)
        await message.reply_text(words(code)['build_error'],reply_markup=controls(code))
    return True
