# -*- coding: utf-8 -*-
"""Mô hình kênh vô tuyến cơ bản: pathloss, nhiễu, SINR và ước lượng tốc độ link.

Các công thức sử dụng:
- FSPL: PL(dB) = 20·log10(d[m]) + 20·log10(f[Hz]) − 147.55
- Log-distance: PL(dB) = PL_ref + 10·n·log10(d/d_ref)
- Nhiệt Johnson–Nyquist: N(dBm) = −174 + 10·log10(BW[Hz]) + NF
- Shannon (ước lượng thô, tính thêm hệ số 0.5 cho overhead/half-duplex):
  R(bps) = 0.5 · BW · log2(1 + SNR_linear)
"""
from __future__ import annotations
import numpy as np, math


def pathloss_db(d_m: float, cfg) -> float:
    """Tính suy hao đường truyền (dB) ở khoảng cách d_m, theo cấu hình `cfg`.

    Args:
        d_m: khoảng cách (m).
        cfg: đối tượng cấu hình kênh, có thể có:
             - model: "fspl" hoặc "log_distance" (mặc định log_distance)
             - carrier_hz: tần số sóng mang (Hz) cho fspl
             - ref_pathloss_db, pathloss_exp, ref_distance_m cho log-distance.

    Returns:
        PL(dB) theo mô hình đã chọn.
    """
    d = max(1e-3, float(d_m))  # tránh log(0)
    if getattr(cfg, "model", "log_distance") == "fspl":
        # Free Space Path Loss (đơn vị: m, Hz)
        return 20.0 * math.log10(d) + 20.0 * math.log10(cfg.carrier_hz) - 147.55

    # Log-distance path loss
    return (
        cfg.ref_pathloss_db
        + 10.0 * cfg.pathloss_exp * math.log10(d / cfg.ref_distance_m)
    )


def noise_power_dbm(bw_hz: float, nf_db: float) -> float:
    """Công suất nhiễu (dBm) trong băng BW, cộng thêm Noise Figure."""
    return -174.0 + 10.0 * math.log10(float(bw_hz)) + float(nf_db)


def sinr_db(tx_dbm: float, pl_db: float, n_dbm: float) -> float:
    """SINR xấp xỉ (dB) khi bỏ qua nhiễu giao thoa (interference)."""
    return (tx_dbm - pl_db) - n_dbm


def estimate_link_rate(src_pos, dst_pos, cfg) -> float:
    """Ước lượng thông lượng (Mbps) giữa hai điểm 3D theo Shannon.

    Args:
        src_pos: (x, y, z) nguồn.
        dst_pos: (x, y, z) đích.
        cfg: cấu hình kênh, cần có bandwidth_hz, noise_figure_db và tham số PL.

    Returns:
        Thông lượng ước lượng theo Mbps (giá trị dương, đã chặn SNR nhỏ).
    """
    # 1) khoảng cách Euclid
    d = float(np.linalg.norm(np.array(dst_pos) - np.array(src_pos)))

    # 2) pathloss & noise
    pl = pathloss_db(d, cfg)
    n_dbm = noise_power_dbm(cfg.bandwidth_hz, cfg.noise_figure_db)

    # 3) công suất phát (giả định hằng số, 20 dBm)
    tx_dbm = 20.0

    # 4) SINR(dB) → SNR tuyến tính
    s_db = sinr_db(tx_dbm, pl, n_dbm)
    s_lin = 10.0 ** (s_db / 10.0)

    # 5) Shannon (nhân 0.5 để phản ánh overhead/half-duplex)
    bw = float(cfg.bandwidth_hz)
    rate_bps = 0.5 * bw * math.log2(1.0 + max(1e-9, s_lin))

    # 6) đổi sang Mbps
    return rate_bps / 1e6
