# README — UAV Wireless ML Simulator (Slim v3, UI full)

Tài liệu này trình bày **tổng thể dự án** và **cách tạo/điều khiển một mô phỏng** từ A→Z. Nội dung bám sát **full code hiện tại** (phiên bản có **UI launcher + sidebar**, benchmark pipeline, và các sửa lỗi quan trọng).

---

## 1) Tổng quan dự án

**UAV Wireless ML Simulator** là mô phỏng nhẹ cho bài toán **mạng không dây hỗ trợ bởi UAV**:
- UE (User Equipment) di chuyển ngẫu nhiên trên mặt đất.
- UAV bay ở độ cao xác định (theo waypoint hoặc tự do).
- Tốc độ liên kết (UE→UAV/BS) được ước lượng bằng Shannon dựa trên **pathloss** và **noise**.
- **Renderer OpenGL** (pyglet + PyOpenGL) trực quan hóa 3D, có HUD thống kê & FPS thủ công.
- Có chế độ **headless** để chạy không vẽ, ghi chỉ số JSON.
- **Benchmark** đo FPS và thời gian khởi tạo backend hiển thị.
- **UI mode**: màn hình chọn/tạo config (launcher) và **sidebar** hiển thị thống kê + nút Back/Toggle wires/Pause.

**Luồng xử lý chính**:

```
2 entry points:
CLI: python cli.py --config configs/default.yaml --steps 3000
UI mode: python cli_ui.py
      │
      ▼
load_config (đọc file YAML → Dict → DotDict) 
      │
      ▼
World.spawn (tạo entities (UAV, UE, BS, SAT))
      │
      ▼
Renderer.loop (chạy vòng lặp chính)
      │
      └─› Mỗi vòng: World.step(dt)
        ├─ move_ue, move_uav (physics): Cập nhật vị trí UE/UAV
        ├─ estimate_link_rate (channel): Ước lượng tốc độ link
        ├─ cập nhật packets, thống kê: Sinh/log packet, tính latency, throughput, drop
        └─ Renderer vẽ 3D + HUD/Sidebar: Renderer vẽ 3D + HUD thống kê
```

**Đơn vị mặc định**:
- Vị trí (m), vận tốc (m/s), thời gian (s).
- Nhiễu (dBm), băng thông (Hz), pathloss (dB).
- Thông lượng (Mbps).

**Sửa lỗi quan trọng**:
- `physics.py`: UAV waypoint step = `min(dist, speed*dt)` (tránh overshoot).
- `world.py`: sửa gán `best_id` khi attach UAV.

---

## 2) Cấu trúc thư mục & vai trò

```
.
├─ uwml/                     ← thư viện lõi (core library cho mô phỏng)
│   ├─ channel.py            # Mô hình kênh: pathloss (fspl/log-distance), noise, SINR, Shannon link rate
│   ├─ config.py             # Nạp YAML thành DotDict (dùng cú pháp cfg.a.b thay cho dict)
│   ├─ models.py             # Định nghĩa entity: BS, UAV, UE, Satellite; Packet; HardwareProfile
│   ├─ physics.py            # Động học: move_ue (random-walk), move_uav (theo waypoint/tự do), clamp_bounds
│   ├─ renderer_opengl.py    # Renderer 3D (pyglet + OpenGL), camera quỹ đạo, HUD, vẽ grid/axes/wires
│   ├─ viz_base.py           # Interface Renderer3DBase (chuẩn trừu tượng cho renderer 3D)
│   └─ world.py              # Quản lý toàn bộ mô phỏng: spawn entity, step update, thống kê, log packets
│
├─ benchmarks/               ← đo hiệu năng backend hiển thị (rendering framework)
│   ├─ fw_bench.py           # Runner benchmark: import backend, chạy, gom kết quả CSV
│   ├─ plot_results.py       # Vẽ biểu đồ từ CSV: plot_fps.png, plot_init.png
│   └─ fw_backends/
│       └─ pyglet_pyopengl.py# Backend benchmark pyglet+PyOpenGL: đo init_time, FPS (clear screen, vsync=False)
│
├─ tests/                    ← kiểm thử cơ bản (pytest)
│   ├─ test_bounds.py        # Kiểm tra vị trí luôn nằm trong bounds sau nhiều bước
│   ├─ test_channel.py       # Pathloss phải tăng theo khoảng cách; Noise tăng theo Bandwidth
│   ├─ test_config.py        # YAML phải có đủ các mục chính (system, world, channel, packet, …)
│   ├─ test_packet.py        # Packet log: phải sinh ra gói, cấu trúc đúng (size, priority, src/dst, timestamp)
│   └─ test_world_attach.py  # Sau vài bước, mỗi UE phải attach được UAV gần nhất
│
├─ configs/                  ← YAML cấu hình mô phỏng (có thể chọn hoặc tự tạo mới)
│   ├─ default.yaml          # Cấu hình mặc định (UE=120, UAV=3, speed UE=3.0 m/s)
│   └─ my_config.yaml        # Cấu hình người dùng tạo (UE=100, speed UE=1.5 m/s, có tx_power_dbm)
│
├─ artifacts/                ← kết quả chạy, log, và báo cáo (tự động sinh ra)
│   ├─ pytest.txt            # Kết quả chạy pytest
│   ├─ headless_stats.json   # Thống kê khi chạy headless (time, step, enq/deq, latency,…)
│   ├─ results_fw_bench.csv  # Kết quả benchmark backend
│   ├─ plot_fps.png          # Biểu đồ FPS
│   ├─ plot_init.png         # Biểu đồ thời gian khởi tạo
│   └─ phase1_validation_report.pdf # Báo cáo tổng hợp PDF
│
├─ tools/                    ← tiện ích và script phụ trợ
│   ├─ channel_sanity.py     # In bảng kiểm tra nhanh pathloss, noise, link rate
│   ├─ run_all_checks.bat    # Script batch: pytest → headless → bench → plot → PDF (tự động hoá kiểm tra)
│   └─ write_report_pdf.py   # Gom kết quả (pytest, headless, benchmark) → sinh báo cáo PDF
│
├─ quick_demo.py             # Demo nhanh: nạp default.yaml → spawn World → mở OpenGL renderer
├─ cli.py                    # Entrypoint dòng lệnh: headless (xuất JSON) hoặc render (mở 3D)
├─ cli_ui.py                 # Entrypoint có UI chọn config + sidebar điều khiển
├─ ui_launcher.py            # Màn hình chọn/tạo config mới (UI launcher đơn giản)
├─ ui_sidebar.py             # Sidebar UI: hiển thị stats + nút Back, Toggle wires, Pause/Resume
├─ channel_sanity.py         # (bản copy ngoài tools/, giữ cho gọi nhanh từ root) kiểm tra channel
└─ write_report_pdf.py       # (bản copy ngoài tools/, giữ cho gọi nhanh từ root) xuất báo cáo PDF

```

---

## 3) Cài đặt & yêu cầu hệ thống

**Python**: 3.9+ (khuyến nghị 3.10/3.11)  
**Thư viện**: `pyglet`, `PyOpenGL`, `numpy`, `PyYAML`, `matplotlib`, `reportlab`, `pytest`…

```bash
python -m pip install -r requirements.txt
```

**Lưu ý về đồ họa**
- Renderer dùng **OpenGL**. Trên máy không có GPU driver/GL hợp lệ, hãy chạy chế độ `--headless`.
- Trên macOS, Python 3.12 có thể yêu cầu thêm quyền truy cập GL; nếu lỗi hãy thử Python 3.10/3.11.

---

## 4) Cách tạo một mô phỏng (from scratch)

Bạn có 2 cách: **(A) dùng CLI** hoặc **(B) nhúng thư viện trong script của bạn**.

### A) Chạy bằng CLI (nhanh nhất)
1. Chuẩn bị YAML cấu hình (ví dụ `configs/default.yaml`, xem mẫu ở phần 5).
2. Chạy **renderer**:

   Trên Windows (PowerShell):
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   python cli.py --config configs/default.yaml --steps 3000
   
   ```
   Trên macOS/Linux (bash/zsh):
   ```bash   
   python3 -m venv .venv
   source .venv/bin/activate
   python3 -m pip install --upgrade pip
   python3 -m pip install -r requirements.txt
   
   ```
   ⚠️ Fix lỗi pyglet trên macOS/Linux:
   ```bash
   pip uninstall pyglet -y
   pip install "pyglet==1.5.27"
   python3 cli.py --config configs/default.yaml --steps 3000
   ```

   Phím tắt: `R` reset camera • `←/→/↑/↓` xoay nhìn • `+/-` zoom • `G` lưới • `W` dây liên kết • `H` HUD • `Home` auto-frame.

6. Chạy **headless** (không vẽ, in thống kê JSON):
   ```bash
   python cli.py --config configs/default.yaml --headless --steps 3000 > artifacts\headless_stats.json
   ```
7. Chạy bằng UI mode (mới)
   ```bash
   python cli_ui.py
   ```
- Launcher: chọn một config có sẵn hoặc tạo config mới (chỉnh số UE, steps, đặt tên file).
- Sidebar: trong khi mô phỏng chạy, sidebar hiển thị thống kê + nút Back, Toggle wires, Pause/Resume.

### B) Nhúng trong script của bạn
```python
from uwml.config import load_config
from uwml.world import World
from uwml.renderer_opengl import OpenGLRenderer

cfg = load_config('configs/default.yaml')  # 1) nạp YAML
w = World(cfg)                             # 2) tạo world
w.spawn()                                  # 3) sinh thực thể
OpenGLRenderer().loop(w, cfg.system.dt, cfg.system.steps)  # 4) chạy render
```

**Luồng mô phỏng mỗi bước (`World.step`)**
- cập nhật vị trí UE/UAV (`physics`)
- sinh gói theo xác suất, ước lượng thông lượng (`channel`) → tính độ trễ → ghi thống kê & log
- tiến thời gian, tăng chỉ số bước

---

## 5) Mẫu cấu hình YAML (tham khảo nhanh)

```yaml
system:
  dt: 0.05           # bước thời gian (s)
  steps: 1000        # số bước mô phỏng

time:
  seed: 123          # tái lập kết quả (tùy chọn)

world:
  bounds: [-200, 200, -200, 200, 0, 200]  # hộp biên 3D
  n_uav: 4        # fallback nếu uav.count không đặt
  n_ue: 80        # fallback nếu ue.count không đặt
  satellites: []  # hoặc danh sách [x, y, z]

uav:
  count: 4
  altitude_m: 60
  speed_mps: 8
  waypoints: null  # danh sách điểm 3D hoặc null

ue:
  count: 120
  speed_mps: 3
  turn_std_deg: 25

mobility:              # fallback khi các trường trên không đặt
  ue_speed_mps: 3
  ue_turn_std_deg: 25
  uav_speed_mps: 8
  uav_waypoints: null

channel:
  model: log_distance          # hoặc fspl
  ref_pathloss_db: 40
  pathloss_exp: 3.2
  ref_distance_m: 1
  bandwidth_hz: 5_000_000
  noise_figure_db: 6
  carrier_hz: 2_400_000_000    # dùng khi model=fspl

packet:
  size_bytes: 1200
  gen_prob_per_step: 0.15
  max_log: 1000

hardware:              # chỉ để HUD
  cpu_cores: 8
  gpu_tflops_est: 10.5
  mem_gb: 32

viz:
  uav_column_height: 60
```

---

## 6) Kiến trúc mã & điểm mở rộng

### `uwml/world.py`
- `spawn()`: bố trí UAV theo vòng tròn, UE ngẫu nhiên; đọc `world.satellites` để tạo vệ tinh.
- `step(dt)`: di chuyển UE/UAV → sinh/lập nhật gói → thống kê.
- **Mở rộng**: thêm lịch truyền (queue thật), lập lịch MAC, rơi gói, can nhiễu,…

### `uwml/channel.py`
- Pathloss: `fspl` hoặc `log_distance`.
- Nhiễu: `-174 dBm/Hz + 10log10(BW) + NF`.
- `estimate_link_rate`: Shannon (x0.5 overhead).
- **Mở rộng**: shadowing, fast/slow fading, interference từ nhiều nguồn.

### `uwml/physics.py`
- `move_ue` random-walk mượt (Gaussian turn).
- `move_uav` tới waypoint không vượt đích, hoặc bay tự do.
- **Mở rộng**: ràng buộc động lực học UAV, tránh va chạm, bám mục tiêu.

### `uwml/renderer_opengl.py`
- Camera quỹ đạo, HUD, dây liên kết, cột UAV.
- **Mở rộng**: shader, model 3D UAV, nhãn tên, bản đồ nền, chọn thực thể bằng chuột.

---

## 7) Chế độ headless & thống kê

Khi chạy với `--headless`, simulator in JSON ví dụ:
```json
{
  "time_s": 150.0,
  "step": 3000,
  "enqueued": 425,
  "dequeued": 425,
  "dropped": 0,
  "avg_latency_s": 0.0123,
  "max_latency_s": 0.0531,
  "packets_logged": 425
}
```
Các trường này đến từ `World.stats` và hàng đợi `World.packets`.

---

## 8) Benchmark & biểu đồ

Chạy benchmark hiển thị (Phase-1 chỉ có backend `pyglet_pyopengl`):
```bash
python -m benchmarks.fw_bench --duration 8 --csv artifacts/results_fw_bench.csv
python -m benchmarks.plot_results artifacts/results_fw_bench.csv
```
Tạo `plot_fps.png` và `plot_init.png` trong thư mục làm việc.

---

## 9) Kiểm thử

Chạy toàn bộ:
```bash
python -m pytest
```

---

## 10) Tools tạo đủ artifact (one‑click)

```bash
tools\run_all_checks.bat
```
Sinh: `pytest.txt`, `headless_stats.json`, `results_fw_bench.csv`, `plot_fps.png`, `plot_init.png`, `phase1_validation_report.pdf`.

---

## 11) FAQ & lỗi thường gặp

**Q: Mở renderer báo lỗi OpenGL/GLX/WGL?**  
A: Kiểm tra driver GPU, chạy trong môi trường có OpenGL. Nếu không có, dùng `--headless`.

**Q: FPS thấp?**  
A: Tắt vsync (đã tắt trong benchmark), giảm số UE/UAV, giảm kích thước cửa sổ.

**Q: Không thấy vệ tinh (dấu chấm cam)?**  
A: Đặt `world.satellites` trong YAML, ví dụ `[0, 0, 800]`. Muốn ẩn, để mảng rỗng hoặc bỏ vẽ ở renderer.

**Q: Muốn tự điều khiển waypoint UAV?**  
A: Đặt `uav.waypoints` là danh sách điểm 3D. Mặc định `move_uav` sẽ đi lần lượt, không overshoot.

---
