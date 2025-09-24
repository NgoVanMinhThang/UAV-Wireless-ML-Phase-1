# -*- coding: utf-8 -*-
"""Các thực thể (entity) trong thế giới mô phỏng + vài kiểu dữ liệu phụ trợ."""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass


class Entity:
    """Thực thể cơ sở có id, vị trí (pos 3D) và vận tốc (vel 3D)."""

    def __init__(self, id: int, pos, vel=(0, 0, 0)):
        self.id = id
        self.pos = np.array(pos, dtype=np.float32)  # [x, y, z]
        self.vel = np.array(vel, dtype=np.float32)  # [vx, vy, vz]

    def update(self, dt: float):
        """Tích phân tiến: x <- x + v * dt (mô hình đơn giản)."""
        self.pos = self.pos + self.vel * dt


class BS(Entity):
    """Base Station (trạm gốc)."""
    pass


class Satellite(Entity):
    """Vệ tinh."""
    pass


class UAV(Entity):
    """UAV/Drone bay.”

    - _way_idx: con trỏ waypoint hiện tại (nếu chạy theo lộ trình).
    """
    def __init__(self, id: int, pos, vel=(0, 0, 0)):
        super().__init__(id, pos, vel)
        self._way_idx = 0


class UE(Entity):
    """Thiết bị người dùng (User Equipment)."""

    def __init__(self, id: int, pos, vel=(0, 0, 0)):
        super().__init__(id, pos, vel)
        self.attached_uav_id = None  # id UAV mà UE đang "bám" (nearest)


@dataclass
class Packet:
    """Bản ghi gói đơn giản để log."""
    size_bytes: int
    priority: int
    src_id: int
    dst_id: int
    timestamp: float


@dataclass
class HardwareProfile:
    """Thông số phần cứng (dùng hiển thị HUD)."""
    cpu_cores: int
    gpu_tflops_est: float
    mem_gb: int
