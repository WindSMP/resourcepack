# Turns the sprite into cubes: one per run of same-depth pixels in a row, centred on z=8.
import json, sys
from PIL import Image
img=Image.open(sys.argv[1]).convert("RGBA"); depth=json.load(open(sys.argv[2]))
ops=[]
for y in range(16):
    x=0
    while x<16:
        if img.getpixel((x,y))[3]==0: x+=1; continue
        d=depth[f"{x},{y}"]; x0=x
        while x<16 and img.getpixel((x,y))[3]>0 and depth[f"{x},{y}"]==d: x+=1
        x1=x; top=16-y
        f=lambda u: {"uv":u,"texture":0}
        ops.append({"op":"add_cube","name":f"r{y}_{x0}","from":[x0,top-1,8-d/2],"to":[x1,top,8+d/2],
            "faces":{"south":f([x0,y,x1,y+1]),"north":f([x1,y,x0,y+1]),"up":f([x0,y,x1,y+1]),"down":f([x0,y,x1,y+1]),
                     "east":f([x1-1,y,x1,y+1]),"west":f([x0,y,x0+1,y+1])}})
json.dump(ops,open(sys.argv[3],"w")); print(len(ops),"cubes")
