import cv2 as c,numpy as n
def pt(x,y):return n.array([(45+x*365/250)*2,(235+y*485/332)*2])
cases=[
('Robonine 1',(159,75),(149,225),(242,68),[(43,43),(121,48),(39,120),(115,126)]),
('Robonine 2',(132,20),(130,180),(220,15),[(46,40),(128,42),(47,120),(128,126)]),
('Stock 1',(133,145),(123,271),(223,142),[(51,57),(116,63),(47,117),(110,126)]),
('Stock 2',(117,120),(109,250),(204,118),[(44,58),(110,66),(46,123),(107,135)])]
dst=n.float32([[-1,-1],[1,-1],[-1,1],[1,1]])
rng=n.random.default_rng(17)
for name,hub,tip,axis,s in cases:
 h=pt(*hub);s=n.array(s)+n.rint(h)-85
 p=n.array([h,pt(*tip),pt(*axis)])
 def angle(s,p):
  H=c.getPerspectiveTransform(s.astype('float32'),dst)
  a,b,k=c.perspectiveTransform(p.astype('float32')[None],H)[0]
  u=b-a;v=k-a
  return n.degrees(n.arctan2(v[0]*u[1]-v[1]*u[0],v@u))
 q=angle(s,p)
 a=[angle(s+rng.uniform(-1,1,s.shape),p+rng.uniform(-1,1,p.shape)) for _ in range(1500)]
 print(name,round(q,2),n.round(n.percentile(a,[2.5,97.5]),2))
