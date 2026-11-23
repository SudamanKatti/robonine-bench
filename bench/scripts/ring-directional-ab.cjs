const fs=require('node:fs');
const {StsServo}=require('../../host/servo-driver');
const {GravityModel}=require('../../host/arm-control/GravityModel');
const servo=new StsServo({serial:{path:'COM6',baudRate:1000000}});
const id=2, session=require('node:crypto').randomInt(1,65536);
const o={timeoutMs:100,rejectOnAlarm:true}, wait=ms=>new Promise(r=>setTimeout(r,ms));
const cfg={...require('../config/two-count-profile.json'),accelerationLimit:100,rampTimeMs:250};
const weight=2*Math.PI/4096, zero=2904;
let seq=0, gseq=0, sent, start, model, active=false, cancelled=false;
process.once('SIGINT',()=>{cancelled=true;});
const log={calibration:[],comparison:[]};
const median=values=>{const v=[...values].sort((a,b)=>a-b);return v[Math.floor(v.length/2)];};
async function leg(goal,speed,on){
 await servo.arm.setTargets([{id,target:{sequence:++seq,positionQ8:goal*256,speedLimit:speed}}],session,o);
 const rows=[];
 let settled;
 for(const end=Date.now()+5500;Date.now()<end;){
  if(cancelled)throw Error('Cancelled');
  await wait(18);
  const s=await servo.arm.tuning(id,o);
  const pos=s.measuredPositionQ8/256;
  if(s.session!==session||s.faults||!s.fresh||!s.driveEnabled||pos<start-18||pos>start+72)throw Error('Travel or feedback check failed at '+pos);
  const effort=on?model.evaluate({2:pos},[2],{2:cfg})[2]:0;
  if(effort!==sent){await servo.arm.updateGravity(id,{session,sequence:++gseq,gravityEffort:effort},o);sent=effort;}
  if(s.acceptedSequence!==seq||s.gravitySequence!==gseq)continue;
  rows.push(s);
  if(!s.running&&(settled??=Date.now())+950<=Date.now())return rows;
 }
 throw Error('Motion or gravity acknowledgement timed out');
}
function estimate(up,down,speed){
 const steady=(rows,sign)=>rows.filter(s=>{
  const p=s.measuredPositionQ8/256, v=sign*s.measuredVelocityQ8PerS/256;
  return s.running&&p>=start+10&&p<=start+44&&v>=speed*.55&&v<=speed*1.45;
 });
 const a=steady(up,1), b=steady(down,-1);
 const pairs=[];
 for(let bin=start+10;bin<start+44;bin+=7){
  const inBin=s=>s.measuredPositionQ8/256>=bin&&s.measuredPositionQ8/256<bin+7;
  const u=a.filter(inBin), d=b.filter(inBin);
  if(!u.length||!d.length)continue;
  const v1=median(u.map(s=>s.measuredVelocityQ8PerS/256));
  const v2=median(d.map(s=>-s.measuredVelocityQ8PerS/256));
  if(Math.abs(v1-v2)>speed*.3)continue;
  pairs.push((median(u.map(s=>s.appliedEffort))+median(d.map(s=>s.appliedEffort)))/2/Math.cos(weight*(bin+3.5-zero)));
 }
 return pairs;
}
(async()=>{
 await servo.connect({discovery:{ids:[id]}});
 try{
  const r=await servo.bus.read(id,['torqueEnable','presentPosition','positionCorrection'],o);
  start=r.presentPosition;log.start=start;
  if(r.torqueEnable||r.positionCorrection!==85||Math.min(Math.abs(start-2904),Math.abs(start-2562))>20)throw Error('Starting pose changed: '+start);
  const caps=await servo.arm.capabilities(id,o);
  if(caps?.major!==9)throw Error('Robonine v9 required');
  await servo.arm.configure(id,cfg,o);
  active=true;
  await servo.arm.select(id,true,session,o);
  await servo.bus.write(id,{torqueEnable:1},o);
  await wait(350);
  await leg(start,30,false);
  for(const speed of [30,45,30]){
   const up=await leg(start+52,speed,false), down=await leg(start,speed,false);
   const pairs=estimate(up,down,speed);
   console.log(JSON.stringify({speed,pairs}));
   log.calibration.push({speed,pairs,up,down});
  }
  const usable=log.calibration.filter(c=>c.pairs.length>=1).map(c=>median(c.pairs));
  const peak=median(usable);
  if(usable.length<3||!(peak>=1&&peak<=cfg.effortLimit)||Math.max(...usable)-Math.min(...usable)>Math.max(4,peak*.35))throw Error('Matched-motion data did not yield a repeatable positive gravity estimate');
  const doc={format:'sts-gravity',version:1,units:'pwm-effort',name:'ID 2 half-pound ring',calibration:'Provisional estimate from three repeated matched-motion samples near one angle',mounting:'Single horizontal shaft',payload:'Half-pound ring on printed arm',encoderCalibration:{2:{positionCorrection:85,resolution:1,reverse:false}},models:{2:{maxEffort:cfg.effortLimit,note:'Positive compensation lifts ring.',terms:[{fn:'cos',weights:{2:weight},offsetRad:-zero*weight,coefficient:peak}]}}};
  model=new GravityModel(doc);log.model=doc;
  for(const on of [false,true,false])for(const goal of [start+52,start]){
   const rows=await leg(goal,45,on);
   const moving=rows.filter(s=>s.running);
   const rms=moving.length?Math.sqrt(moving.reduce((a,s)=>a+((s.referencePositionQ8-s.measuredPositionQ8)/256)**2,0)/moving.length):null;
   const stop=Math.abs(goal-rows.at(-1).measuredPositionQ8/256);
   console.log(JSON.stringify({on,goal,rms,stop,gravity:rows.at(-1).gravityEffort}));
   log.comparison.push({on,goal,rms,stop,rows});
  }
 }finally{
  try{if(active){await servo.bus.write(id,{torqueEnable:0},o);const r=await servo.bus.read(id,['torqueEnable'],o);if(r.torqueEnable)throw Error('Torque-off verification failed');console.log('Torque off verified');}}
  finally{await servo.close();const file='ring-directional-ab-'+Date.now()+'.json';fs.writeFileSync(file,JSON.stringify(log));console.log(file);}
 }
})().catch(e=>{console.error(e.message);process.exitCode=1;});
