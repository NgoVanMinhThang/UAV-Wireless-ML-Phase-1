# Nghiên cứu khung hiển thị 3D (Task‑2)

## 1) Benchmark mini (kết quả)
- **Backend**: `pyglet_pyopengl`
- **FPS**: ~ **2204.6**
- **Init time**: ~ **0.3496 s**

![plot_fps.png](/mnt/data/plot_fps.png)

![plot_init.png](/mnt/data/plot_init.png)

## 2) Cách tái tạo

```bat
py -m benchmarks.fw_bench --duration 8 --n_uav 5 --n_ue 300 --csv artifacts\results_fw_bench.csv
py benchmarks\plot_results.py artifacts\results_fw_bench.csv
```

**Gợi ý**: Tăng `--n_ue` để thấy FPS giảm; nếu FPS bị khoá 60 kiểm tra vsync/driver.

## 3) Đánh giá nhanh (định tính)
PyOpenGL + pyglet đáp ứng Phase‑1 (đơn giản/ổn định/dễ tích hợp). ModernGL là hướng nâng cấp khi cần instancing/shader & hiệu năng cao.
