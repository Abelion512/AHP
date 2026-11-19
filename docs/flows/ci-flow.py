from PIL import Image, ImageDraw
import os

from _font import BOLD, REG, font

# Regenerates docs/assets/ci-flow.png. Needs Pillow >= 10.1
# (pip install 'pillow>=10.1'). Run from anywhere: python3 docs/flows/ci-flow.py

W, H = 1500, 860
im = Image.new("RGB", (W, H), "#0f1420"); d = ImageDraw.Draw(im)
t = font(BOLD, 34); b = font(BOLD, 22); s = font(REG, 19)
G = "#9fb0cc"
d.text((40, 26), "How it works: checks on a pull request", font=t, fill="#ffffff")
d.text((40, 74), "A new commit starts ci plus the title and body checks. A title edit starts the title and body checks, not ci or the labeler.", font=s, fill=G)

def box(x, y, w, h, title, lines, col):
    d.rounded_rectangle((x, y, x + w, y + h), radius=16, fill="#18202f", outline=col, width=3)
    d.text((x + 18, y + 14), title, font=b, fill=col)
    for i, l in enumerate(lines): d.text((x + 18, y + 50 + i * 27), l, font=s, fill="#dbe4f5")

def line(*p): d.line(p, fill=G, width=4)
def head(x, y): d.polygon([(x, y), (x - 14, y - 9), (x - 14, y + 9)], fill=G)

d.text((40, 118), "A. New commit pushed to the PR branch", font=b, fill="#6ea8ff")
box(40, 160, 240, 100, "Push to PR", ["New commit on", "the PR branch"], "#6ea8ff")
# Both checks start on synchronize. The ci push workflow is main-only.
line(280, 210, 320, 210); line(320, 210, 360, 210); head(360, 210)
line(320, 210, 320, 355); line(320, 355, 360, 355); head(360, 355)
box(360, 160, 420, 100, "ci + e2e (PR runs)", ["Plugin matrix, e2e, secret scan.", "No cache added."], "#7ee0a1")
box(360, 300, 420, 110, "PR title + body checks", ["Separate workflows; read title/body.", "Both run on a new commit."], "#7ee0a1")
box(850, 160, 610, 150, "Older ci run cancelled", ["Per PR, pull_request runs only.", "When a newer commit arrives, the older ci", "run of the same PR is cancelled."], "#ff8a8a")

yb = 570
d.text((40, yb - 42), "B. PR title edited, no new commit", font=b, fill="#6ea8ff")
box(40, yb, 240, 100, "Edit title", ["On the PR page"], "#6ea8ff")
box(360, yb, 420, 110, "PR title + body checks", ["Separate workflows; read title/body.", "ci and labeler do not start."], "#7ee0a1")
line(280, yb + 50, 320, yb + 50); line(320, yb + 50, 360, yb + 50); head(360, yb + 50)

box(850, 350, 610, 230, "Never cancelled", ["For ci: push to main, scheduled and manual", "runs each have their own run group.", "A ci pull_request run is cancelled only by a", "newer ci pull_request run of the same PR.", "No merge, deploy or branch rule change."], "#c3a6ff")
d.text((40, 800), "The path labeler also runs on open/synchronize; it is not a CI gate.", font=s, fill="#e2e8f0")
im.save(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "ci-flow.png")))
