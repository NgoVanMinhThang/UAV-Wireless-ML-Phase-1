# -*- coding: utf-8 -*-
"""Động học đơn giản cho UE (random-walk) và UAV (tự do/waypoint)."""
from __future__ import annotations
import numpy as np, math, random


def clamp_bounds(p, b):
    """Ép vị trí p = [x,y,z] nằm trong hộp biên b = (x0, x1, y0, y1, z0, z1)."""
    x0, x1, y0, y1, z0, z1 = b
    p[0] = min(max(p[0], x0), x1)
    p[1] = min(max(p[1], y0), y1)
    p[2] = min(max(p[2], z0), z1)
    return p


def move_ue(ue, dt, world, speed=3.0, turn_std_deg=25.0):
    """Random-walk mượt cho UE trên mặt phẳng z=0.

    - Nếu chưa có hướng, gán ngẫu nhiên.
    - Mỗi bước đổi hướng theo phân phối Gauss (độ lệch chuẩn turn_std_deg).
    - Vận tốc có độ lớn = speed, hướng theo góc hiện tại.
    """
    if not hasattr(ue, "_dir_rad"):
        ue._dir_rad = random.uniform(0, 2 * math.pi)

    # Đổi hướng chút ít để đường đi tự nhiên
    ue._dir_rad += math.radians(random.gauss(0, turn_std_deg))

    # Vận tốc trong mặt phẳng (z = 0)
    v = np.array(
        [math.cos(ue._dir_rad), math.sin(ue._dir_rad), 0.0], dtype=np.float32
    ) * speed

    ue.vel = v
    ue.update(dt)  # x <- x + v*dt
    clamp_bounds(ue.pos, world.bounds)  # giữ trong hộp biên


def move_uav(uav, dt, world, speed=8.0, waypoints=None):
    """Điều khiển UAV.

    - Nếu không có waypoint: bay theo vận tốc hiện tại.
    - Nếu có waypoint: hướng tới điểm đích hiện tại, không vượt quá step = min(dist, speed*dt).
    """
    if not waypoints:
        uav.update(dt)
        clamp_bounds(uav.pos, world.bounds)
        return

    # Đích hiện tại: quay vòng qua danh sách waypoint
    tgt = waypoints[uav._way_idx % len(waypoints)]
    d = np.array(tgt, dtype=np.float32) - uav.pos
    dist = float(np.linalg.norm(d))

    if dist < 1e-3:
        # Đến nơi → chuyển waypoint kế
        uav._way_idx += 1
        return

    dir = d / max(1e-6, dist)  # vector đơn vị hướng tới đích
    uav.vel = dir * speed

    # FIXME (mã gốc bị thiếu): dòng dưới trong file của bạn đang là `step=min(dist,speed...t)`
    # Gợi ý đúng là: step = min(dist, speed * dt)
    step = min(dist, speed * dt)

    # Cập nhật vị trí theo bước không vượt quá đích
    uav.pos = uav.pos + dir * step
    clamp_bounds(uav.pos, world.bounds)
