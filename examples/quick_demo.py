# -*- coding: utf-8 -*-
"""Quick demo:
- Nạp cấu hình YAML
- Tạo World, spawn thực thể
- Mở renderer và chạy vòng lặp mô phỏng/hiển thị
"""
from uwml.config import load_config
from uwml.world import World
from uwml.renderer_opengl import OpenGLRenderer

# 1) Nạp cấu hình mặc định
cfg = load_config('configs/default.yaml')

# 2) Tạo thế giới và sinh thực thể (BS/UAV/UE/SAT)
w = World(cfg)
w.spawn()

# 3) Mở renderer và chạy vòng lặp (dt & steps lấy từ config)
OpenGLRenderer().loop(w, cfg.system.dt, cfg.system.steps)
