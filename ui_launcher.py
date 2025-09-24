# -*- coding: utf-8 -*-
# Màn hình chọn config/ tạo config mới (cực nhẹ, vẽ thủ công).
# Ý tưởng: liệt kê các file .yaml trong thư mục configs/, cho chọn bằng chuột/phím;
# hoặc tạo mới với vài tham số cơ bản (n_uav, n_ue, steps), đặt tên rồi lưu YAML.

from __future__ import annotations
import os, glob, yaml
import pyglet
from pyglet.window import key, mouse

class Launcher:
    def __init__(self, configs_dir="configs"):
        self.configs_dir = configs_dir
        os.makedirs(self.configs_dir, exist_ok=True)
        self.mode = "select"   # "select" hoặc "new"
        self.selected_idx = 0
        self.items = self._scan()

        # Dữ liệu tạm khi tạo mới
        self.new_name = "my_config"
        self.new_n_uav = 3
        self.new_n_ue = 100
        self.new_steps = 200

        # UI
        self.win = pyglet.window.Window(900, 560, caption="UAV Simulator Launcher")
        self.font = pyglet.text.Label("", font_size=13, color=(230,230,230,255))

        @self.win.event
        def on_draw():
            self.win.clear()
            pyglet.gl.glClearColor(0.06,0.07,0.09,1.0)
            if self.mode == "select":
                self._draw_select()
            else:
                self._draw_new()

        @self.win.event
        def on_key_press(sym, mod):
            if self.mode == "select":
                if sym == key.UP: self.selected_idx = max(0, self.selected_idx-1)
                elif sym == key.DOWN: self.selected_idx = min(len(self.items), self.selected_idx+1)
                elif sym == key.ENTER:
                    if self.selected_idx == 0:
                        self.mode = "new"
                    else:
                        self._launch(self.items[self.selected_idx-1])
                elif sym == key.ESCAPE:
                    self.win.close()
            else:  # new
                if sym == key.ESCAPE:
                    self.mode = "select"
                elif sym == key.TAB:
                    pass  # bỏ qua focus phức tạp, dùng phím để tăng/giảm
                elif sym == key.ENTER:
                    path = self._save_new()
                    self._launch(os.path.basename(path))
                elif sym == key.LEFT:
                    self.new_steps = max(10, self.new_steps-10)
                elif sym == key.RIGHT:
                    self.new_steps += 10
                elif sym == key.UP:
                    self.new_n_ue += 5
                elif sym == key.DOWN:
                    self.new_n_ue = max(10, self.new_n_ue-5)

        @self.win.event
        def on_text(text):
            # nhập tên file khi ở mode "new": gõ chữ, Backspace thì xoá
            if self.mode == "new":
                if text and text.isprintable() and text not in "\r\n\t":
                    self.new_name += text

        @self.win.event
        def on_text_motion(motion):
            if self.mode == "new" and motion == pyglet.window.key.MOTION_BACKSPACE:
                self.new_name = self.new_name[:-1]

    def _scan(self):
        items = sorted([os.path.basename(p) for p in glob.glob(os.path.join(self.configs_dir, "*.yaml"))])
        # ô đầu tiên là "Tạo mới..."
        return items

    def _draw_text(self, s, x, y):
        self.font.text = s; self.font.x = x; self.font.y = y; self.font.draw()

    def _draw_select(self):
        self._draw_text("CHỌN CONFIG:", 40, self.win.height-40)
        # dòng 0: tạo mới
        entries = ["[+] Tạo config mới"] + self.items
        for i, name in enumerate(entries):
            y = self.win.height-80 - i*26
            prefix = "→ " if i == self.selected_idx else "  "
            self._draw_text(prefix + name, 60, y)

        self._draw_text("Mẹo: dùng ↑/↓ để chọn, Enter để mở. ESC để thoát.", 40, 40)

    def _draw_new(self):
        self._draw_text("TẠO CONFIG MỚI", 40, self.win.height-40)
        self._draw_text(f"Tên file (không có đuôi .yaml): {self.new_name}", 60, self.win.height-90)
        self._draw_text(f"Số UAV: 3 (cố định bản đơn giản)", 60, self.win.height-120)
        self._draw_text(f"Số UE: {self.new_n_ue}   (↑ tăng 5, ↓ giảm 5)", 60, self.win.height-150)
        self._draw_text(f"Số bước mô phỏng (steps): {self.new_steps}   (← giảm 10, → tăng 10)", 60, self.win.height-180)
        self._draw_text("Enter để lưu & chạy | ESC để quay lại | Backspace để xoá ký tự tên file", 60, 60)

    def _save_new(self):
        # tạo YAML đơn giản dựa trên default
        data = {
            "system": {"dt": 0.1, "steps": int(self.new_steps)},
            "time": {"seed": 42},
            "hardware": {"cpu_cores": 8, "gpu_tflops_est": 9.0, "mem_gb": 16},
            "world": {"bounds": [-120,120,-120,120,0,120], "n_uav": 3, "n_ue": int(self.new_n_ue), "satellites":[[0,0,300]]},
            "uav": {"count": 3, "altitude_m":60.0, "speed_mps":8.0, "waypoints":[[-80,-80,60],[80,-80,60],[80,80,60],[-80,80,60]]},
            "ue": {"speed_mps":1.5, "wander_radius":20.0},
            "channel": {"tx_power_dbm":18.0, "pathloss_exp":2.1, "ref_pathloss_db":30.0, "carrier_hz":2.4e9, "bandwidth_hz":5.0e6, "noise_figure_db":5.0},
            "packet": {"size_bytes":1200, "gen_prob_per_step":0.2, "priority":1, "max_log":1000},
            "viz": {"point_px":{"ue":6.0,"uav":10.0,"bs":10.0,"sat":10.0}, "wire_px":2.0, "uav_column_height":60.0}
        }
        fname = f"{self.new_name}.yaml"
        path = os.path.join(self.configs_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
        return path

    def _launch(self, config_name: str):
        # Đơn giản: ghi ra file tạm rồi kết thúc launcher bằng cách set caption -> caller đọc
        # Ở phiên bản gọn này, mình dùng caption để trả về path cho process gọi (một mẹo nhỏ).
        self.win.set_caption(f"LAUNCH::{os.path.join(self.configs_dir, config_name)}")
        self.win.close()

def pick_config_via_ui(configs_dir="configs"):
    app = Launcher(configs_dir=configs_dir)
    pyglet.app.run()
    cap = app.win.caption
    if cap.startswith("LAUNCH::"):
        return cap.split("LAUNCH::",1)[1]
    return None
