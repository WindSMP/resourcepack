# Wind tool textures: vanilla tools recoloured in the Breeze's colours (the sell axe keeps a gold head
# so it never looks like the tree axe), each with a depth map for its 3D model.
import json, os, sys
from PIL import Image
T=sys.argv[1]; OUT=sys.argv[2]
ROD={(40,30,11):(30,46,84),(73,54,21):(62,94,135),(104,78,30):(87,108,157),(137,103,39):(149,141,211)}
ROD_DEPTH={(40,30,11):1.0}
BREEZE={(8,37,32):(58,62,118),(14,63,54):(126,128,196),(30,138,119):(170,164,222),(39,178,154):(200,194,236),(43,199,172):(228,230,248),(51,235,203):(255,255,255)}
BREEZE_THIN={(8,37,32),(14,63,54)}
GOLD={(63,46,14):(104,62,14),(130,93,22):(190,124,24),(220,150,19):(230,164,38),(233,177,21):(246,198,64),(234,238,87):(255,232,128),(253,255,118):(255,250,204)}
GOLD_THIN={(63,46,14),(130,93,22)}
BUCKET={(53,53,53):(44,48,92),(84,84,84):(70,84,140),(95,95,95):(87,108,157),(114,114,114):(122,130,196),(150,150,150):(160,156,218),(168,168,168):(190,186,232),(216,216,216):(226,228,248),(255,255,255):(255,255,255)}
TOOLS={
  "wind_pickaxe":("diamond_pickaxe",BREEZE,BREEZE_THIN,1.2,1.6),
  "wind_axe":("diamond_axe",BREEZE,BREEZE_THIN,1.2,1.6),
  "wind_shovel":("diamond_shovel",BREEZE,BREEZE_THIN,1.2,1.6),
  "wind_sell_axe":("golden_axe",GOLD,GOLD_THIN,1.2,1.6),
  "wind_bucket":("bucket",BUCKET,{(53,53,53)},1.8,2.4),
}
for name,(src,head,thin,d_thin,d_thick) in TOOLS.items():
    im=Image.open(f"{T}/{src}.png").convert("RGBA"); out=Image.new("RGBA",(16,16),(0,0,0,0)); depth={}
    for y in range(16):
        for x in range(16):
            p=im.getpixel((x,y))
            if not p[3]: continue
            c=p[:3]
            if c in head:
                out.putpixel((x,y),head[c]+(255,)); depth[f"{x},{y}"]=d_thin if c in thin else d_thick
            elif c in ROD:
                out.putpixel((x,y),ROD[c]+(255,)); depth[f"{x},{y}"]=ROD_DEPTH.get(c,1.2)
            else: raise SystemExit(f"{name}: unmapped colour {c} at {x},{y}")
    out.save(f"{OUT}/{name}_tex.png"); json.dump(depth,open(f"{OUT}/{name}_depth.json","w"))
    print(name,"ok")
