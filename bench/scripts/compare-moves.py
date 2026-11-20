import cv2 as c,numpy as np
theta=np.arange(180)*2*np.pi/180; kernel=np.exp(4j*theta)
for name,idx,box,center in [('stock',0,(95,210,35,27),(164,227)),('tuned',100,(105,143,42,30),(172,161))]:
 data=np.fromfile('work/'+name+'-video.gray',np.uint8); frames=data[:data.size//129600*129600].reshape(-1,480,270)
 if len(frames)<=idx: continue
 x,y,w,h=box;tpl=frames[idx,y:y+h,x:x+w]; rows=[]
 for g in frames:
  _,q,_,(u,v)=c.minMaxLoc(c.matchTemplate(g[70:300,30:220],tpl,c.TM_CCOEFF_NORMED))
  cx,cy=u+30+center[0]-x,v+70+center[1]-y
  vals=np.mean([c.remap(g,(cx+r*np.cos(theta)).astype('float32')[None,:],(cy+r*np.sin(theta)).astype('float32')[None,:],c.INTER_LINEAR)[0] for r in [12,13,14,15]],axis=0)
  rows.append((q,np.angle(vals@kernel)))
 q,phase=np.asarray(rows).T; a=np.degrees(np.unwrap(phase))/4
 np.savetxt('work/'+name+'-comparison.csv',np.c_[np.arange(len(a))/10,a,q],delimiter=',')
 print(name,[(i//10,round(float(np.median(a[i:i+10])),1)) for i in range(0,len(a),10)])
