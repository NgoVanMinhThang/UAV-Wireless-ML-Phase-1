# -*- coding: utf-8 -*-
"""Kiểm thử cấu trúc file cấu hình: phải có đủ các mục chính."""
from uwml.config import load_config

def test_config_sections():
    cfg = load_config('configs/default.yaml')

    # Các phần bắt buộc tối thiểu cho mô phỏng
    for sec in ('system', 'world', 'channel', 'packet'):
        assert hasattr(cfg, sec)

    # Các phần tùy chọn nhưng được kỳ vọng có trong mẫu mặc định
    for sec in ('time', 'hardware', 'uav', 'ue', 'viz'):
        assert hasattr(cfg, sec)
