from uwml.config import load_config
from uwml.world import World

def test_positions_within_bounds():
    cfg=load_config('configs/default.yaml'); w=World(cfg); w.spawn()
    for _ in range(50): w.step(cfg.system.dt)
    x0,x1,y0,y1,z0,z1=cfg.world.bounds
    def inside(p): return (x0-1e-5)<=p[0]<=(x1+1e-5) and (y0-1e-5)<=p[1]<=(y1+1e-5) and (z0-1e-5)<=p[2]<=(z1+1e-5)
    assert all(inside(u.pos) for u in w.ue)
    assert all(inside(a.pos) for a in w.uav)
