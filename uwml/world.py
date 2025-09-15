# -*- coding: utf-8 -*-
"""Mô-đun 'world' giữ toàn bộ trạng thái mô phỏng:
- Biên không gian (bounds), các thực thể (BS/UAV/UE/SAT)
- Sinh thực thể ban đầu (spawn)
- Hàm step() để tiến mô phỏng theo thời gian dt
- Thống kê (enqueued/dequeued/latency) để hiển thị HUD hay in ra JSON
"""
from __future__ import annotations
import numpy as np, random, math
from dataclasses import dataclass
from collections import deque

from .config import DotDict
from .models import BS, UAV, UE, Satellite, Packet, HardwareProfile
from .physics import move_ue, move_uav
from .channel import estimate_link_rate


@dataclass
class Stats:
    """Các bộ đếm thống kê toàn cục của mô phỏng.
    - time_s: thời gian mô phỏng đã trôi qua (giây)
    - step: số bước mô phỏng đã chạy
    - enqueued: số gói được "sinh" ra (enqueue)
    - dequeued: số gói coi như đã truyền xong (dequeue)
    - dropped: số gói rơi (chưa dùng trong mô hình tối giản này)
    - sum_latency_s: tổng độ trễ (giây) để tính trung bình
    - count_latency: số mẫu độ trễ đã ghi nhận
    - max_latency_s: độ trễ lớn nhất quan sát được
    """
    time_s: float = 0.0
    step: int = 0
    enqueued: int = 0
    dequeued: int = 0
    dropped: int = 0
    sum_latency_s: float = 0.0
    count_latency: int = 0
    max_latency_s: float = 0.0


class World:
    """Bao toàn bộ 'thế giới mô phỏng': cấu hình, thực thể, thống kê, và vòng đời."""

    def __init__(self, cfg: DotDict):
        """Khởi tạo vùng nhớ + tham chiếu cấu hình."""
        self.cfg = cfg
        # Hộp biên không gian (x0, x1, y0, y1, z0, z1) dùng để kẹp vị trí
        self.bounds = np.array(cfg.world.bounds, dtype=np.float32)

        # Thông tin phần cứng (chỉ để hiển thị lên HUD; không ảnh hưởng mô phỏng)
        hw = getattr(cfg, "hardware", DotDict(cpu_cores=0, gpu_tflops_est=0.0, mem_gb=0))
        self.hw = HardwareProfile(hw.cpu_cores, hw.gpu_tflops_est, hw.mem_gb)

        # Tập thực thể ban đầu (BS tại gốc tọa độ; các list còn lại trống)
        self.bs = BS(0, [0, 0, 0])
        self.uav = []
        self.ue = []
        self.sat = []

        # Thống kê + nhật ký gói
        self.stats = Stats()
        self.packets = deque(maxlen=getattr(cfg.packet, "max_log", 1000))

        # Ghim seed ngẫu nhiên (nếu có) để tái lập kết quả khi chạy lại
        if hasattr(cfg, "time") and hasattr(cfg.time, "seed"):
            random.seed(int(cfg.time.seed))

    def spawn(self):
        """Sinh thực thể ban đầu theo cấu hình (UAV/UE/Satellite)."""
        # --- UAV ---
        uv = getattr(self.cfg, "uav", None)
        # Số lượng UAV: ưu tiên self.cfg.uav.count; fallback self.cfg.world.n_uav
        n_uav = uv.count if (uv and hasattr(uv, "count")) else getattr(self.cfg.world, "n_uav", 0)
        # Độ cao mặc định của UAV (m)
        alt = uv.altitude_m if (uv and hasattr(uv, "altitude_m")) else 60.0
        # Bán kính bố trí UAV theo vòng tròn (35% cạnh nhỏ hơn của vùng mô phỏng)
        rad = min(abs(self.bounds[1] - self.bounds[0]),
                  abs(self.bounds[3] - self.bounds[2])) * 0.35

        # Bố trí UAV quanh vòng tròn, chia đều theo góc
        for i in range(n_uav):
            a = 2 * math.pi * i / max(1, n_uav)
            pos = [rad * math.cos(a), rad * math.sin(a), alt]
            self.uav.append(UAV(i + 1, pos))

        # --- UE ---
        ue_cfg = getattr(self.cfg, "ue", None)
        # Số lượng UE: ưu tiên self.cfg.ue.count; fallback self.cfg.world.n_ue
        n_ue = ue_cfg.count if (ue_cfg and hasattr(ue_cfg, "count")) else getattr(self.cfg.world, "n_ue", 0)

        # Phân bố UE ngẫu nhiên trên mặt phẳng (z = 0)
        for j in range(n_ue):
            import random as _r
            x = _r.uniform(self.bounds[0], self.bounds[1])
            y = _r.uniform(self.bounds[2], self.bounds[3])
            self.ue.append(UE(j, [x, y, 0.0]))

        # --- Vệ tinh (tùy chọn) ---
        sats = getattr(self.cfg.world, "satellites", []) or []
        for k, p in enumerate(sats):
            self.sat.append(Satellite(k, p))

    def _nearest_uav_pos(self, p):
        """Trả về vị trí UAV gần nhất với điểm 3D p (nếu không có UAV → trả vị trí BS)."""
        if not self.uav:
            return self.bs.pos
        dmin = 1e9
        best = self.uav[0].pos
        for a in self.uav:
            # Khoảng cách Euclid từ p tới UAV a
            d = float(np.linalg.norm(a.pos - p))
            if d < dmin:
                dmin, best = d, a.pos
        return best

    def step(self, dt: float):
        """Chạy 1 bước mô phỏng trong khoảng thời gian dt (giây).

        Trình tự:
        1) Đọc tham số mobility (tốc độ UE/UAV, độ đổi hướng, waypoint)
        2) Cập nhật động học UE/UAV
        3) Với mỗi UE, có xác suất phát sinh gói → ước lượng tốc độ link & độ trễ
        4) Cập nhật thống kê & tiến thời gian
        """
        mcfg = self.cfg

        # --- 1) Đọc tham số di chuyển (ưu tiên trong ue./uav., nếu thiếu thì fallback mobility.*) ---
        ue_speed = getattr(getattr(mcfg, "ue", None), "speed_mps",
                           getattr(mcfg, "mobility", DotDict()).__dict__.get("ue_speed_mps", 3.0))
        ue_turn = getattr(getattr(mcfg, "ue", None), "turn_std_deg",
                          getattr(mcfg, "mobility", DotDict()).__dict__.get("ue_turn_std_deg", 25.0))
        uav_speed = getattr(getattr(mcfg, "uav", None), "speed_mps",
                            getattr(mcfg, "mobility", DotDict()).__dict__.get("uav_speed_mps", 8.0))
        uav_wps = getattr(getattr(mcfg, "uav", None), "waypoints",
                          getattr(mcfg, "mobility", DotDict()).__dict__.get("uav_waypoints", None))

        # --- 2) Cập nhật động học ---
        for u in self.ue:
            # Random-walk mượt trong mặt phẳng, z=0; giữ trong bounds
            move_ue(u, dt, self, speed=ue_speed, turn_std_deg=ue_turn)
        for a in self.uav:
            # Bay tự do hoặc theo waypoint; giữ trong bounds
            move_uav(a, dt, self, speed=uav_speed, waypoints=uav_wps)

        # --- 3) Sinh lưu lượng + ước lượng độ trễ truyền ---
        pcfg = self.cfg.packet
        for u in self.ue:
            # Tìm đích gần nhất (UAV gần nhất; nếu không có UAV thì BS)
            dst = self._nearest_uav_pos(u.pos)

            # Ghi nhận id UAV gần nhất để hiển thị trạng thái bám (attached)
            best_id = 0
            dmin = 1e9
            for a in self.uav:
                d = float(np.linalg.norm(a.pos - u.pos))
                if d < dmin:
                    dmin, best_id = d, a.id   # FIX: sửa lỗi gõ 'dmin, best_id=d, a.id'
            u.attached_uav_id = best_id if self.uav else 0

            # Xác suất phát sinh gói ở bước này
            import random as _r
            if _r.random() < pcfg.gen_prob_per_step:
                self.stats.enqueued += 1

                # Ước lượng tốc độ liên kết (Mbps) theo Shannon
                rate = estimate_link_rate(u.pos, dst, self.cfg.channel)

                # Thời gian truyền (giây): kích thước (bit) / thông lượng (bit/s)
                size_bits = pcfg.size_bytes * 8.0
                tx_time = size_bits / max(1e-6, rate * 1e6)

                # Mô hình tối giản: phát sinh là coi như truyền xong (không có hàng đợi)
                self.stats.dequeued += 1
                self.stats.sum_latency_s += tx_time
                self.stats.count_latency += 1
                if tx_time > self.stats.max_latency_s:
                    self.stats.max_latency_s = tx_time

                # Ghi log gói để có thể kiểm tra lại sau
                self.packets.append(
                    Packet(
                        pcfg.size_bytes,
                        int(getattr(pcfg, "priority", 1)),  # ưu tiên (nếu có)
                        int(u.id),
                        int(u.attached_uav_id),
                        float(self.stats.time_s),
                    )
                )

        # --- 4) Tiến thời gian mô phỏng & tăng chỉ số bước ---
        self.stats.time_s += dt
        self.stats.step += 1
