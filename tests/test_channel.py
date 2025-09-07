from uwml.config import load_config
from uwml.channel import pathloss_db, noise_power_dbm

def test_pathloss_monotonic():
    cfg=load_config('configs/default.yaml'); ds=[1,2,5,10,20,50,100]
    vals=[pathloss_db(d,cfg.channel) for d in ds]
    assert all(vals[i]<vals[i+1] for i in range(len(vals)-1))

def test_noise_bw_depends():
    cfg=load_config('configs/default.yaml')
    n1=noise_power_dbm(1e6,cfg.channel.noise_figure_db); n2=noise_power_dbm(8e6,cfg.channel.noise_figure_db)
    assert n2>n1
