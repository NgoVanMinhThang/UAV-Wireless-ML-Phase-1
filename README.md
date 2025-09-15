# README — UAV Wireless ML Simulator (Slim v3)

Tài liệu này trình bày **tổng thể dự án** và **cách tạo/điều khiển một mô phỏng** từ A→Z. Nội dung bám đúng mã nguồn đã có trong repo.

---

## 1) Tổng quan dự án

**UAV Wireless ML Simulator** là một mô phỏng nhẹ (Slim v3) cho bài toán **mạng không dây hỗ trợ bởi UAV**:
- UE (User Equipment) di chuyển ngẫu nhiên trên mặt đất.
- UAV bay ở độ cao xác định (tự do hoặc theo waypoint).
- Tốc độ liên kết (UE→UAV/BS) được ước lượng bởi công thức Shannon dựa trên mô hình **pathloss** và **noise**.
- **Renderer OpenGL** trực quan hóa 3D theo thời gian thực (pyglet + PyOpenGL) kèm **HUD** thống kê.
- Có chế độ **headless** để chạy không vẽ, ghi nhận các chỉ số (thời gian, độ trễ gói,…).
- Bộ **benchmark** đơn giản đo FPS và thời gian khởi tạo backend hiển thị.

**Luồng xử lý chính**

```
2 entry points:
CLI: python cli.py --config configs/default.yaml --steps 3000
quick_demo: python -m examples.quick_demo
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
        └─ Renderer vẽ HUD + hình học: Renderer vẽ 3D + HUD thống kê
```

**Đơn vị mặc định**
- Vị trí (m), vận tốc (m/s), thời gian (s)
- Nhiễu (dBm), băng thông (Hz), pathloss (dB)
- Thông lượng trả về **Mbps**

---

## 2) Cấu trúc thư mục & vai trò

```
.
├─ uwml/                     ← thư viện lõi
│   ├─ channel.py            # pathloss, nhiễu, SINR, Shannon link rate
│   ├─ config.py             # nạp YAML thành DotDict (truy cập dấu chấm)
│   ├─ models.py             # Entity: BS, UAV, UE, Satellite; Packet; HardwareProfile
│   ├─ physics.py            # move_ue (random-walk), move_uav (free/waypoints), clamp_bounds
│   ├─ renderer_opengl.py    # renderer 3D (pyglet + PyOpenGL), HUD, camera quỹ đạo
│   ├─ viz_base.py           # interface Renderer3DBase
│   └─ world.py              # World: spawn(), step(), Stats, log packets
├─ benchmarks/               ← đo backend hiển thị
│   ├─ fw_bench.py           # chạy benchmark, gom kết quả CSV
│   ├─ plot_results.py       # vẽ biểu đồ từ CSV
│   └─ fw_backends/
│       └─ pyglet_pyopengl.py# đo init_time & FPS (clear screen)
├─ tests/                    ← kiểm thử cơ bản
│   ├─ test_bounds.py        # vị trí luôn trong bounds
│   ├─ test_channel.py       # pathloss tăng theo d, noise tăng theo BW
│   ├─ test_config.py        # YAML có các mục chính
│   ├─ test_packet.py        # packets có log sau khi chạy
│   └─ test_world_attach.py  # UE bám UAV gần nhất
├─ configs/                  ← YAML cấu hình mô phỏng (bạn cung cấp)
├─ artifacts/                ← kết quả chạy (csv, ảnh plot, pdf, …)
├─ quick_demo.py             ← demo chạy renderer ngay
├─ cli.py                    ← entrypoint dòng lệnh (headless / render)
├─ channel_sanity.py         ← in bảng pathloss/noise/rate kiểm tra nhanh
└─ write_report_pdf.py       ← tổng hợp báo cáo PDF
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

## 10) FAQ & lỗi thường gặp

**Q: Mở renderer báo lỗi OpenGL/GLX/WGL?**  
A: Kiểm tra driver GPU, chạy trong môi trường có OpenGL. Nếu không có, dùng `--headless`.

**Q: FPS thấp?**  
A: Tắt vsync (đã tắt trong benchmark), giảm số UE/UAV, giảm kích thước cửa sổ.

**Q: Không thấy vệ tinh (dấu chấm cam)?**  
A: Đặt `world.satellites` trong YAML, ví dụ `[0, 0, 800]`. Muốn ẩn, để mảng rỗng hoặc bỏ vẽ ở renderer.

**Q: Muốn tự điều khiển waypoint UAV?**  
A: Đặt `uav.waypoints` là danh sách điểm 3D. Mặc định `move_uav` sẽ đi lần lượt, không overshoot.

---
