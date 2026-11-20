import json,numpy as n,sys
def metrics(a,start,end):
 t=n.array([z[0] for z in a]); x=(n.array([z[1] for z in a])-start)*n.sign(end-start)
 d=abs(end-start)
 middle=(x>=d*.25)&(x<=d*.75)
 z=n.arange(t[0],t[-1],.02); y=n.interp(z,t,x)
 out=[n.polyfit(t[middle]-t[0],x[middle],1)[0]]
 for k in (6,9,12):
  ac=(y[4*k:]-2*y[2*k:-2*k]+y[:-4*k])/(2*k*.02)**2
  xx=y[2*k:-2*k]
  out.extend((max(ac[(xx>=0)&(xx<d*.2)]),max(-ac[(xx>d*.8)&(xx<d)])))
 return out
stock=[]
for l in open('outputs/stock-loaded-180.ndjson'):
 d=json.loads(l)
 if d['speed']==250:stock.append(metrics(d['samples'],d['start'],d['target']))
c={};v=[]; hold=[]
for l in open(sys.argv[1],encoding='utf8'):
 try:e=json.loads(l)
 except ValueError:continue
 if e['type']=='sample':
  s=e['sample'];c.setdefault(e['trialId'],[]).append((s['sampleMs']/1000,s['measuredPositionQ8']/256))
 if e['type']=='trial-end':
  d=e['trial'];hold.append(d['result']['metrics']['holdError'])
  if d['split']=='validate':v.append(metrics(c[d['id']],d['from'],d['target']))
 if e['type']=='run-end':print(e['summary']['status'])
print('stock',len(stock),n.median(stock,axis=0).round(1))
if v:print('robonine',len(v),n.median(v,axis=0).round(1),'hold',hold)
