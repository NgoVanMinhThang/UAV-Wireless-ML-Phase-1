# UAV Wireless-ML — Giai đoạn 1 (Slim)

Mô phỏng Phase‑1 theo đề cương: môi trường 3D (BS/UAV/Satellite/UE), kênh LoS + log‑distance (toy), UE random‑walk, UAV waypoint, gói metadata, HUD thống kê; cấu hình YAML + API mở.

## 1) Cài đặt & chạy nhanh

```bat
py -m venv .venv
.\.venv\Scripts\activate
py -m pip install --upgrade pip
py -m pip install -r requirements.txt

py cli.py --config configs\default.yaml --steps 200
```
Điều khiển: Chuột (orbit/zoom/pan), `HOME` (auto-frame), `R` (reset cam), `G` (Grid), `W` (Link), `H` (HUD), `ESC` (thoát).

**Headless**:
```bat
py cli.py --config configs\default.yaml --steps 600 --headless > artifacts\headless_stats.json
```

## 2) Kết quả kiểm thử (từ artifact)
- **Headless stats**:
  - `time_s = 60`
  - `step = 600`
  - `enqueued = 14543`
  - `dequeued = 14543`
  - `dropped = 0`
  - `avg_latency_s = 0.000232756`
  - `max_latency_s = 0.000274891`
  - `packets_logged = 1000`

- **Benchmark viewer** (pyglet + PyOpenGL, vsync=False):
  - `backend = pyglet_pyopengl`
  - `fps = 2204.6`
  - `init_time_s = 0.3496`
  - `available = True`

![plot_fps.png](/mnt/data/plot_fps.png)

![plot_init.png](/mnt/data/plot_init.png)


## 3) Tạo đủ artifact (one‑click)

```bat
tools\run_all_checks.bat
```
Sinh: `pytest.txt`, `headless_stats.json`, `results_fw_bench.csv`, `plot_fps.png`, `plot_init.png`, `phase1_validation_report.pdf`.

## 4) Con số kênh (bổ sung)
Sinh file:
```bat
py tools\channel_sanity.py > artifacts\channel_summary.txt
```
Dán bảng Pathloss/Noise/LinkRate vào README để đối chiếu.
