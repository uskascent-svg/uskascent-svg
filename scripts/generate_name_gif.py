from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

W, H = 800, 190
BG = (13, 17, 23)
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
GLYPHS = {
"U":["10001","10001","10001","10001","10001","10001","01110"],
"T":["11111","00100","00100","00100","00100","00100","00100"],
"K":["10001","10010","10100","11000","10100","10010","10001"],
"A":["01110","10001","10001","11111","10001","10001","10001"],
"R":["11110","10001","10001","11110","10100","10010","10001"],
"S":["01111","10000","10000","01110","00001","00001","11110"],
"H":["10001","10001","10001","11111","10001","10001","10001"],
}
CELL, GAP, X0, Y0 = 10, 7, 24, 47
WORD = "UTKARSH"
ADV = 5 * CELL + GAP
steps = [(letter, col) for letter in range(len(WORD)) for col in range(5)]
frames, durations = [], []

for step in range(len(steps) + 1):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 7, W-9, H-8), radius=9, outline=(48,54,61))
    d.text((24, 18), "utkarsh@cloud:~$ figlet -f ansi_shadow UTKARSH", font=FONT, fill=(139,148,158))
    # offset shadow creates the terminal ANSI-shadow depth
    for shadow in (True, False):
        for row in range(7):
            for li, letter in enumerate(WORD):
                for col in range(5):
                    if li * 5 + col >= step or GLYPHS[letter][row][col] != "1":
                        continue
                    x, y = X0 + li*ADV + col*CELL, Y0 + row*CELL
                    if shadow:
                        d.rectangle((x+3,y+3,x+CELL,y+CELL), fill=(0,76,70))
                    else:
                        t = (li*5+col) / 34
                        color = (int(0+129*t), int(245-105*t), int(160+88*t))
                        d.rectangle((x,y,x+CELL-2,y+CELL-2), fill=color)
    d.text((24, 171), "typing identity... UTKARSH", font=FONT, fill=(0,217,213))
    cx = X0 + (step//5)*ADV + (step%5)*CELL + 2
    d.rectangle((cx, 166, cx+6, 178), fill=(0,245,160))
    frames.append(im.convert("P", palette=Image.Palette.ADAPTIVE, colors=48))
    durations.append(650 if step == 0 else 900 if step == len(steps) else [75,110,65,145,90][step % 5] + (180 if step % 5 == 0 else 0))

Path("assets").mkdir(exist_ok=True)
frames[0].save("assets/animated-name.gif", save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True, disposal=2)
