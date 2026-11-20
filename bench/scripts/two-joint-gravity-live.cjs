const {StsServo}=require('../../host/servo-driver');
const {GravityModel}=require('../../host/arm-control/GravityModel');
const cfg=require('../config/so101-two-joint-controller.json');
const model=new GravityModel(require('../config/so101-two-joint-fixed-tip.json'));
const servo=new StsServo({serial:{path:cfg.followerPort,baudRate:cfg.baudRate}});
const ids=[1,2], session=require('node:crypto').randomInt(1,65536);
const opts={timeoutMs:100,rejectOnAlarm:true}, wait=ms=>new Promise(r=>setTimeout(r,ms));
const active=[], pos={}, sent={}, seq={1:0,2:0};
let running=true, report=0;
for(const signal of ['SIGINT','SIGTERM'])process.once(signal,()=>{running=false;});
(async()=>{
 await servo.connect({discovery:{ids}});
 try{
  for(const id of ids){
   const s=await servo.bus.read(id,['presentPosition','positionCorrection','torqueEnable'],opts);
   if(s.torqueEnable||s.positionCorrection!==model.document.encoderCalibration[id].positionCorrection)throw Error('Preflight ID '+id);
   pos[id]=s.presentPosition;
  }
  model.evaluate(pos,ids,cfg.profiles);
  for(const id of ids){
   await servo.arm.configure(id,{...cfg.profiles[id],accelerationLimit:cfg.acceleration,rampTimeMs:cfg.rampTimeMs},opts);
   await servo.arm.select(id,true,session,opts);
   active.push(id);await servo.bus.write(id,{torqueEnable:1},opts);
  }
  await wait(350);
  while(running){
   const begin=performance.now(), telemetry={};
   for(const id of ids){
    const s=await servo.arm.tuning(id,opts);
    if(s.session!==session||s.faults||!s.fresh||!s.driveEnabled||!s.outputReady||s.pTerm||s.iTerm||s.dTerm||(seq[id]&&s.gravitySequence!==seq[id]))throw Error('Control state ID '+id);
    pos[id]=s.measuredPositionQ8/256;
    telemetry[id]={position:pos[id],gravity:s.gravityEffort,applied:s.appliedEffort};
   }
   const effort=model.evaluate(pos,ids,cfg.profiles);
   for(const id of ids)if(sent[id]!==effort[id]){
    if(performance.now()-begin>250)throw Error('Stale joint measurements');
    seq[id]=seq[id]%65535+1;
    await servo.arm.updateGravity(id,{session,sequence:seq[id],gravityEffort:effort[id]},opts);
    sent[id]=effort[id];
   }
   if(performance.now()-begin>300)throw Error('Gravity cycle exceeded 300 ms');
   if(Date.now()-report>5000){console.log(JSON.stringify(telemetry));report=Date.now();}
   await wait(20);
  }
 }finally{
  for(const id of active)try{await servo.bus.write(id,{torqueEnable:0},opts);console.log('Torque off',id,(await servo.bus.read(id,['torqueEnable'],opts)).torqueEnable===0);}catch(e){console.error('Torque-off error',id,e.message);}
  await servo.close();
 }
})().catch(e=>{console.error(e.message);process.exitCode=1;});
