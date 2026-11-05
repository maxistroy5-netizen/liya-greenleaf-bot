"""Offline export of existing lesson routes. Run with python -I. No bot/API calls."""
import asyncio,copy,importlib,json,pathlib,sys
from types import SimpleNamespace
if not sys.flags.isolated:
 raise SystemExit('Use python -I to prevent implicit runtime hooks')
BASE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from telegram.ext import ApplicationHandlerStop
for name in ['usercustomize','marketing_lesson5_mentor_fix','marketing_reorder','marketing_width_recovery','marketing_three_bonuses','marketing_income_growth','marketing_lesson_navigation']:
 importlib.import_module(name)
import usercustomize as uc
import marketing_lesson_navigation as nav
class Message:
 def __init__(self,text): self.text=text; self.output=[]
 async def reply_text(self,text,**kwargs): self.output.append(text)
 async def reply_photo(self,photo=None,caption='',**kwargs): self.output.append(caption)
async def send(text,state):
 msg=Message(text); context=SimpleNamespace(user_data=state)
 try: await uc.marketing_lesson_router(SimpleNamespace(message=msg),context)
 except ApplicationHandlerStop: pass
 return msg.output
async def main():
 lessons=[]
 ordinals=['первый','второй','третий','четвёртый','пятый','шестой','седьмой','восьмой']
 for i in range(1,9):
  state={}; out=await send(f'{i}️⃣ Урок {i}',state)
  assert out, i
  question=(await send(f'📝 Проверить {ordinals[i-1]} блок',state))[-1]
  quiz=[]
  for step in range(1,5):
   candidates=[]
   for letter in 'ABC':
    candidate=copy.deepcopy(state); replies=await send(letter,candidate)
    assert replies,(i,step,letter)
    candidates.append((letter,candidate,replies[-1]))
   good=[c for c in candidates if c[1]!=state]
   assert len(good)==1,(i,step,candidates)
   letter,new_state,reply=good[0]
   hint=next(c[2] for c in candidates if c[0]!=letter)
   quiz.append({'id':f'l{i}q{step}','text':question,'correct':letter,'hint':hint})
   state=new_state
   if state.get('marketing_lesson_stage','').endswith('_done'):
    completion=reply;break
   question=reply
  lessons.append({'id':str(i),'caption':out[0],'note':out[1], 'quiz':quiz,'completion':completion,'legacy_stage':nav.LESSONS[i]['stage']})
 result={'version':'legacy-2d51843-v1','language':'ru','status':'source-export','lessons':lessons}
 (BASE / 'course' / 'source_ru.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print([(x['id'],len(x['quiz'])) for x in lessons])
asyncio.run(main())
