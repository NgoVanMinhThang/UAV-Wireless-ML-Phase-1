# -*- coding: utf-8 -*-
# Điểm vào có giao diện chọn config.
# Cách dùng: python cli_ui.py  (hoặc python -m cli_ui)
from __future__ import annotations
import os, sys
from uwml.config import load_config
from uwml.world import World
from uwml.renderer_opengl import OpenGLRenderer

# thêm đường dẫn để import ui modules (cùng thư mục với file này)
sys.path.append(os.path.dirname(__file__))
from ui_launcher import pick_config_via_ui
from ui_sidebar import Sidebar

def main():
    # 1) Chọn config qua UI
    cfg_path = pick_config_via_ui(configs_dir="configs")
    if not cfg_path:
        print("Không chọn config nào. Thoát.")
        return

    # 2) Nạp và chạy mô phỏng với sidebar
    cfg = load_config(cfg_path)
    w = World(cfg); w.spawn()

    ren = OpenGLRenderer()
    ren.show_wires = True
    ren._world = w
    ren._auto_frame(w)

    # Trạng thái pause
    ren._paused = False

    # Tạo sidebar
    sidebar = Sidebar(
        win=ren.win,
        world_ref=lambda: getattr(ren, "_world", None),
        toggle_wires_fn=lambda: setattr(ren, "show_wires", not ren.show_wires),
        pause_resume_fn=lambda: setattr(ren, "_paused", not getattr(ren, "_paused", False)),
        back_fn=lambda: ren.win.close()
    )
    ren._sidebar = sidebar

    # Wrap lại update để tôn trọng pause
    def update(_dt):
        if not getattr(ren, "_paused", False):
            w.step(cfg.system.dt)
    import pyglet
    pyglet.clock.schedule_interval(update, cfg.system.dt)

    @ren.win.event
    def on_draw():
        ren._draw(w)
        # vẽ overlay 2D
        ren._begin_2d()
        ren._update_hud(w)  # vẫn dùng HUD cũ nếu muốn
        sidebar.set_paused(getattr(ren, "_paused", False))
        sidebar.draw()
        ren._end_2d()

    @ren.win.event
    def on_mouse_press(x, y, button, mods):
        # thử cho sidebar xử lý trước
        if sidebar.on_mouse_press(x, y, button, mods):
            return
        # còn lại thì dùng logic renderer cũ (xoay camera...)
        # không cần gọi gì thêm vì renderer đã có handler trong file gốc

    import pyglet
    pyglet.app.run()

if __name__ == "__main__":
    main()
