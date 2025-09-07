from __future__ import annotations
import numpy as np
from dataclasses import dataclass
class Entity:
    def __init__(self, id:int, pos, vel=(0,0,0)):
        self.id=id; self.pos=np.array(pos,dtype=np.float32); self.vel=np.array(vel,dtype=np.float32)
    def update(self, dt: float): self.pos=self.pos+self.vel*dt
class BS(Entity): pass
class Satellite(Entity): pass
class UAV(Entity):
    def __init__(self,id:int,pos,vel=(0,0,0)):
        super().__init__(id,pos,vel); self._way_idx=0
class UE(Entity):
    def __init__(self,id:int,pos,vel=(0,0,0)):
        super().__init__(id,pos,vel); self.attached_uav_id=None
@dataclass
class Packet:
    size_bytes:int; priority:int; src_id:int; dst_id:int; timestamp:float
@dataclass
class HardwareProfile:
    cpu_cores:int; gpu_tflops_est:float; mem_gb:int
