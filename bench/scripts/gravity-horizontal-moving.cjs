const {StsServo}=require('./repo/host/servo-driver');
const fs=require('node:fs');
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const {randomInt}=require('node:crypto');
const servo=new StsServo({serial:{path:'COM6',baudRate:1000000}});
const session=randomInt(1,65536),o={timeoutMs:150,rejectOnAlarm:true},id=1;
const config={...require('./robonine-recording/two-count-profile.json'),accelerationLimit:150,rampTimeMs:250};
let seq=0,gseq=0,armed=false;
async function sample(){
 const s=await servo.arm.tuning(id,o);
 if(s.faults||s.session!==session||!s.armed||s.temperatureValidated>=55||s.measuredPositionQ8/256<2913||s.measuredPositionQ8/256>3173)throw Error('Guard triggered');
 if(Math.abs(s.referencePositionQ8-s.measuredPositionQ8)>25600)throw Error('Following error');
 return s;
}
async function move(p){
 await servo.arm.setTargets([{id,target:{sequence:++seq,positionQ8:p*256,speedLimit:50}}],session,o);
 const end=Date.now()+23000, rows=[];
 while(Date.now()<end){await wait(45);const s=await sample();rows.push(s);if(s.acceptedSequence===seq&&!s.running&&Math.abs(s.measuredPositionQ8/256-p)<=12)return rows;}
 throw Error('Move timeout');
}
async function hold(effort){
 await servo.arm.updateGravity(id,{session,sequence:++gseq,gravityEffort:effort},o);
 const end=Date.now()+2200,rows=[];
 while(Date.now()<end){await wait(45);const s=await sample();rows.push(s);}
 if(rows.at(-1)?.gravityEffort!==effort||rows.at(-1)?.gravitySequence!==gseq)throw Error('Gravity readback mismatch');
 return rows.slice(-20);
}
(async()=>{
 await servo.connect({discovery:{ids:[1]}});
 try{
  const b=await servo.bus.read(id,['torqueEnable','presentPosition'],o);
  if(b.torqueEnable||!(b.presentPosition>=3033&&b.presentPosition<=3053))throw Error(JSON.stringify(b));
  await servo.arm.configure(id,config,o);
  await servo.arm.select(id,true,session,o);
  armed=true;await servo.bus.write(id,{torqueEnable:1},o);
  await wait(350);
  for(const effort of [0,4,4,0]){
   await hold(0); await move(2963);
   const on=await hold(effort);
   for(const [from,target] of [[2963,3123],[3123,2963]]){
    const rows=await move(target);
    fs.appendFileSync('outputs/robonine-horizontal-moving-ab.ndjson',JSON.stringify({from,target,effort,rows})+'\n');
    console.log(from,target,effort,rows.length);
   }
  }
 }finally{
  try{if(armed){await servo.bus.write(id,{torqueEnable:0},o);console.log('Torque off',(await servo.bus.read(id,['torqueEnable'],o)).torqueEnable===0);}}
  finally{await servo.close();}
 }
})().catch(e=>{console.error(e);process.exitCode=1});
