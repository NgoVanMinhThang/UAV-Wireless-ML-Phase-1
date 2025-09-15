# -*- coding: utf-8 -*-
"""Kiểm thử vị trí luôn nằm trong 'bounds' sau nhiều bước mô phỏng."""
from uwml.config import load_config
from uwml.world import World

def test_positions_within_bounds():
    # Nạp cấu hình và khởi tạo thế giới
    cfg = load_config('configs/default.yaml')
    w = World(cfg)
    w.spawn()

    # Tiến mô phỏng 50 bước để các entity di chuyển đủ nhiều
    for _ in range(50):
        w.step(cfg.system.dt)

    # Lấy hộp biên để kiểm tra
    x0, x1, y0, y1, z0, z1 = cfg.world.bounds

    def inside(p):
        # Cho phép một sai số epsilon rất nhỏ để tránh lỗi số học
        return (x0-1e-5) <= p[0] <= (x1+1e-5) and \
               (y0-1e-5) <= p[1] <= (y1+1e-5) and \
               (z0-1e-5) <= p[2] <= (z1+1e-5)

    # Tất cả UE/UAV đều phải nằm trong biên
    assert all(inside(u.pos) for u in w.ue)
    assert all(inside(a.pos) for a in w.uav)
