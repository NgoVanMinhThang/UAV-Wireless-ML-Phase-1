from uwml.config import load_config

def test_config_sections():
    cfg=load_config('configs/default.yaml')
    for sec in ('system','world','channel','packet'): assert hasattr(cfg,sec)
    for sec in ('time','hardware','uav','ue','viz'): assert hasattr(cfg,sec)
