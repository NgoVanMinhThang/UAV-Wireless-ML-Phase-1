# -*- coding: utf-8 -*-
# Thanh tiện ích đơn giản vẽ bằng OpenGL + pyglet (2D overlay).
# Mục tiêu: hiện thông số, và vài nút (Back, Toggle Wires, Pause/Resume).
# Dùng kiểu mộc mạc, đủ xài cho demo.

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Tuple, List
import pyglet
from OpenGL import GL

@dataclass
class Button:
    label: str
    rect: Tuple[int,int,int,int]  # (x, y, w, h) tính theo pixel từ góc trái-dưới
    on_click: Callable[[], None]

    def hit(self, mx, my):
        x, y, w, h = self.rect
        return (x <= mx <= x + w) and (y <= my <= y + h)

class Sidebar:
    """Vẽ panel bên phải. Không dùng widget framework để giữ nhẹ.
    Bạn có thể thay thế bằng imgui/qt nếu muốn về sau.
    """
    PAD = 12
    WIDTH = 280  # bề rộng panel bên phải (px)

    def __init__(self, win, world_ref, toggle_wires_fn, pause_resume_fn, back_fn):
        self.win = win
        self.world_ref = world_ref  # hàm/lambda trả về world hiện tại
        self.toggle_wires = toggle_wires_fn
        self.pause_resume = pause_resume_fn
        self.back = back_fn

        self.font_title = pyglet.text.Label(
            "Tiện ích", font_size=14, x=0, y=0, color=(255,255,255,255)
        )
        self.font_text = pyglet.text.Label(
            "", font_size=12, x=0, y=0, color=(230,230,230,255)
        )

        # Nút sẽ được đặt lại vị trí mỗi frame theo kích cỡ cửa sổ
        self.buttons: List[Button] = []
        self._paused = False

    def set_paused(self, val: bool):
        self._paused = bool(val)

    def layout_buttons(self):
        # Tính toạ độ nút từ dưới lên để tránh đè lên text
        w = self.WIDTH - 2*self.PAD
        x = self.win.width - self.WIDTH + self.PAD
        y = 16  # margin dưới
        h = 32
        gap = 10

        self.buttons = [
            Button("◀ Back", (x, y, w, h), self.back),
            Button("🔌 Toggle wires", (x, y + (h+gap), w, h), self.toggle_wires),
            Button(("⏸ Pause" if not self._paused else "▶ Resume"),
                   (x, y + 2*(h+gap), w, h), self.pause_resume),
        ]

    def draw_panel_bg(self):
        # Vẽ nền mờ của sidebar
        GL.glColor4f(0.08, 0.1, 0.15, 0.85)
        x0 = self.win.width - self.WIDTH
        GL.glBegin(GL.GL_QUADS)
        GL.glVertex2f(x0, 0);             GL.glVertex2f(self.win.width, 0)
        GL.glVertex2f(self.win.width, self.win.height); GL.glVertex2f(x0, self.win.height)
        GL.glEnd()

    def draw_button(self, btn: Button):
        x,y,w,h = btn.rect
        # nền nút
        GL.glColor4f(0.2,0.25,0.35,0.9)
        GL.glBegin(GL.GL_QUADS)
        GL.glVertex2f(x, y); GL.glVertex2f(x+w, y)
        GL.glVertex2f(x+w, y+h); GL.glVertex2f(x, y+h)
        GL.glEnd()
        # viền
        GL.glColor4f(0.5,0.7,1.0,0.9)
        GL.glBegin(GL.GL_LINE_LOOP)
        GL.glVertex2f(x, y); GL.glVertex2f(x+w, y); GL.glVertex2f(x+w, y+h); GL.glVertex2f(x, y+h)
        GL.glEnd()
        # nhãn
        self.font_text.text = btn.label
        self.font_text.x = x + 10; self.font_text.y = y + h/2 + 2
        self.font_text.draw()

    def draw_stats(self):
        w = self.world_ref()
        if w is None: return
        lines = [
            "THỐNG KÊ",
            f"Bước: {w.stats.step}  |  Thời gian: {w.stats.time_s:.1f}s",
            f"Enq: {w.stats.enqueued}  Deq: {w.stats.dequeued}  Drop: {w.stats.dropped}",
            f"Avg latency: {(w.stats.sum_latency_s / max(1, w.stats.count_latency or 1)):.3f}s",
            f"Max latency: {w.stats.max_latency_s:.3f}s",
            f"#UAV: {len(w.uav)}  #UE: {len(w.ue)}  #SAT: {len(w.sat)}",
        ]
        x = self.win.width - self.WIDTH + self.PAD
        y = self.win.height - self.PAD - 18
        # title
        self.font_title.text = "Tiện ích"
        self.font_title.x = x
        self.font_title.y = y
        self.font_title.draw()
        # text block
        y -= 24
        for line in lines:
            self.font_text.text = line
            self.font_text.x = x
            self.font_text.y = y
            self.font_text.draw()
            y -= 18

    def draw(self):
        self.layout_buttons()
        self.draw_panel_bg()
        self.draw_stats()
        for b in self.buttons:
            self.draw_button(b)

    def on_mouse_press(self, x, y, button, mods):
        # hit test nút
        for b in self.buttons:
            if b.hit(x, y):
                b.on_click()
                return True
        return False
