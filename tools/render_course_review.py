"""Build a readable bilingual review from the checked course catalogs."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lia_course import load_catalog

def main():
    ru, uz = load_catalog('ru'), load_catalog('uz')
    lines = ['# Лия: уроки на русском и узбекском', '',
             'Черновик для проверки носителем языка. Рабочий бот не изменён.', '',
             'Восемь уроков, 22 вопроса. Предметные вопросы исходных примеров — course/README.md.', '']
    for a, b in zip(ru['lessons'], uz['lessons'], strict=True):
        lines += [f'## Урок {a["id"]}: {a["title"]}', '', '### Русский', '', a['body'], '',
                  '### O‘zbekcha', '', b['title'], '', b['body'], '', '### Вопросы и подсказки', '']
        for i, (q, translated) in enumerate(zip(a['quiz'], b['quiz'], strict=True), 1):
            lines += [f'**{i}. {q["prompt"]}**', '']
            lines += [f'{key}. {q["options"][key]}' for key in 'ABC']
            lines += ['', f'**{translated["prompt"]}**', '']
            lines += [f'{key}. {translated["options"][key]}' for key in 'ABC']
            lines += ['', 'Подсказка: ' + q['hint'], '', 'Yordam: ' + translated['hint'], '',
                      'Ключ для проверки: ' + q['correct'], '']
    (ROOT / 'COURSE_REVIEW_RU_UZ.md').write_text('\n'.join(lines), encoding='utf-8')

if __name__ == '__main__':
    main()
