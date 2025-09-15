# -*- coding: utf-8 -*-
"""Tiện ích nạp YAML → đối tượng truy cập bằng dấu chấm (DotDict)."""
from __future__ import annotations
import yaml, types


class DotDict(types.SimpleNamespace):
    """Bọc dict lồng nhau thành SimpleNamespace để dùng cú pháp cfg.a.b."""

    @classmethod
    def from_dict(cls, d):
        """Đệ quy chuyển dict → DotDict (giữ nguyên kiểu với giá trị không phải dict)."""
        ns = cls()
        for k, v in d.items():
            setattr(ns, k, cls.from_dict(v) if isinstance(v, dict) else v)
        return ns


def load_config(path: str):
    """Đọc file YAML ở `path` và trả về DotDict tương ứng."""
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return DotDict.from_dict(data)
