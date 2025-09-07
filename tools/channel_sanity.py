from uwml.config import load_config
from uwml.channel import pathloss_db, noise_power_dbm, estimate_link_rate

cfg = load_config("configs/default.yaml")

# 1) Bảng pathloss
distances = [1, 5, 10, 50, 100]
print("== Pathloss (dB) ==")
for d in distances:
    print(f"{d:>4} m -> {pathloss_db(d, cfg.channel):.2f} dB")

# 2) Noise cho BW/NF hiện tại
n_dbm = noise_power_dbm(cfg.channel.bandwidth_hz, cfg.channel.noise_figure_db)
print("\n== Noise ==")
print(f"Bandwidth: {cfg.channel.bandwidth_hz} Hz  |  NF: {cfg.channel.noise_figure_db} dB")
print(f"Noise(dBm): {n_dbm:.2f}")

# 3) LinkRate @ một vài khoảng cách
print("\n== LinkRate (Mbps) ==")
for d in [5, 10, 50, 100]:
    rate = estimate_link_rate([0,0,0],[d,0,0], cfg.channel)
    print(f"d={d:>3} m -> {rate:.3f} Mbps")
