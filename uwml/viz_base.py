# -*- coding: utf-8 -*-
"""Giao diện trừu tượng cho renderer 3D."""
from __future__ import annotations


class Renderer3DBase:
    def loop(self, world, dt: float, steps: int):
        """Bắt đầu vòng lặp hiển thị (phải được lớp con cài đặt)."""
        raise NotImplementedError
