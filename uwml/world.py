from __future__ import annotations
import numpy as np, random, math
from dataclasses import dataclass
from collections import deque
from .config import DotDict
from .models import BS,UAV,UE,Satellite,Packet,HardwareProfile
from .physics import move_ue, move_uav
from .channel import estimate_link_rate
@dataclass
class Stats:
    time_s: float=0.0; step:int=0; enqueued:int=0; dequeued:int=0; dropped:int=0
    sum_latency_s: float=0.0; count_latency:int=0; max_latency_s: float=0.0
class World:
    def __init__(self,cfg:DotDict):
        self.cfg=cfg; self.bounds=np.array(cfg.world.bounds,dtype=np.float32)
        hw=getattr(cfg,"hardware",DotDict(cpu_cores=0,gpu_tflops_est=0.0,mem_gb=0))
        self.hw=HardwareProfile(hw.cpu_cores,hw.gpu_tflops_est,hw.mem_gb)
        self.bs=BS(0,[0,0,0]); self.uav=[]; self.ue=[]; self.sat=[]
        self.stats=Stats(); self.packets=deque(maxlen=getattr(cfg.packet,"max_log",1000))
        if hasattr(cfg,"time") and hasattr(cfg.time,"seed"): random.seed(int(cfg.time.seed))
    def spawn(self):
        uv=getattr(self.cfg,"uav",None)
        n_uav=uv.count if (uv and hasattr(uv,"count")) else getattr(self.cfg.world,"n_uav",0)
        alt=uv.altitude_m if (uv and hasattr(uv,"altitude_m")) else 60.0
        rad=min(abs(self.bounds[1]-self.bounds[0]),abs(self.bounds[3]-self.bounds[2]))*0.35
        for i in range(n_uav):
            a=2*math.pi*i/max(1,n_uav); pos=[rad*math.cos(a),rad*math.sin(a),alt]; self.uav.append(UAV(i+1,pos))
        ue_cfg=getattr(self.cfg,"ue",None); n_ue=ue_cfg.count if (ue_cfg and hasattr(ue_cfg,"count")) else getattr(self.cfg.world,"n_ue",0)
        for j in range(n_ue):
            import random as _r; x=_r.uniform(self.bounds[0],self.bounds[1]); y=_r.uniform(self.bounds[2],self.bounds[3])
            self.ue.append(UE(j,[x,y,0.0]))
        sats=getattr(self.cfg.world,"satellites",[]) or []
        for k,p in enumerate(sats): self.sat.append(Satellite(k,p))
    def _nearest_uav_pos(self,p):
        if not self.uav: return self.bs.pos
        dmin=1e9; best=self.uav[0].pos
        for a in self.uav:
            d=float(np.linalg.norm(a.pos-p)); 
            if d<dmin: dmin, best=d, a.pos
        return best
    def step(self,dt:float):
        mcfg=self.cfg
        ue_speed=getattr(getattr(mcfg,"ue",None),"speed_mps", getattr(mcfg,"mobility",DotDict()).__dict__.get("ue_speed_mps",3.0))
        ue_turn =getattr(getattr(mcfg,"ue",None),"turn_std_deg", getattr(mcfg,"mobility",DotDict()).__dict__.get("ue_turn_std_deg",25.0))
        uav_speed=getattr(getattr(mcfg,"uav",None),"speed_mps", getattr(mcfg,"mobility",DotDict()).__dict__.get("uav_speed_mps",8.0))
        uav_wps  =getattr(getattr(mcfg,"uav",None),"waypoints", getattr(mcfg,"mobility",DotDict()).__dict__.get("uav_waypoints",None))
        for u in self.ue: move_ue(u,dt,self,speed=ue_speed,turn_std_deg=ue_turn)
        for a in self.uav: move_uav(a,dt,self,speed=uav_speed,waypoints=uav_wps)
        pcfg=self.cfg.packet
        for u in self.ue:
            dst=self._nearest_uav_pos(u.pos); best_id=0; dmin=1e9
            for a in self.uav:
                d=float(np.linalg.norm(a.pos-u.pos)); 
                if d<dmin: dmin, best_id=d, a.id
            u.attached_uav_id = best_id if self.uav else 0
            import random as _r
            if _r.random()<pcfg.gen_prob_per_step:
                self.stats.enqueued+=1
                rate=estimate_link_rate(u.pos,dst,self.cfg.channel)
                size_bits=pcfg.size_bytes*8.0; tx_time=size_bits/max(1e-6,rate*1e6)
                self.stats.dequeued+=1; self.stats.sum_latency_s+=tx_time; self.stats.count_latency+=1
                if tx_time>self.stats.max_latency_s: self.stats.max_latency_s=tx_time
                self.packets.append(Packet(pcfg.size_bytes, int(getattr(pcfg,"priority",1)), int(u.id), int(u.attached_uav_id), float(self.stats.time_s)))
        self.stats.time_s+=dt; self.stats.step+=1
