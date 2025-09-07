import time
import pyglet
from OpenGL import GL

def run(duration_s=8.0, n_uav=5, n_ue=300):
    """
    Benchmark pyglet + PyOpenGL:
    - Đo thời gian khởi tạo context (init_time_s)
    - Render clear() trong vòng lặp duration_s để lấy FPS (vsync=False)
    """
    t0 = time.perf_counter()
    cfg = pyglet.gl.Config(double_buffer=True, depth_size=24)
    win = pyglet.window.Window(640, 480, visible=False, config=cfg, vsync=False)

    @win.event
    def on_draw():
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    # Bật clock để tiến hàm scheduled (dù không dùng)
    pyglet.clock.schedule_interval(lambda dt: None, 1/120.0)

    # Gọi một vòng vẽ đầu tiên để đảm bảo context/GL state sẵn sàng
    win.switch_to()
    win.dispatch_events()
    win.dispatch_event("on_draw")
    win.flip()

    init_time_s = time.perf_counter() - t0

    # Đo FPS
    frames, t0 = 0, time.perf_counter()
    while (time.perf_counter() - t0) < float(duration_s):
        pyglet.clock.tick()
        win.switch_to()
        win.dispatch_events()
        win.dispatch_event("on_draw")
        win.flip()
        frames += 1

    elapsed = max(1e-6, time.perf_counter() - t0)
    fps = frames / elapsed

    try:
        win.close()
    except Exception:
        pass

    return {
        "backend": "pyglet_pyopengl",
        "available": True,
        "fps": round(fps, 1),
        "init_time_s": round(init_time_s, 4),
    }
