from PIL import Image, ImageDraw, ImageFont
import os

# Regenerates docs/assets/ci-flow.png. Needs Pillow (pip install pillow).
# Run from anywhere: python3 docs/flows/ci-flow.py
def font(names,size):
    for n in names:
        try: return ImageFont.truetype(n,size)
        except OSError: pass
    try: return ImageFont.load_default(size)
    except TypeError: return ImageFont.load_default()  # Pillow < 10.1 has no size argument

DEJAVU="/usr/share/fonts/truetype/dejavu/"
MAC="/System/Library/Fonts/Supplemental/"
REG=["DejaVuSans.ttf",DEJAVU+"DejaVuSans.ttf","Arial.ttf",MAC+"Arial.ttf","C:/Windows/Fonts/arial.ttf"]
BOLD=["DejaVuSans-Bold.ttf",DEJAVU+"DejaVuSans-Bold.ttf","Arial Bold.ttf",MAC+"Arial Bold.ttf","C:/Windows/Fonts/arialbd.ttf"]

W,H=1500,820
im=Image.new("RGB",(W,H),"#0f1420"); d=ImageDraw.Draw(im)
t=font(BOLD,34); b=font(BOLD,22); s=font(REG,19)
G="#9fb0cc"
d.text((40,26),"How it works: checks on a pull request",font=t,fill="#ffffff")
d.text((40,74),"A new commit starts the ci pull_request run and the PR title check. A title edit starts only the title check.",font=s,fill=G)

def box(x,y,w,h,title,lines,col):
    d.rounded_rectangle((x,y,x+w,y+h),radius=16,fill="#18202f",outline=col,width=3)
    d.text((x+18,y+14),title,font=b,fill=col)
    for i,l in enumerate(lines): d.text((x+18,y+50+i*27),l,font=s,fill="#dbe4f5")
def line(*p): d.line(p,fill=G,width=4)
def head(x,y): d.polygon([(x,y),(x-14,y-9),(x-14,y+9)],fill=G)

d.text((40,118),"A. New commit pushed to the PR branch",font=b,fill="#6ea8ff")
box(40,160,240,100,"Push to PR",["New commit on","the PR branch"],"#6ea8ff")
# Both checks start on synchronize. The ci push workflow is main-only.
line(280,210,320,210); line(320,210,360,210); head(360,210)
line(320,210,320,340); line(320,340,360,340); head(360,340)
box(360,160,420,100,"ci (pull_request run)",["Plugin matrix, e2e, secret scan.","No cache added."],"#7ee0a1")
box(360,300,420,80,"PR title check",["Runs in parallel, reads the title"],"#7ee0a1")

box(850,160,610,150,"Older run cancelled",["Per workflow, per PR, pull_request runs only.","When a newer commit arrives, the older run of","the same workflow on the same PR is cancelled."],"#ff8a8a")

yb=530
d.text((40,yb-42),"B. PR title edited, no new commit",font=b,fill="#6ea8ff")
box(40,yb,240,80,"Edit title",["On the PR page"],"#6ea8ff")
box(360,yb,420,80,"PR title check only",["Other workflows do not start."],"#7ee0a1")
line(280,yb+40,320,yb+40); line(320,yb+40,360,yb+40); head(360,yb+40)

box(850,350,610,230,"Never cancelled",["Push to main, scheduled and manual runs:","each has its own run group.","A pull_request run is cancelled only by a newer","pull_request run of the same PR.","No merge, deploy or branch rule change."],"#c3a6ff")
im.save(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","assets","ci-flow.png")))
