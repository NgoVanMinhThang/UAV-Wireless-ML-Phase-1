from uwml.config import load_config
from uwml.world import World
from uwml.renderer_opengl import OpenGLRenderer
cfg=load_config('configs/default.yaml'); w=World(cfg); w.spawn(); OpenGLRenderer().loop(w,cfg.system.dt,cfg.system.steps)
