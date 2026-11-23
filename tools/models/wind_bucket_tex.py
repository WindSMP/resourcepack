# Drain bucket: the Breeze-coloured, empty bucket (as vanilla's, recoloured by wind_tools_tex.py), kept
# slim: the rim stands out a little, the opening sits a little in. Rewrites the depth map only.
import json, sys
from PIL import Image
d=sys.argv[1]
im=Image.open(f"{d}/wind_bucket_tex.png").convert("RGBA"); depth=json.load(open(f"{d}/wind_bucket_depth.json"))
OUTLINE=(44,48,92)
for key in list(depth):
    x,y=map(int,key.split(","))
    outline=im.getpixel((x,y))[:3]==OUTLINE
    if y<=2 or (y in (3,4,5,6) and outline): depth[key]=1.6      # the rim
    elif y in (3,4,5): depth[key]=0.8                            # the opening, a little sunken
    else: depth[key]=1.2                                         # the body
json.dump(depth,open(f"{d}/wind_bucket_depth.json","w"))
