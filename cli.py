from __future__ import annotations
import argparse, json
from uwml.config import load_config
from uwml.world import World
from uwml.renderer_opengl import OpenGLRenderer
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/default.yaml")
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--headless", action="store_true")
    args=ap.parse_args()
    cfg=load_config(args.config)
    if args.steps is not None: cfg.system.steps=args.steps
    w=World(cfg); w.spawn()
    if args.headless:
        for _ in range(cfg.system.steps): w.step(cfg.system.dt)
        stats={"time_s":w.stats.time_s,"step":w.stats.step,"enqueued":w.stats.enqueued,"dequeued":w.stats.dequeued,
               "dropped":w.stats.dropped,"avg_latency_s":(w.stats.sum_latency_s/max(1,w.stats.count_latency or 1)),
               "max_latency_s":w.stats.max_latency_s,"packets_logged":len(w.packets)}
        print(json.dumps(stats,indent=2)); return
    OpenGLRenderer().loop(w, cfg.system.dt, cfg.system.steps)
if __name__=="__main__": main()
