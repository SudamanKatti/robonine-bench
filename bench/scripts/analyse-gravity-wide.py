import json,math,statistics as s
from collections import defaultdict
g=defaultdict(list)
for d in map(json.loads,open('outputs/robonine-gravity-wide-ab.ndjson')):
 a=[r for r in d['rows'] if r['running'] and r['referenceVelocityQ8PerS'] and min(d['from'],d['target'])<=r['measuredPositionQ8']/256<=max(d['from'],d['target'])]
 if not a:continue
 rms=lambda x:math.sqrt(s.mean(z*z for z in x))
 g[d['speed'],d['from'],d['onFlag']].append((rms([(r['referencePositionQ8']-r['measuredPositionQ8'])/256 for r in a]),rms([r['pTerm']+r['dTerm']+r['iTerm'] for r in a]),tuple(sorted(set(r['gravityEffort'] for r in a))),sum(r['saturated'] for r in a)/len(a)))
for k,v in sorted(g.items()):print(k,len(v),'tracking',round(s.mean(a[0] for a in v),2),'PID',round(s.mean(a[1] for a in v),2),'gravity',sorted(set(x for a in v for x in a[2])),'sat',round(s.mean(a[3] for a in v),3))
