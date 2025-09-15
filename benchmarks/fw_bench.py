# -*- coding: utf-8 -*-
"""Trình chạy benchmark khung hiển thị (framework bench).

- Load các backend (ở thư mục benchmarks/fw_backends) bằng import động.
- Chạy từng backend, gom kết quả và ghi ra CSV.
- In ra console tóm tắt cho nhanh.

Sử dụng:
    python -m benchmarks.fw_bench --duration 8 --csv results_fw_bench.csv
"""
import os, sys, importlib, csv, argparse, traceback

# Khi chạy trực tiếp file này, thêm thư mục cha vào sys.path
# để có thể import 'benchmarks.fw_backends.xxx' thành công.
if __package__ is None or __package__ == "":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    __package__ = "benchmarks"

# Danh sách backend cần chấm. Phase-1 chỉ có pyglet_pyopengl.
BACKENDS = ["pyglet_pyopengl"]


def _load_backend(name: str):
    """Import mô-đun backend theo tên.

    Ưu tiên import nội bộ dạng '.fw_backends.name' (khi chạy như package),
    nếu lỗi thì fallback sang 'benchmarks.fw_backends.name' (khi sửa đường dẫn thủ công).
    """
    try:
        return importlib.import_module(f".fw_backends.{name}", package=__package__)
    except Exception:
        return importlib.import_module(f"benchmarks.fw_backends.{name}")


def main():
    # --- CLI ---
    ap = argparse.ArgumentParser()
    ap.add_argument('--duration', type=float, default=8.0, help='thời gian đo FPS (s)')
    ap.add_argument('--n_uav', type=int, default=5, help='tham số tải giả')
    ap.add_argument('--n_ue', type=int, default=300, help='tham số tải giả')
    ap.add_argument('--csv', default='results_fw_bench.csv', help='đường dẫn file CSV kết quả')
    args = ap.parse_args()

    rows = []
    for name in BACKENDS:
        try:
            # Mỗi backend định nghĩa hàm run(...)
            m = _load_backend(name)
            res = m.run(duration_s=args.duration, n_uav=args.n_uav, n_ue=args.n_ue)
            # Bảo đảm có các khóa tối thiểu
            res.setdefault('backend', name)
            res.setdefault('available', True)
        except Exception as e:
            # Nếu backend lỗi (không khả dụng), ghi thông tin để phân tích
            res = {
                'backend': name,
                'available': False,
                'error': repr(e),
                # Lọc 6 dòng cuối trace cho ngắn gọn
                'trace': ''.join(tr for tr in traceback.format_exc().splitlines()[-6:])
            }
        rows.append(res)
        print(res)  # echo từng kết quả ra console

    # --- Ghi CSV ---
    keys = sorted({k for r in rows for k in r.keys()})  # union tất cả cột
    with open(args.csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print('Wrote', args.csv)


if __name__ == '__main__':
    main()
