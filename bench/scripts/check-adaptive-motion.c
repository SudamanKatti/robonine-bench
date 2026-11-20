#include "arm_motion.h"
#include <assert.h>
#include <stdio.h>
static unsigned check(arm_motion_t *m,int goal,unsigned limit,unsigned speed){
 unsigned t=0;
 for(;!arm_motion_idle(m)&&t<90000;t++){
  arm_motion_step(m,1);
  assert(arm_motion_position(m)>=-4096*256&&arm_motion_position(m)<=4096*256);
  assert((double)m->acceleration/68719476736.0*1e6<=limit+.01);
  if ((double)m->acceleration/68719476736.0*1e6 < -(double)limit-.01) { printf("acc %g limit %u speed %u goal %d step %u\n", (double)m->acceleration/68719476736.0*1e6,limit,speed,goal,t); fflush(stdout); assert(0); }
  assert(arm_motion_velocity(m)<=(int)(speed*256+1) && arm_motion_velocity(m)>=-(int)(speed*256+1));
 }
 assert(arm_motion_idle(m)&&arm_motion_position(m)==goal*256);
 return t;
}
int main(void){
 unsigned count=0;
 for(int sign=-1;sign<=1;sign+=2)for(unsigned speed=100;speed<=500;speed+=100)
 for(int dist=512;dist<=2048;dist*=2)for(unsigned limit=200;limit<=600;limit+=200){
  arm_motion_t m; arm_motion_init(&m,0);
  assert(arm_motion_target(&m,sign*dist*256,speed,limit,150,-4096*256,4096*256));
  check(&m,sign*dist,limit,speed);
  arm_motion_init(&m,0);
  assert(arm_motion_target(&m,sign*dist*256,speed,limit,150,-4096*256,4096*256));
  while(sign*arm_motion_position(&m)<dist*128)arm_motion_step(&m,1);
  arm_motion_t before=m;
  assert(arm_motion_target(&m,0,speed,limit,150,-4096*256,4096*256));
  assert(m.position==before.position&&m.velocity==before.velocity&&m.acceleration==before.acceleration);
  check(&m,0,limit,speed);
  count+=2;
 }
 printf("%u bounded planner cases passed\n",count);
}
