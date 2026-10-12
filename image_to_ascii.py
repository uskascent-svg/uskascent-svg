#!/usr/bin/env python3
"""Convert a logo image into a self-contained animated ASCII SVG."""
import argparse
from html import escape
from pathlib import Path
from PIL import Image, ImageOps

RAMP = " .:-=+*#%@"
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("image", help="Input PNG/JPG/WebP")
    ap.add_argument("--output",default="logo.svg")
    ap.add_argument("--columns",type=int,default=72)
    args=ap.parse_args()
    image=Image.open(args.image).convert("RGB")
    # Ignore near-black background when mapping; preserve silhouette/wordmark.
    image=ImageOps.grayscale(image)
    width=args.columns
    height=max(1,round(width*image.height/image.width*0.42))
    image=image.resize((width,height))
    rows=[]
    for y in range(height):
        row=""
        for x in range(width):
            value=image.getpixel((x,y))
            row+=RAMP[min(len(RAMP)-1, value*len(RAMP)//256)]
        rows.append(row)
    svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 330" role="img">',
         '<title>Animated ASCII logo</title><rect width="100%" height="100%" rx="12" fill="#050b0e"/>',
         '<g font-family="monospace" font-size="14" font-weight="700" fill="#27e1e5" xml:space="preserve">']
    for i,row in enumerate(rows):
        svg.append(f'<text x="24" y="{42+i*14}">{escape(row)}</text>')
    svg += ['<animate attributeName="opacity" values=".75;1;.85;1;.75" dur="3.8s" repeatCount="indefinite"/>',
            '<animateTransform attributeName="transform" type="translate" values="0 0;2 -1;0 0" dur="5s" repeatCount="indefinite"/>',
            '</g></svg>']
    Path(args.output).write_text("\n".join(svg)+"\n",encoding="utf-8")
    print(f"Wrote {args.output} ({Path(args.output).stat().st_size:,} bytes)")
if __name__=="__main__": main()
