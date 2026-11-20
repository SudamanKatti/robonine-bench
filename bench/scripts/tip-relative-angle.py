import cv2 as c,numpy as n
def pt(x,y): return n.array([(45+x*365/250)*2,(235+y*485/332)*2])
def get(v,t):
 v.set(c.CAP_PROP_POS_MSEC,t*1000);ok,f=v.read();assert ok
 return c.cvtColor(f,c.COLOR_BGR2GRAY)
def features(a,p):
 m=n.zeros(a.shape,n.uint8);x,y=map(int,p)
 m[max(0,y-175):y+90,x+120:min(a.shape[1],x+380)]=255
 return c.SIFT_create(1500,contrastThreshold=.012).detectAndCompute(a,m)
def center(im,p):
 x,y=map(round,p);z=im[y-10:y+11,x-10:x+11].astype(float)
 yy,xx=n.indices(z.shape);v=n.maximum(n.percentile(z,33)-z,0)
 return n.array([x-10+(xx*v).sum()/v.sum(),y-10+(yy*v).sum()/v.sum()])
for name,t0,t1,tip,h0,h1 in [
 ('212636',55,75,pt(149,225),pt(159,75),pt(132,20)),
 ('213249',58,83,pt(123,271),pt(133,145),pt(117,120))]:
 v=c.VideoCapture(f'C:/Users/ASUS/Downloads/20261118_{name}.mp4')
 a=get(v,t0); ka,da=features(a,h0);ref=center(a,tip); shaft=center(a,h0); groups=[[],[]]
 for i,(t,h) in enumerate([(t0,h0),(t1,h1)]):
  for dt in (-.25,0,.25,.5):
   b=get(v,t+dt);kb,db=features(b,h)
   if db is None: continue
   pairs=[p for p,q in c.BFMatcher().knnMatch(db,da,k=2) if p.distance<.72*q.distance]
   x=n.float32([kb[p.queryIdx].pt for p in pairs]);y=n.float32([ka[p.trainIdx].pt for p in pairs])
   for method in ('affine','projective'):
    H,ok=(c.estimateAffinePartial2D(x,y,ransacReprojThreshold=2) if method=='affine' else c.findHomography(x,y,c.RANSAC,2))
    if H is None or ok.sum()<25:continue
    warped=(c.warpAffine(b,H,(a.shape[1],a.shape[0])) if method=='affine' else c.warpPerspective(b,H,(a.shape[1],a.shape[0])))
    q=center(warped,ref); hub=center(warped,shaft); ray=q-hub; groups[i].append((method,n.degrees(n.arctan2(ray[1],ray[0]))))
 for method in ('affine','projective'):
  p,q=[n.asarray([xy for k,xy in g if k==method]) for g in groups]
  print(name,method,len(p),len(q),'shift_deg',round(abs(n.median(p)-n.median(q)),3),'within_deg',round(max(n.ptp(p),n.ptp(q)),3),'frames',n.round(p,3),n.round(q,3))
