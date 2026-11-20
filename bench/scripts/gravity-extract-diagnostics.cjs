const {extract}=require('./repo/tools/tuning/identification');
try{extract(['outputs/robonine-tip-repo-gravity.ndjson']);}catch(e){
 const d=e.diagnostics;
 if(d){console.log(d.rejected);let c={};for(const r of d.rows){const k=[r.split,r.source.speed,r.x[1]];c[k]=(c[k]||0)+1;}console.log(c);}
}
