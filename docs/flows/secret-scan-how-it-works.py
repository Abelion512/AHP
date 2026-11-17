from PIL import Image, ImageDraw, ImageFont
import math
import os

# Regenerates docs/assets/secret-scan-how-it-works.png.
# Needs Pillow (pip install pillow). Run from anywhere:
# python3 docs/flows/secret-scan-how-it-works.py
def font(names, size):
    for n in names:
        try: return ImageFont.truetype(n, size)
        except OSError: pass
    try: return ImageFont.load_default(size)
    except TypeError: return ImageFont.load_default()  # Pillow < 10.1

DEJAVU = "/usr/share/fonts/truetype/dejavu/"
MAC = "/System/Library/Fonts/Supplemental/"
REG = ["DejaVuSans.ttf", DEJAVU + "DejaVuSans.ttf", "Arial.ttf", MAC + "Arial.ttf", "C:/Windows/Fonts/arial.ttf"]
BOLD = ["DejaVuSans-Bold.ttf", DEJAVU + "DejaVuSans-Bold.ttf", "Arial Bold.ttf", MAC + "Arial Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"]

out = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "secret-scan-how-it-works.png"))
W, H = 1500, 640
im = Image.new("RGB", (W, H), "#0f1420")
d = ImageDraw.Draw(im)
t = font(BOLD, 34); b = font(BOLD, 22); s = font(REG, 19)
G = "#9fb0cc"
d.text((40, 26), "How it works: exact fingerprints in secret-scan", font=t, fill="#ffffff")
d.text((40, 74), "gitleaks still scans every commit. Only one exact, already-published synthetic fixture is ignored.", font=s, fill=G)

def box(x, y, w, h, title, lines, border="#3b82f6"):
    d.rounded_rectangle([x, y, x + w, y + h], 14, outline=border, width=3, fill="#161d2e")
    d.text((x + 18, y + 14), title, font=b, fill="#ffffff")
    for i, ln in enumerate(lines):
        d.text((x + 18, y + 52 + i * 28), ln, font=s, fill=G)

def arrow(x1, y1, x2, y2):
    d.line([x1, y1, x2, y2], fill="#64748b", width=3)
    ang = math.atan2(y2 - y1, x2 - x1)
    L = 12
    for da in (math.radians(150), math.radians(-150)):
        d.line([x2, y2, x2 + L * math.cos(ang + da), y2 + L * math.sin(ang + da)], fill="#64748b", width=3)

box(60, 240, 380, 150, "1. secret-scan runs", ["On every PR: checkout,", "gitleaks scans the full", "git history."], "#3b82f6")
box(540, 240, 400, 150, "2. Fingerprint check", ["commit + path + rule + line", "is compared to the exact", "entries in .gitleaksignore."], "#a855f7")
box(1020, 100, 430, 200, "3a. Exact match (on main)", ["The synthetic classifier test", "canary from the main-restore", "commit is already listed on main.", "This finding is ignored; other", "findings are still evaluated."], "#22c55e")
box(1020, 380, 430, 120, "3b. No match", ["Other detected findings", "remain failures."], "#ef4444")
arrow(440, 315, 540, 315)
arrow(940, 315, 1020, 200)
arrow(940, 315, 1020, 440)
d.text((60, 590), "Scope stays narrow: one fixture, one commit. No path- or rule-wide suppression.", font=s, fill="#e2e8f0")
im.save(out)
print("wrote", out)
