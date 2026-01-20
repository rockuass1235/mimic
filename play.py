import time
import random
import ctypes
from pynput import mouse, keyboard

winmm = ctypes.WinDLL('winmm')

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

    def _precise_sleep_ms(self, ms):
        """
        高精度睡眠函數：統一接收毫秒 (ms) 
        """
        if ms <= 0: return
        target_sec = time.perf_counter() + (ms / 1000.0)
        while time.perf_counter() < target_sec:
            rem = target_sec - time.perf_counter()
            if rem > 0.002: # 剩餘時間大於 2ms 才釋放 CPU
                time.sleep(0.001)
            else:
                pass # 忙碌等待以確保毫秒級精確 

    def calculate_gaussian_delay(self, ms):
        """計算高斯隨機延遲 (單位：毫秒) """
        if ms <= 0: return 0
        mu = ms
        sigma = ms * 0.1
        new_ms = random.gauss(mu, sigma)
        return max(ms * 0.8, min(new_ms, ms * 1.2))

    def play_once(self, use_random=True):
        self.playing = True
        try:
            winmm.timeBeginPeriod(1) # 提升系統計時精度 
            with open(self.filename, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in lines:
                if not self.playing: break
                parts = line.strip().split(" ", 1)
                if not parts: continue
                cmd = parts[0]
                params = parts[1].split("|") if len(parts) > 1 else []

                if cmd == "WAIT":
                    # 直接從腳本中讀取毫秒 [cite: 2, 4]
                    ms = int(params[0])
                    delay = self.calculate_gaussian_delay(ms) if use_random else ms
                    self._precise_sleep_ms(delay)

                elif cmd == "KEY_DOWN":
                    key = self.key_map.get(params[0], params[0])
                    self.kb_ctrl.press(key)
                elif cmd == "KEY_UP":
                    key = self.key_map.get(params[0], params[0])
                    self.kb_ctrl.release(key)
                elif cmd in ["MOUSE_DOWN", "MOUSE_UP"]:
                    btn = mouse.Button.left if params[0] == "left" else mouse.Button.right
                    if cmd == "MOUSE_DOWN": self.ms_ctrl.press(btn)
                    else: self.ms_ctrl.release(btn)
        except Exception as e:
            print(f"Playback Error: {e}")
        finally:
            winmm.timeEndPeriod(1)
            self.playing = False

    def stop(self):
        self.playing = False
