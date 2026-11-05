"""Render test samples from controlled copy; no credentials or live Telegram calls."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lia_materials import business_card, invitations, lesson_pdf, png_from_pdf


def main(folder):
    folder.mkdir(parents=True,exist_ok=True)
    for code,name in [('ru','Анна Тестовая'),('uz','O‘tkir G‘ulomov')]:
        dest=folder/code;dest.mkdir(exist_ok=True)
        card=business_card(code,{'name':name,'phone':'+1 202 555 0142','telegram':'@demo','whatsapp':'+12025550142','max':'https://max.ru/demo','instagram':'@demo','email':'demo@example.org'})
        (dest/'card.pdf').write_bytes(card)
        for i,doc in enumerate(invitations(code,name,'LIA Demo','2026-12-05 · 14:00 UTC\nhttps://example.org/meeting'),1):
            (dest/f'invitation-{i}.pdf').write_bytes(doc)
        (dest/'lessons.pdf').write_bytes(lesson_pdf(code))
        for i in range(1,9):
            pdf=lesson_pdf(code,i)
            (dest/f'lesson-{i}.pdf').write_bytes(pdf)
            (dest/f'lesson-{i}.png').write_bytes(png_from_pdf(pdf))

if __name__=='__main__':
    main(Path(sys.argv[1]))
