import json,numpy as np
from collections import defaultdict
groups=defaultdict(list)
for d in map(json.loads,open('outputs/robonine-gravity-speed-matrix.ndjson')):
 if d['onFlag']:continue
 s=np.sign(d['target']-d['from'])
 w=[]
 for a in d['rows']:
  if a['saturated'] or not a['running'] or abs(a['referenceVelocityQ8PerS']/256-s*d['speed'])>d['speed']*.05:
   w=[];continue
  w.append(a)
  dt=((w[-1]['sampleMs']-w[0]['sampleMs'])%2**32)/1000
  if dt<.2:continue
  x0=w[0]['measuredPositionQ8']/256;x1=w[-1]['measuredPositionQ8']/256;v=(x1-x0)/dt
  if abs(v-s*d['speed'])<d['speed']*.15:
   c=np.mean([np.cos((r['measuredPositionQ8']/256-3043)*2*np.pi/4096) for r in w])
   groups[(d['speed'],d['from'])].append(([s,max(v,0),min(v,0),c],np.mean([r['appliedEffort'] for r in w])))
  w=[]
for k,v in sorted(groups.items()): print(k,len(v))
speeds=sorted({k[0] for k in groups})
for test in speeds:
 train=[a for (speed,_),b in groups.items() if speed!=test for a in b]
 valid=[a for (speed,_),b in groups.items() if speed==test for a in b]
 if len({k[0] for k in groups if k[0]!=test})<2 or not valid:continue
 X,y=map(np.array,zip(*train));Z,w=map(np.array,zip(*valid))
 if np.linalg.matrix_rank(X)<4:continue
 c=np.linalg.lstsq(X,y,rcond=None)[0]
 b=np.linalg.lstsq(X[:,:3],y,rcond=None)[0]
 rms=lambda e:np.mean(e**2)**.5
 print('held speed',test,'gravity',round(c[-1],2),'effort prediction rms',round(rms(Z[:,:3]@b-w),2),'->',round(rms(Z@c-w),2))
