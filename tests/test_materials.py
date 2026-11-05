import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pymupdf
from lia_materials import business_card, invitations, lesson_pdf, ECOSYSTEM_URL, png_from_pdf
from lia_tools import handle_message


def pdf(data):
    return pymupdf.open(stream=data, filetype='pdf')


class MaterialsTests(unittest.TestCase):
    def test_card_keeps_contacts_and_active_qr_target(self):
        with pdf(business_card('uz', {'name':'O‘tkir G‘ulomov','phone':'+12025550142','telegram':'@example','email':'demo@example.org'})) as doc:
            page=doc[0]; text=page.get_text()
            self.assertIn('O‘tkir G‘ulomov',text)
            self.assertIn('Greenleaf hamkori',text)
            self.assertEqual({l['uri'] for l in page.get_links()}, {ECOSYSTEM_URL,'tel:+12025550142','https://t.me/example','mailto:demo@example.org'})

    def test_invitations_keep_recipient_date_timezone_and_link(self):
        docs=invitations('uz','Dilorom','Anora','2026-12-05 14:00 UTC\nhttps://example.org/meeting')
        self.assertEqual(len(docs),3)
        for i, data in enumerate(docs,1):
            with pdf(data) as doc:
                text=doc[0].get_text()
                self.assertIn('Dilorom',text)
                self.assertIn('Anora',text)
                if i==3:
                    self.assertIn('2026-12-05 14:00 UTC',text)
                    self.assertEqual([l['uri'] for l in doc[0].get_links()], ['https://example.org/meeting'])
        with pdf(invitations('ru','Анна')[2]) as doc:
            self.assertNotIn('10:00',doc[0].get_text())
            self.assertFalse(doc[0].get_links())

    def test_lesson_exports_preserve_numbers_and_language(self):
        for code,heading in [('ru','Урок 3'),('uz','Dars 3')]:
            with pdf(lesson_pdf(code)) as doc:
                self.assertEqual(len(doc),8)
                self.assertIn(heading,doc[2].get_text())
                self.assertIn('88 $ × 70 ₽ × 0,95 = 5 852 ₽',' '.join(doc[2].get_text().split()))
            self.assertTrue(png_from_pdf(lesson_pdf(code,3)).startswith(b'\x89PNG'))
        with self.assertRaises(ValueError):lesson_pdf('tg')


class MaterialRoutingTests(unittest.IsolatedAsyncioTestCase):
    async def test_card_input_is_consumed_by_local_wizard(self):
        msg=SimpleNamespace(text='O‘tkir G‘ulomov',reply_text=AsyncMock())
        ctx=SimpleNamespace(user_data={'material_flow':{'language':'uz','kind':'card','field':'name','data':{}}})
        self.assertTrue(await handle_message(SimpleNamespace(effective_message=msg),ctx,'uz'))
        self.assertEqual(ctx.user_data['material_flow']['data']['name'],'O‘tkir G‘ulomov')
        self.assertIn('Telefon',msg.reply_text.call_args.args[0])
