const {BatchSource}=require('./repo/tools/tuning/BatchSource');
const original=BatchSource.prototype.move;
BatchSource.prototype.move=async function(controller,target,speed,trial){
 if (!trial)return original.call(this,controller,target,speed,trial);
 const from=trial.from, dir=Math.sign(target-from), id=this.feedbackId;
 const send=async goal=>{const f=this.frame(controller,goal,speed);await this.callbacks.onCommand(f);await controller.send(f);};
 const rows=[];
 let trigger,stop;
 await send(target);
 const start=controller.clock();
 try{
  while(controller.clock()-start<15000){
   const s=await this.tick(controller), t=s.hostMs-start, x=s.measuredPositionQ8/256;
   if(x<1911||x>2985)throw Error('Reversal travel guard');
   rows.push([t,x,s.measuredVelocityQ8PerS/256]);
   if(!trigger&&dir*(x-2448)>=0){trigger=[t,x];await send(from);}
   if(trigger&&!s.running&&s.referencePositionQ8===from*256&&Math.abs(x-from)<=5){
    stop??=t;if(t-stop>=750)break;
   }else stop=undefined;
  }
 }finally{
  const fs=require('node:fs');
  fs.appendFileSync('outputs/robonine-fast-reversal.ndjson',JSON.stringify({from,target,speed,trigger,stop,rows})+'\n');
 }
 if(!trigger||stop===undefined)throw Error('Reversal did not settle');
 this.n=(this.n??0)+1;
 if(this.n===2)throw Error('Reversal capture complete; end before validation');
 throw Error('Reversal capture complete');
};
require('./repo/tools/tuning/cli');
require('./repo/tools/tuning/cli').main().catch(e=>{console.error(e.message);process.exitCode=1});
