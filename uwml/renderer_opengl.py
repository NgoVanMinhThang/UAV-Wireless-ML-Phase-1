# -*- coding: utf-8 -*-
"""Renderer 3D sử dụng pyglet + OpenGL.

Nhiệm vụ:
- Tạo cửa sổ hiển thị thế giới mô phỏng UAV/UE/BS/Satellite.
- Camera kiểu quỹ đạo: yaw, pitch, dist quanh một target.
- Vẽ lưới + trục tọa độ, các thực thể, dây liên kết, và HUD thống kê.
"""
from __future__ import annotations
import math, time, numpy as np

import pyglet
from pyglet.window import key, mouse
from OpenGL import GL

from .viz_base import Renderer3DBase


# -------------------- Ma trận tiện ích --------------------
def perspective(fovy_deg, aspect, znear, zfar):
    """Ma trận chiếu phối cảnh (perspective projection)."""
    f = 1.0 / math.tan(math.radians(fovy_deg) / 2.0)
    a = (zfar + znear) / (znear - zfar)
    b = (2 * zfar * znear) / (znear - zfar)
    return np.array([[f/aspect, 0, 0, 0],
                     [0, f, 0, 0],
                     [0, 0, a, b],
                     [0, 0, -1, 0]], dtype=np.float32)

def look_at(eye, target, up=(0, 0, 1)):
    """View matrix kiểu gluLookAt (mắt, điểm nhìn, vector up)."""
    eye = np.array(eye, np.float32)
    target = np.array(target, np.float32)
    up = np.array(up, np.float32)

    # 3 trục trực giao: f (forward), s (side), u (up)
    f = target - eye
    f = f / (np.linalg.norm(f) + 1e-9)
    s = np.cross(f, up); s = s / (np.linalg.norm(s) + 1e-9)
    u = np.cross(s, f)

    # Ma trận quay
    M = np.eye(4, dtype=np.float32)
    M[0,:3] = s; M[1,:3] = u; M[2,:3] = -f

    # Ma trận tịnh tiến
    T = np.eye(4, dtype=np.float32)
    T[:3,3] = -eye
    return (M @ T).astype(np.float32)

def orbit_to_eye(yaw, pitch, dist):
    """Chuyển tham số quỹ đạo (yaw, pitch, dist) thành tọa độ mắt."""
    ry, rp = math.radians(yaw), math.radians(pitch)
    return np.array([
        dist * math.cos(rp) * math.cos(ry),
        dist * math.cos(rp) * math.sin(ry),
        dist * math.sin(rp)
    ], np.float32)


# -------------------- Renderer chính --------------------
class OpenGLRenderer(Renderer3DBase):
    # Bảng màu RGBA
    C_BG   = (0.02, 0.02, 0.03, 1.0)   # nền
    C_GRID = (0.20, 0.20, 0.22, 1.0)   # lưới
    C_BS   = (0.95, 0.95, 0.20, 1.0)   # trạm gốc
    C_UAV  = (0.20, 0.80, 1.00, 1.0)   # UAV
    C_UE   = (0.20, 1.00, 0.20, 1.0)   # UE
    C_WIRE = (0.55, 0.70, 1.00, 1.0)   # dây liên kết
    C_AX_X = (1.00, 0.30, 0.30, 1.0)   # trục X
    C_AX_Y = (0.30, 1.00, 0.30, 1.0)   # trục Y
    C_AX_Z = (0.30, 0.30, 1.00, 1.0)   # trục Z
    C_SAT  = (1.00, 0.50, 0.00, 1.0)   # vệ tinh

    def __init__(self, width=1280, height=760):
        # Cửa sổ Pyglet với depth buffer + MSAA
        self.width, self.height = width, height
        cfg = pyglet.gl.Config(double_buffer=True, depth_size=24,
                               sample_buffers=1, samples=4)
        self.win = pyglet.window.Window(width, height,
            "UAV Wireless-ML (Phase 1)",
            config=cfg, resizable=True, vsync=True)

        # Camera mặc định: góc nhìn nghiêng nhẹ, khoảng cách vừa phải
        self.yaw, self.pitch, self.dist = 30.0, 20.0, 250.0
        self.target = np.array([0.0, 0.0, 0.0], np.float32)

        # HUD text (hiện thông tin ở góc trên trái)
        self._hud = pyglet.text.Label(
            "", font_size=12, x=12, y=self.height - 20,
            color=(255,255,255,255)
        )

        # Tùy chọn hiển thị
        self.show_grid = True
        self.show_wires = True
        self._dragging = False

        # --- FPS thủ công ---
        self._fps_t0 = time.perf_counter()
        self._fps_frames = 0
        self._fps_value = 0.0

        # -------------------- Event handlers --------------------
        @self.win.event
        def on_resize(w, h):
            """Cập nhật viewport và vị trí HUD khi đổi kích thước."""
            self.width, self.height = w, h
            self._hud.y = self.height - 20
            GL.glViewport(0, 0, w, h)

        @self.win.event
        def on_key_press(sym, mod):
            """Điều khiển bằng phím: ESC, R, mũi tên, zoom, toggle lớp vẽ."""
            if sym == key.ESCAPE:
                self.win.close()
            elif sym == key.R:  # reset camera
                self.yaw, self.pitch, self.dist = 30.0, 20.0, 250.0
            elif sym == key.LEFT:   self.yaw   -= 4.0
            elif sym == key.RIGHT:  self.yaw   += 4.0
            elif sym == key.UP:     self.pitch = max(-80.0, min(80.0, self.pitch + 4.0))
            elif sym == key.DOWN:   self.pitch = max(-80.0, min(80.0, self.pitch - 4.0))
            elif sym in (key.PLUS, key.NUM_ADD):       self.dist = max(20.0, self.dist * 0.87)
            elif sym in (key.MINUS, key.NUM_SUBTRACT): self.dist = min(1500.0, self.dist / 0.87)
            elif sym == key.G:   self.show_grid  = not self.show_grid
            elif sym == key.W:   self.show_wires = not self.show_wires
            elif sym == key.H:   # ẩn/hiện HUD
                self._hud.y = (-100 if self._hud.y > 0 else self.height - 20)
            elif sym == key.HOME and hasattr(self, "_world"):
                self._auto_frame(self._world)

        @self.win.event
        def on_mouse_press(x, y, button, mods):
            """Chuột trái để bắt đầu kéo xoay camera."""
            if button == mouse.LEFT:
                self._dragging = True
                self._mx, self._my = x, y

        @self.win.event
        def on_mouse_release(x, y, button, mods):
            """Thả chuột trái thì ngừng kéo xoay."""
            self._dragging = False

        @self.win.event
        def on_mouse_drag(x, y, dx, dy, buttons, mods):
            """Kéo chuột để xoay camera quanh target."""
            if not self._dragging: return
            self.yaw   += dx * 0.3
            self.pitch = max(-85.0, min(85.0, self.pitch + dy * 0.25))

        @self.win.event
        def on_mouse_scroll(x, y, sx, sy):
            """Cuộn để zoom in/out."""
            if sy > 0: self.dist = max(20.0, self.dist * 0.9)
            else:      self.dist = min(1500.0, self.dist / 0.9)

    # -------------------- Tiện ích nội bộ --------------------
    def _auto_frame(self, world):
        """Đặt camera sao cho bao trọn toàn bộ thực thể."""
        pts = [world.bs.pos] + [a.pos for a in world.uav] + \
              [u.pos for u in world.ue] + [s.pos for s in world.sat]
        P = np.array(pts, np.float32)
        center = P.mean(axis=0)
        radius = float(np.max(np.linalg.norm(P - center, axis=1))) * 1.2
        self.target = center
        self.dist = max(50.0, radius / math.tan(math.radians(55/2)))

    def loop(self, world, dt, steps):
        """Bắt đầu vòng lặp pyglet; gọi world.step định kỳ."""
        self._world = world
        self._auto_frame(world)

        def update(_dt):  # callback mỗi tick
            world.step(dt)

        pyglet.clock.schedule_interval(update, dt)

        @self.win.event
        def on_draw():
            """Hàm vẽ cho mỗi frame."""
            self._draw(world)

        pyglet.app.run()

    # ====== Pass 3D & 2D (sửa để HUD không bị méo) ======
    def _begin_3d(self):
        """Thiết lập GL để bắt đầu vẽ 3D."""
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glClearColor(*self.C_BG)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        # Ma trận chiếu + view
        proj = perspective(55.0, self.width/float(self.height), 0.1, 5000.0)
        eye = orbit_to_eye(self.yaw, self.pitch, self.dist)
        view = look_at(eye, self.target)

        # Fixed-function pipeline (đẩy stack rồi nạp riêng PROJECTION & MODELVIEW)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadMatrixf(proj.T)

        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glLoadMatrixf(view.T)

    def _end_3d(self):
        """Khôi phục stack ma trận sau pass 3D."""
        GL.glMatrixMode(GL.GL_MODELVIEW);  GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_PROJECTION); GL.glPopMatrix()

    def _begin_2d(self):
        """Thiết lập pass 2D (orthographic) để vẽ HUD/text."""
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glOrtho(0, self.width, 0, self.height, -1, 1)  # tọa độ pixel

        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glLoadIdentity()

    def _end_2d(self):
        """Khôi phục stack ma trận sau khi vẽ HUD."""
        GL.glMatrixMode(GL.GL_MODELVIEW);  GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_PROJECTION); GL.glPopMatrix()

    def _color(self, c): GL.glColor4f(*c)

    def _line(self, a, b):
        GL.glBegin(GL.GL_LINES)
        GL.glVertex3f(*a); GL.glVertex3f(*b)
        GL.glEnd()

    def _draw_grid_axes(self):
        """Vẽ lưới sàn (nếu bật) và trục Oxyz."""
        if self.show_grid:
            self._color(self.C_GRID)
            half, step = 120, 10
            for x in range(-half, half+1, step):
                self._line((x, -half, 0), (x, half, 0))
            for y in range(-half, half+1, step):
                self._line((-half, y, 0), (half, y, 0))
        # Trục màu
        self._color(self.C_AX_X); self._line((0,0,0),(80,0,0))
        self._color(self.C_AX_Y); self._line((0,0,0),(0,80,0))
        self._color(self.C_AX_Z); self._line((0,0,0),(0,0,80))

    def _draw_points(self, pts, color, size_px=6.0):
        """Vẽ tập hợp điểm với màu/kích thước cho trước."""
        self._color(color)
        GL.glPointSize(float(size_px))
        GL.glBegin(GL.GL_POINTS)
        for p in pts:
            GL.glVertex3f(float(p[0]), float(p[1]), float(p[2]))
        GL.glEnd()

    def _draw_uav_columns(self, uav_pts, base_height=60.0):
        """Vẽ cột dọc xuống đất dưới mỗi UAV."""
        self._color(self.C_UAV)
        GL.glLineWidth(3.0)
        for p in uav_pts:
            self._line((float(p[0]), float(p[1]), 0.0),
                       (float(p[0]), float(p[1]), float(base_height)))

    def _draw_wires(self, pairs):
        """Vẽ dây liên kết (UE→UAV gần nhất)."""
        if not self.show_wires: return
        self._color(self.C_WIRE)
        GL.glLineWidth(2.0)
        for a, b in pairs: self._line(a, b)

    def _update_hud(self, world):
        """Cập nhật text HUD: FPS + thống kê mô phỏng."""
        # FPS mỗi ~0.5s
        self._fps_frames += 1
        now = time.perf_counter(); dt = now - self._fps_t0
        if dt >= 0.5:
            self._fps_value = self._fps_frames / dt
            self._fps_frames = 0; self._fps_t0 = now
        fps = self._fps_value

        avg_lat = world.stats.sum_latency_s / max(1, world.stats.count_latency)
        self._hud.text = (
            f"FPS={fps:5.1f} | t={world.stats.time_s:5.1f}s step={world.stats.step} "
            f"enq={world.stats.enqueued} deq={world.stats.dequeued} drop={world.stats.dropped} "
            f"avg_lat={avg_lat:.3f}s max_lat={world.stats.max_latency_s:.3f}s "
            f"HW: {world.hw.cpu_cores}C/{world.hw.gpu_tflops_est:.1f}TF/{world.hw.mem_gb}GB"
        )

    def _draw(self, world):
        """Hàm vẽ chính mỗi frame."""
        # ---- PASS 3D ----
        self._begin_3d()
        self._draw_grid_axes()

        # Thu thập dữ liệu
        ue_pts  = [u.pos for u in world.ue]
        uav_pts = [a.pos for a in world.uav]
        bs_pts  = [world.bs.pos]
        sat_pts = [s.pos for s in world.sat]
        wires = [(u.pos, world._nearest_uav_pos(u.pos)) for u in world.ue]

        # Vẽ thực thể
        self._draw_wires(wires)
        self._draw_uav_columns(uav_pts, base_height=getattr(world.cfg.viz, "uav_column_height", 60.0))
        self._draw_points(bs_pts,  self.C_BS,  size_px=10.0)
        self._draw_points(uav_pts, self.C_UAV, size_px=8.0)
        self._draw_points(ue_pts,  self.C_UE,  size_px=6.0)
        if sat_pts: self._draw_points(sat_pts, self.C_SAT, size_px=10.0)
        self._end_3d()

        # ---- PASS 2D (HUD) ----
        # HUD
        self._begin_2d()
        self._update_hud(world)
        self._hud.draw()
        self._end_2d()
