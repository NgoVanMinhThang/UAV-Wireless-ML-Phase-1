from __future__ import annotations
import numpy as np, math, random
def clamp_bounds(p,b):
    x0,x1,y0,y1,z0,z1=b; p[0]=min(max(p[0],x0),x1); p[1]=min(max(p[1],y0),y1); p[2]=min(max(p[2],z0),z1); return p
def move_ue(ue,dt,world,speed=3.0,turn_std_deg=25.0):
    if not hasattr(ue,"_dir_rad"): ue._dir_rad=random.uniform(0,2*math.pi)
    ue._dir_rad+=math.radians(random.gauss(0,turn_std_deg))
    v=np.array([math.cos(ue._dir_rad),math.sin(ue._dir_rad),0.0],dtype=np.float32)*speed
    ue.vel=v; ue.update(dt); clamp_bounds(ue.pos,world.bounds)
def move_uav(uav,dt,world,speed=8.0,waypoints=None):
    if not waypoints: uav.update(dt); clamp_bounds(uav.pos,world.bounds); return
    tgt=waypoints[uav._way_idx%len(waypoints)]; d=np.array(tgt,dtype=np.float32)-uav.pos
    dist=float(np.linalg.norm(d)); 
    if dist<1e-3: uav._way_idx+=1; return
    dir=d/max(1e-6,dist); uav.vel=dir*speed; step=min(dist,speed*dt); uav.pos=uav.pos+dir*step; clamp_bounds(uav.pos,world.bounds)
