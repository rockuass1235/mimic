import time
import random
import numpy as np
from pynput import mouse, keyboard


class ActionPlayer:
    def __init__(self, filename="script.txt"):
        self.filename = filename
        self.playing = False
        self.kb_ctrl = keyboard.Controller()
        self.ms_ctrl = mouse.Controller()

        self.key_map = {
            "space": keyboard.Key.space, "enter": keyboard.Key.enter,
            "esc": keyboard.Key.esc, "shift": keyboard.Key.shift,
            "ctrl": keyboard.Key.ctrl, "alt": keyboard.Key.alt,
            "tab": keyboard.Key.tab, "backspace": keyboard.Key.backspace,
            "up": keyboard.Key.up, "down": keyboard.Key.down,
            "left": keyboard.Key.left, "right": keyboard.Key.right,
            "f1": keyboard.Key.f1, "f2": keyboard.Key.f2, "f3": keyboard.Key.f3,
            "f4": keyboard.Key.f4, "f5": keyboard.Key.f5, "f6": keyboard.Key.f6,
            "f7": keyboard.Key.f7, "f8": keyboard.Key.f8, "f9": keyboard.Key.f9,
        }

    # --- 核心計算函數：您可以決定何時調用它 ---
    def calculate_gaussian_delay(self, ms):
        """僅進行高斯常態分佈計算，返回新的毫秒數"""
        if ms <= 0: return 0
        mu = ms
        sigma = ms * 0.1  # 標準差為 10%
        new_ms = random.gauss(mu, sigma)
        # 限制範圍，確保不會出現負數或過於離譜的延遲（正負 30% 內）
        return max(ms * 0.7, min(new_ms, ms * 1.3))

    def _bezier_move(self, target_pos, use_random):
        """滑鼠移動邏輯"""
        start_pos = self.ms_ctrl.position
        if not use_random:
            self.ms_ctrl.position = target_pos
            return

        # 貝茲曲線移動 (僅在開啟隨機化時)
        x1, y1 = start_pos
        x2, y2 = target_pos
        dist = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
        if dist < 5:
            self.ms_ctrl.position = target_pos
            return

        cp1 = (x1 + (x2 - x1) * 0.3, y1 + (y2 - y1) * 0.3 + random.uniform(-dist * 0.1, dist * 0.1))
        cp2 = (x1 + (x2 - x1) * 0.7, y1 + (y2 - y1) * 0.7 + random.uniform(-dist * 0.1, dist * 0.1))
        steps = random.randint(10, 15)
        t = np.linspace(0, 1, steps)
        for i in t:
            if not self.playing: break
            p = (1 - i) ** 3 * np.array([x1, y1]) + 3 * (1 - i) ** 2 * i * np.array(cp1) + 3 * (
                        1 - i) * i ** 2 * np.array(cp2) + i ** 3 * np.array([x2, y2])
            self.ms_ctrl.position = (int(p[0]), int(p[1]))
            time.sleep(0.001)

    def play(self, use_random=True):
        """播放主循環"""
        self.playing = True
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in lines:
                if not self.playing: break
                parts = line.strip().split(" ", 1)
                if not parts: continue
                cmd = parts[0]
                params = parts[1].split("|") if len(parts) > 1 else []

                if cmd == "WAIT":
                    original_ms = int(params[0])
                    # --- 決定點：使用隨機毫秒還是原始毫秒 ---
                    if use_random:
                        final_delay = self.calculate_gaussian_delay(original_ms)
                    else:
                        final_delay = original_ms

                    if final_delay > 0:
                        time.sleep(final_delay / 1000.0)

                elif cmd == "KEY_DOWN":
                    self.kb_ctrl.press(self.key_map.get(params[0], params[0]))
                elif cmd == "KEY_UP":
                    self.kb_ctrl.release(self.key_map.get(params[0], params[0]))
                elif cmd in ["MOUSE_DOWN", "MOUSE_UP"]:
                    btn = mouse.Button.left if params[0] == "left" else mouse.Button.right
                    self._bezier_move((int(params[1]), int(params[2])), use_random)
                    if cmd == "MOUSE_DOWN":
                        self.ms_ctrl.press(btn)
                    else:
                        self.ms_ctrl.release(btn)
        except Exception as e:
            print(f"Play Error: {e}")
        finally:
            self.playing = False

    def stop(self):
        self.playing = False