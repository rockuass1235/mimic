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

    def calculate_gaussian_delay(self, ms):
        """計算帶有上下限保護的高斯隨機延遲"""
        if ms <= 0: return 0
        mu = ms
        sigma = ms * 0.12  # 提高標準差至 12% 增加隨機性
        new_ms = random.gauss(mu, sigma)
        # 限制在原始時間的 70% ~ 140% 之間，避免極端值
        return max(ms * 0.7, min(new_ms, ms * 1.4))

    def _bezier_move(self, target_pos, use_random):
        """強化版貝茲曲線移動，加入隨機擾動 jitter"""
        start_pos = self.ms_ctrl.position
        if not use_random:
            self.ms_ctrl.position = target_pos
            return

        x1, y1 = start_pos
        x2, y2 = target_pos
        dist = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
        
        if dist < 10:
            self.ms_ctrl.position = target_pos
            return

        # 加入控制點的隨機偏移量，使每次移動路徑略有不同
        cp1 = (x1 + (x2 - x1) * 0.3, y1 + (y2 - y1) * 0.3 + random.uniform(-dist * 0.15, dist * 0.15))
        cp2 = (x1 + (x2 - x1) * 0.7, y1 + (y2 - y1) * 0.7 + random.uniform(-dist * 0.15, dist * 0.15))
        
        steps = random.randint(12, 20) # 隨機化移動步數
        t = np.linspace(0, 1, steps)
        
        for i in t:
            if not self.playing: break
            p = (1 - i) ** 3 * np.array([x1, y1]) + 3 * (1 - i) ** 2 * i * np.array(cp1) + 3 * (
                        1 - i) * i ** 2 * np.array(cp2) + i ** 3 * np.array([x2, y2])
            
            # 加入微小的像素擾動 (Jitter)
            jitter_x = random.uniform(-1, 1) if use_random else 0
            jitter_y = random.uniform(-1, 1) if use_random else 0
            self.ms_ctrl.position = (int(p[0] + jitter_x), int(p[1] + jitter_y))
            time.sleep(random.uniform(0.001, 0.003))

    def play_once(self, use_random=True):
        """回放單次腳本，已修正方法名稱"""
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
                    final_delay = self.calculate_gaussian_delay(original_ms) if use_random else original_ms
                    if final_delay > 0:
                        time.sleep(final_delay / 1000.0)

                elif cmd == "KEY_DOWN":
                    key = self.key_map.get(params[0], params[0])
                    # 按下按鍵前加入 1-5ms 的極小隨機偏移
                    if use_random: time.sleep(random.uniform(0.001, 0.005))
                    self.kb_ctrl.press(key)
                    
                elif cmd == "KEY_UP":
                    key = self.key_map.get(params[0], params[0])
                    self.kb_ctrl.release(key)
                    
                elif cmd in ["MOUSE_DOWN", "MOUSE_UP"]:
                    btn = mouse.Button.left if params[0] == "left" else mouse.Button.right
                    # 滑鼠點擊前先移動，並加入隨機化路徑
                    self._bezier_move((int(params[1]), int(params[2])), use_random)
                    if cmd == "MOUSE_DOWN":
                        self.ms_ctrl.press(btn)
                    else:
                        self.ms_ctrl.release(btn)
                        
        except Exception as e:
            print(f"Playback Error: {e}")
        finally:
            self.playing = False

    def stop(self):
        self.playing = False
