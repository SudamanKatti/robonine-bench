import sys,time,json,serial
sys.path.insert(0,'work/repo/tools/flash')
import bootloader as b
def u(r,i):return int.from_bytes(r[i:i+2],'little')
def w(p,a,v,n=1):
 b.send(p,1,3,bytes([a])+v.to_bytes(n,'little'));time.sleep(.04)
with serial.Serial('COM6',1000000,timeout=.05) as p,open('outputs/stock-tip-recording-slow.ndjson','x') as f:
 r=b.registers(p,1); x=u(r,56)
 assert list(r[:2])==[3,10] and 1994<=x<=3068 and r[40]==0,(x,r[40])
 try:
  w(p,42,x,2);w(p,40,1);w(p,41,2);w(p,46,100,2)
  for target,hold in [(2019,2.2),(3043,2.2),(2019,2.2),(3043,2.2),(2019,2.2)]:
   start=u(b.registers(p,1),56)
   t=time.monotonic();w(p,42,target,2)
   rows=[];quiet=None;done=False;progress=t;prev=start
   while time.monotonic()-t<15:
    r=b.registers(p,1);x=u(r,56);now=time.monotonic();dt=now-t
    assert r[40]==1 and u(r,42)==target and 1994<=x<=3068 and r[63]<55,(x,u(r,42),target,r[40],r[63])
    rows.append([dt,x,u(r,58),r[63],u(r,69)])
    if abs(x-prev)>=2:progress=now;prev=x
    assert abs(x-target)<=12 or now-progress<.85,'Motion stalled'
    if abs(x-target)<=12 and u(r,58)==0:
     if quiet is None:quiet=dt
     if dt-quiet>=hold:done=True;break
    else:quiet=None
    time.sleep(.02)
   f.write(json.dumps(dict(start=start,target=target,speed=100,hold=hold,settled=done,error=x-target,stop_s=quiet,samples=rows))+'\n');f.flush()
   print(start,target,done,x-target,flush=True)
   assert done
 finally:
  w(p,40,0);print('Torque off',b.registers(p,1)[40]==0,flush=True)
