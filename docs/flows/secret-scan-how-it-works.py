from PIL import Image, ImageDraw, ImageFont
# Regenerates docs/assets/secret-scan-how-it-works.png. Run from the repo root: python3 docs/flows/secret-scan-how-it-works.py
out = "docs/assets/secret-scan-how-it-works.png"
W, H = 1500, 640
im = Image.new("RGB", (W, H), "#0f1420")
d = ImageDraw.Draw(im)
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
t = ImageFont.truetype(FB, 34); b = ImageFont.truetype(FB, 22); s = ImageFont.truetype(F, 19)
G = "#9fb0cc"
d.text((40, 26), "How it works: ignoring one known test fixture in secret-scan", font=t, fill="#ffffff")
d.text((40, 74), "gitleaks still scans every commit. Only one exact, already-published synthetic fixture is skipped.", font=s, fill=G)

def box(x, y, w, h, title, lines, border="#3b82f6"):
    d.rounded_rectangle([x, y, x + w, y + h], 14, outline=border, width=3, fill="#161d2e")
    d.text((x + 18, y + 14), title, font=b, fill="#ffffff")
    for i, ln in enumerate(lines):
        d.text((x + 18, y + 52 + i * 28), ln, font=s, fill=G)

def arrow(x1, y1, x2, y2):
    d.line([x1, y1, x2, y2], fill="#64748b", width=3)
    d.polygon([(x2, y2), (x2 - 10, y2 - 6), (x2 - 10, y2 + 6)], fill="#64748b")

box(60, 160, 420, 140, "1. secret-scan runs", ["On every PR: checkout (merge commit),", "gitleaks over the full git history."], "#3b82f6")
box(60, 380, 420, 170, "2. Fingerprint check", ["commit + path + rule + line", "must match .gitleaksignore", "exactly. Anything else is", "treated as a new finding."], "#a855f7")
box(600, 160, 430, 180, "3a. Exact match (this PR)", ["The synthetic classifier test canary", "from the main-restore commit is", "listed, so it is skipped and the", "scan passes."], "#22c55e")
box(600, 380, 430, 170, "3b. No match", ["Any other finding, including a real", "secret or the same string in a new", "commit or line, still fails the check."], "#ef4444")
box(1150, 250, 310, 180, "4. Result", ["Scope stays narrow:", "one fixture, one commit.", "No path- or rule-wide", "suppression."], "#eab308")
arrow(480, 230, 600, 230)
arrow(480, 465, 600, 465)
arrow(1030, 250, 1150, 320)
arrow(1030, 465, 1150, 350)
im.save(out)
print("wrote", out)
