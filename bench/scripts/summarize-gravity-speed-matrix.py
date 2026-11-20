import csv,json,math,statistics as stats
from pathlib import Path
src=Path('outputs/robonine-gravity-speed-matrix.ndjson')
out=Path('outputs/robonine-gravity-speed-matrix-summary.csv')
def rms(vals):return math.sqrt(stats.mean(x*x for x in vals))
with out.open('w',newline='') as f:
 w=csv.writer(f)
 w.writerow(['trial','speed_setting_counts_s','from','target','compensation_enabled','moving_samples','middle_speed_counts_s','tracking_rms_counts','tracking_mean_signed_counts','pid_effort_rms','gravity_min','gravity_max','saturation_pct','final_error_counts'])
 for i,line in enumerate(src.open(),1):
  d=json.loads(line)
  a=[r for r in d['rows'] if r['running'] and r['referenceVelocityQ8PerS']]
  e=[(r['referencePositionQ8']-r['measuredPositionQ8'])/256 for r in a]
  lo,hi=sorted((d['from'],d['target']))
  mid=[r for r in a if lo+.25*(hi-lo)<=r['measuredPositionQ8']/256<=hi-.25*(hi-lo)]
  midv=''
  if len(mid)>1:
   dt=((mid[-1]['sampleMs']-mid[0]['sampleMs'])%2**32)/1000
   if dt:midv=round(abs(mid[-1]['measuredPositionQ8']-mid[0]['measuredPositionQ8'])/256/dt,2)
  w.writerow([i,d['speed'],d['from'],d['target'],int(d['onFlag']),len(a),midv,round(rms(e),3),round(stats.mean(e),3),round(rms([r['pTerm']+r['dTerm']+r['iTerm'] for r in a]),3),min(r['gravityEffort'] for r in a),max(r['gravityEffort'] for r in a),round(100*stats.mean(r['saturated'] for r in a),2),d['rows'][-1]['measuredPositionQ8']/256-d['target']])
print(i,'trials saved')
