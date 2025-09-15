# -*- coding: utf-8 -*-
"""Điểm vào dòng lệnh: nạp cấu hình, chạy mô phỏng headless hoặc mở renderer OpenGL."""
from __future__ import annotations
import argparse, json

from uwml.config import load_config
from uwml.world import World
from uwml.renderer_opengl import OpenGLRenderer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config",  default="configs/default.yaml", help="đường dẫn file YAML cấu hình")
    ap.add_argument("--steps",   type=int, default=None,         help="ghi đè số bước (nếu truyền)")
    ap.add_argument("--headless", action="store_true",           help="chạy không vẽ 3D")
    args = ap.parse_args()

    # 1) Nạp cấu hình
    cfg = load_config(args.config)
    if args.steps is not None:
        cfg.system.steps = args.steps

    # 2) Tạo & nạp thế giới
    w = World(cfg)
    w.spawn()

    # 3) Chạy
    if args.headless:
        # Không vẽ: chỉ chạy step và in thống kê JSON
        for _ in range(cfg.system.steps):
            w.step(cfg.system.dt)

        stats = {
            "time_s": w.stats.time_s,
            "step": w.stats.step,
            "enqueued": w.stats.enqueued,
            "dequeued": w.stats.dequeued,
            "dropped": w.stats.dropped,
            "avg_latency_s": (w.stats.sum_latency_s / max(1, w.stats.count_latency or 1)),
            "max_latency_s": w.stats.max_latency_s,
            "packets_logged": len(w.packets),
        }
        print(json.dumps(stats, indent=2))
        return

    # Có vẽ: mở cửa sổ 3D
    OpenGLRenderer().loop(w, cfg.system.dt, cfg.system.steps)


if __name__ == "__main__":
    main()
