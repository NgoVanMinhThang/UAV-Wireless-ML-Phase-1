# -*- coding: utf-8 -*-
"""Backend benchmark cho stack hiển thị: pyglet + PyOpenGL.

Mục tiêu đo 2 thứ:
1) Thời gian khởi tạo context (init_time_s) — từ lúc bắt đầu tới khi có thể vẽ khung đầu tiên.
2) FPS (khung/giây) khi chỉ clear màn hình (không vẽ hình học) trong duration_s giây, với vsync=False.

Lưu ý:
- Dùng cửa sổ 'visible=False' để không bật UI thật nhưng vẫn có context OpenGL hợp lệ.
- pyglet.clock.schedule_interval(...) được bật để mô phỏng vòng đời app (dù callback rỗng).
"""
import time
import pyglet
from OpenGL import GL


def run(duration_s: float = 8.0, n_uav: int = 5, n_ue: int = 300):
    """Chạy benchmark nhanh cho backend pyglet+PyOpenGL.

    Args:
        duration_s: tổng thời gian đo FPS (giây).
        n_uav, n_ue: tham số “tải” hình thức cho giao diện CLI/csv (không dùng trong loop này).

    Returns:
        dict chứa:
            - backend: tên backend
            - available: True nếu khởi tạo thành công
            - fps: số khung/giây đo được
            - init_time_s: thời gian khởi tạo context (s)
    """
    # ---- 1) Khởi tạo context & vẽ khung đầu để đảm bảo GL state sẵn sàng ----
    t0 = time.perf_counter()
    cfg = pyglet.gl.Config(double_buffer=True, depth_size=24)  # depth buffer 24-bit
    # vsync=False để đo FPS “thô” không bị giới hạn bởi refresh rate màn hình
    win = pyglet.window.Window(640, 480, visible=False, config=cfg, vsync=False)

    @win.event
    def on_draw():
        # Clear cả color và depth để giả lập bước vẽ tối thiểu
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    # Đăng lịch 1 callback rỗng -> kích hoạt bộ đếm thời gian nội bộ của pyglet
    pyglet.clock.schedule_interval(lambda dt: None, 1 / 120.0)

    # Chuỗi gọi tối thiểu để bảo đảm context/handlers đã hoạt động
    win.switch_to()
    win.dispatch_events()
    win.dispatch_event("on_draw")
    win.flip()

    init_time_s = time.perf_counter() - t0  # thời gian từ start → khung hình đầu tiên

    # ---- 2) Đo FPS trong duration_s giây ----
    frames, t0 = 0, time.perf_counter()
    while (time.perf_counter() - t0) < float(duration_s):
        # Tick đồng hồ để chạy các scheduled callbacks
        pyglet.clock.tick()
        # Vẽ 1 khung “clear”
        win.switch_to()
        win.dispatch_events()
        win.dispatch_event("on_draw")
        win.flip()
        frames += 1

    elapsed = max(1e-6, time.perf_counter() - t0)  # chống chia 0
    fps = frames / elapsed

    # Dọn cửa sổ (an toàn)
    try:
        win.close()
    except Exception:
        pass

    # Trả kết quả chuẩn hóa
    return {
        "backend": "pyglet_pyopengl",
        "available": True,
        "fps": round(fps, 1),
        "init_time_s": round(init_time_s, 4),
    }
