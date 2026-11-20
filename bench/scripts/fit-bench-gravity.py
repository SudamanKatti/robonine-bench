import json,sys,numpy as np
from collections import defaultdict
rows=defaultdict(list); X=defaultdict(list); Y=defaultdict(list)
for line in open(sys.argv[1],encoding='utf8'):
 try:e=json.loads(line)
 except ValueError:continue
 if e['type']=='sample':rows[e['trialId']].append(e['sample'])
 if e['type']!='trial-end':continue
 tr=e['trial']; split=tr['split']; speed=tr['speed']; direction=np.sign(tr['target']-tr['from']); a=rows[tr['id']]
 for i in range(0,len(a)-4,5):
  w=a[i:i+5]
  if any(s['saturated'] or abs(s['referenceVelocityQ8PerS']/256-direction*speed)>2 for s in w):continue
  d=((w[-1]['sampleMs']-w[0]['sampleMs'])%2**32)/1000
  if not d:continue
  v=(w[-1]['measuredPositionQ8']-w[0]['measuredPositionQ8'])/256/d
  if abs(v-direction*speed)>0.15*speed:continue
  theta=np.mean([s['measuredPositionQ8']/256 for s in w])*2*np.pi/4096
  X[split].append([1,direction,max(0,v),min(0,v),np.sin(theta),np.cos(theta)])
  Y[split].append(np.mean([s['appliedEffort'] for s in w]))
if not X['screen'] or not X['validate']:sys.exit('Waiting for train and validation sweeps')
a,b=np.asarray(X['screen']),np.asarray(X['validate']);y,z=np.asarray(Y['screen']),np.asarray(Y['validate'])
for m in (4,6):
 c=np.linalg.lstsq(a[:,:m],y,rcond=None)[0]
 print(m,len(y),len(z),np.sqrt(np.mean((b[:,:m]@c-z)**2)),c.round(3))
