"""Regenerate docs/assets/title-reference-change.png (the before/after diagram in PR #42).

Run from the repo root:  python docs/flows/title-reference-change.py
Needs Pillow and the DejaVu fonts. Edit the text lists below, then re-run.
"""
import os
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = '/usr/share/fonts/truetype/dejavu/'
OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'title-reference-change.png')

BEFORE = ['BEFORE', '- Our Plugin: Nebula', '- Tier Naming sets', '- Usage Rule', '',
          'Missing:', '  visible-name rule', '  example PR titles', '  images note']
AFTER = ['AFTER (same file)', 'Unchanged: Our Plugin,', '  Tier Naming, Usage Rule', '',
         'Added sections:', '  + Visible name vs id', '  + Example PR titles', '  + Images']


def main():
    im = Image.new('RGB', (1200, 520), 'white')
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT_DIR + 'DejaVuSans.ttf', 20)
    b = ImageFont.truetype(FONT_DIR + 'DejaVuSans-Bold.ttf', 22)
    d.text((30, 20), 'docs/title-reference.md: what changes (docs only)', font=b, fill='black')

    def box(x, lines, color):
        d.rectangle([x, 80, x + 470, 460], outline='black', fill=color, width=2)
        for i, line in enumerate(lines):
            d.text((x + 14, 92 + i * 28), line, font=f, fill='black')

    box(30, BEFORE, '#f4f4f4')
    box(700, AFTER, '#e6f6e6')
    d.line([(520, 270), (660, 270)], fill='black', width=6)
    d.polygon([(656, 252), (656, 288), (688, 270)], fill='black')
    im.save(OUT)


if __name__ == '__main__':
    main()
