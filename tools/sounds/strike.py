# A wind strike: a short low thump on impact, then a gust whose resonant band falls away fast, so a swing sounds
# like a blow carried on wind. Pure Python. usage: strike.py out.wav seed dur fhigh flow q thump_hz
import math, random, struct, sys, wave
out, seed, dur, fhi, flo, q, thz = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7])
SR=44100; n=int(SR*dur); rnd=random.Random(seed)
lp=bp=0.0; samples=[]
for i in range(n):
    t=i/SR; x=i/n
    w=rnd.uniform(-1,1)
    env=min(1.0,t/0.004)*math.exp(-t/0.085)                  # instant attack, quick fall
    fc=flo+(fhi-flo)*math.exp(-t/0.06)                         # the band drops fast: "fwump"
    f=2*math.sin(math.pi*fc/SR)
    hp=w-lp-bp/q; bp+=f*hp; lp+=f*bp
    thump=math.sin(2*math.pi*thz*t*(1-0.35*x))*math.exp(-t/0.03)   # a short low hit, falling a little in pitch
    samples.append(bp*env*0.9+thump*0.55)
peak=max(abs(s) for s in samples) or 1
with wave.open(out,'wb') as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes(b''.join(struct.pack('<h',int(max(-1,min(1,s/peak*0.85))*32767)) for s in samples))
