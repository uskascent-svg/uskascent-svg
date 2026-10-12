from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math

W, H = 960, 390
OUT = Path("assets/readme-terminal.gif")
FPS = 12
DURATION = 25.0
BG0, BG1 = (7, 19, 11), (2, 6, 4)
GREEN, WHITE, DIM, PALE = (77,255,145), (215,232,219), (131,161,140), (165,255,195)

def font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
    ]
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()

F = font(16)
FB = font(16, True)
FT = font(13, True)
FS = font(12)
# (baseline, text, color, start time)
lines = [
    (70, "$ whoami", GREEN, 0.15),
    (94, "Utkarsh Khairnar", WHITE, 0.95),
    (118, "Computer Engineering Student | Cybersecurity", WHITE, 2.2),
    (142, "Nashik, Maharashtra, India", DIM, 4.0),
    (166, "$ cat status.log", GREEN, 5.2),
    (190, "STATUS: Learning & Building", PALE, 6.0),
    (214, "Threat detection · Security automation · AI-assisted defense", GREEN, 7.7),
    (238, "SOC Analyst · Blue Team · Cloud · AI · Network Security", DIM, 10.7),
    (262, "$ ./career.sh --goal", GREEN, 13.0),
    (286, "→ SOC Analyst → Blue Team → Cloud & AI Security", GREEN, 14.0),
    (310, "Projects: ASCENT SAFETY · Phishing Detection · RAIL-EYE · e-Recycle · KumbhSathi", WHITE, 16.5),
]
def draw_frame(t):
    im = Image.new("RGB", (W,H))
    px = im.load()
    for y in range(H):
        q=y/H*0.5
        shade=tuple(round(BG0[k]*(1-q)+BG1[k]*q) for k in range(3))
        ImageDraw.Draw(im).line((0,y,W,y),fill=shade,width=1)
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((0,0,W-1,H-1), radius=15, outline=(41,74,52), width=2)
    d.rectangle((0,0,W,42), fill=(16,26,19))
    for x,c in [(23,(255,98,93)),(41,(255,192,77)),(59,(66,214,107))]:
        d.ellipse((x-5,16,x+5,26),fill=c)
    d.text((82,12),"ASCENT U3 / CYBER DEFENCE CONSOLE",font=FT,fill=PALE)
    d.text((934,14),"SAFE PROFILE SIMULATION",font=FS,fill=DIM,anchor="ra")
    d.line((0,42,W,42),fill=(32,56,42),width=1)
    cursor=None
    for y, text, color, start in lines:
        elapsed=t-start
        if elapsed <= 0:
            continue
        # Human-like medium speed with a slight natural variation, deterministic per character.
        count=0
        for i,ch in enumerate(text):
            delay=i*0.057 + (0.08*math.sin(i*1.71) if i else 0)
            if elapsed >= delay:
                count=i+1
            else:
                break
        shown=text[:count]
        use_font = FB if text.startswith("$") else F
        d.text((28,y-19),shown,font=use_font,fill=color)
        if count < len(text):
            cursor=(28 + d.textlength(shown,font=use_font), y-18)
            break
        cursor=(28+d.textlength(shown,font=use_font), y-18)
    # Cursor blinks at the current typing position; at rest it stays after the final prompt.
    if int(t*2)%2==0 and cursor:
        cx,cy=cursor
        d.rectangle((int(cx+2),int(cy),int(cx+11),int(cy+19)),fill=GREEN)
    d.text((48,355),"DETECT. PREVENT. PROTECT.",font=FS,fill=DIM)
    return im

frames=[]
for i in range(round(FPS*DURATION)):
    frames.append(draw_frame(i/FPS))
# Final short hold before looping back to the opening.
frames[-1].save(OUT, save_all=True, append_images=frames[1:], duration=round(1000/FPS), loop=0, optimize=True, disposal=2)
print(f"Wrote {OUT} with {len(frames)} frames at {FPS} fps")
