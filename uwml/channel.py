from __future__ import annotations
import numpy as np, math
def pathloss_db(d_m: float, cfg) -> float:
    d=max(1e-3,float(d_m))
    if getattr(cfg,"model","log_distance")=="fspl":
        return 20.0*math.log10(d)+20.0*math.log10(cfg.carrier_hz)-147.55
    return cfg.ref_pathloss_db+10.0*cfg.pathloss_exp*math.log10(d/cfg.ref_distance_m)
def noise_power_dbm(bw_hz: float, nf_db: float) -> float:
    return -174.0+10.0*math.log10(float(bw_hz))+float(nf_db)
def sinr_db(tx_dbm: float, pl_db: float, n_dbm: float) -> float:
    return (tx_dbm-pl_db)-n_dbm
def estimate_link_rate(src_pos,dst_pos,cfg)->float:
    d=float(np.linalg.norm(np.array(dst_pos)-np.array(src_pos)))
    pl=pathloss_db(d,cfg); n_dbm=noise_power_dbm(cfg.bandwidth_hz,cfg.noise_figure_db); tx_dbm=20.0
    s_db=sinr_db(tx_dbm,pl,n_dbm); s_lin=10.0**(s_db/10.0); bw=float(cfg.bandwidth_hz)
    rate=0.5*bw*math.log2(1.0+max(1e-9,s_lin))
    return rate/1e6
