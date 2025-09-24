# -*- coding: utf-8 -*-
"""Kiểm thử log gói tin:
- Sau khi chạy đủ bước, hàng đợi packets phải có ít nhất 1 bản ghi
- Bản ghi cuối cùng có kiểu và trường đúng
"""
from uwml.config import load_config
from uwml.world import World
from uwml.models import Packet

def test_packet_logging():
    cfg = load_config('configs/default.yaml')
    cfg.system.steps = 200  # tăng bước để chắc chắn sinh traffic

    w = World(cfg)
    w.spawn()
    for _ in range(cfg.system.steps):
        w.step(cfg.system.dt)

    # Phải có ít nhất 1 gói được ghi
    assert len(w.packets) > 0

    # Kiểm tra cấu trúc phần tử cuối
    p = w.packets[-1]
    assert isinstance(p, Packet)
    for attr in ('size_bytes', 'priority', 'src_id', 'dst_id', 'timestamp'):
        assert hasattr(p, attr)
