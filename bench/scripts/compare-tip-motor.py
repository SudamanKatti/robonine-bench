import json,numpy as n
from collections import defaultdict
def metrics(rows,start,end):
 t=n.array([z[0] for z in rows]); x=(n.array([z[1] for z in rows])-start)*n.sign(end-start)
 d=abs(end-start)
 def cross(frac):
  for i in range(1,len(x)):
   if x[i-1]<=d*frac<x[i]:return t[i-1]+(t[i]-t[i-1])*(d*frac-x[i-1])/(x[i]-x[i-1])
 z=n.arange(t[0],t[-1],.02);y=n.interp(z,t,x);k=6
 acc=(y[4*k:]-2*y[2*k:-2*k]+y[:-4*k])/(2*k*.02)**2;mid=y[2*k:-2*k]
 return [d*.5/(cross(.75)-cross(.25)),max(acc[(mid>=0)&(mid<d*.2)]),max(-acc[(mid>d*.8)&(mid<d)]),cross(.98)-cross(.02)]
out=defaultdict(list)
for e in map(json.loads,open('outputs/stock-tip-motor-matched.ndjson')):
 if e['hold']<3:continue
 lo,hi=(1936,2960) if e['hold']==3 else (2050,2850)
 end=e['target'];out['stock',hi-lo].append(metrics(e['samples'],lo if end==hi else hi,end)+[abs(e['error'])])
samples=defaultdict(list)
for e in map(json.loads,open('outputs/robonine-tip-motor-matched.ndjson',encoding='utf8')):
 if e['type']=='sample':
  a=e['sample'];samples[e['trialId']].append((a['sampleMs']/1000,a['measuredPositionQ8']/256))
 if e['type']=='trial-end':
  t=e['trial'];out['adaptive',abs(t['target']-t['from'])].append(metrics(samples[t['id']],t['from'],t['target'])+[t['result']['metrics']['holdError']])
for k,v in out.items():print(k,len(v),n.median(v,axis=0).round(2), 'max stop',max(a[-1] for a in v))
