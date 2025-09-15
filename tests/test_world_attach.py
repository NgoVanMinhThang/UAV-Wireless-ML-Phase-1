# -*- coding: utf-8 -*-
"""Kiểm thử: sau vài bước mô phỏng, mỗi UE đã gán attached_uav_id."""
from uwml.config import load_config
from uwml.world import World

def test_attach_nearest_after_steps():
    cfg = load_config('configs/default.yaml')
    w = World(cfg)
    w.spawn()

    # Cho chạy một số bước để UE kịp "bám" UAV gần nhất
    for _ in range(10):
        w.step(cfg.system.dt)

    assert len(w.ue) > 0
    assert all(u.attached_uav_id is not None for u in w.ue)
