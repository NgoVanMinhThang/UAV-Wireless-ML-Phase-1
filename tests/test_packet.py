from uwml.config import load_config
from uwml.world import World
from uwml.models import Packet

def test_packet_logging():
    cfg=load_config('configs/default.yaml'); cfg.system.steps=200
    w=World(cfg); w.spawn()
    for _ in range(cfg.system.steps): w.step(cfg.system.dt)
    assert len(w.packets)>0
    p=w.packets[-1]; assert isinstance(p,Packet)
    for attr in ('size_bytes','priority','src_id','dst_id','timestamp'): assert hasattr(p,attr)
