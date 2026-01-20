import tkinter as tk
from tkinter import messagebox
import threading
import time
import sys
import ctypes
from pynput import keyboard
from record import ActionRecorder
from play import ActionPlayer

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class MimicLiteGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mimic Lite Pro - 毫秒統一版")
        self.root.geometry("380x600")
        self.root.attributes("-topmost", True)

        self.recorder = ActionRecorder()
        self.player = ActionPlayer()
        self.is_running = False
        self.is_recording = False

        self._setup_ui()

        self.hk = keyboard.GlobalHotKeys({
            '<f8>': self.start_record,
            '<f9>': self.start_play,
            '<esc>': self.stop_all
        })
        self.hk.daemon = True
        self.hk.start()

    def _setup_ui(self):
        tk.Label(self.root, text="模擬硬體級按鍵 (單位：毫秒)", font=("Arial", 12, "bold")).pack(pady=10)

        status_color = "green" if is_admin() else "red"
        admin_text = "● 管理員權限已取得" if is_admin() else "○ 請以管理員身份執行"
        tk.Label(self.root, text=admin_text, fg=status_color).pack()

        self.lb_status = tk.Label(self.root, text="狀態: 閒置", font=("Arial", 12), fg="blue")
        self.lb_status.pack(pady=15)

        cfg = tk.LabelFrame(self.root, text=" 執行參數設定 ", padx=10, pady=10)
        cfg.pack(padx=20, fill="x")

        tk.Label(cfg, text="循環次數 (0=無限):").grid(row=0, column=0, sticky="w")
        self.en_loop = tk.Entry(cfg, width=10)
        self.en_loop.insert(0, "1")
        self.en_loop.grid(row=0, column=1, pady=2)

        tk.Label(cfg, text="總執行時長 (HH:MM:SS):").grid(row=1, column=0, sticky="w")
        self.en_time = tk.Entry(cfg, width=10)
        self.en_time.insert(0, "00:00:00")
        self.en_time.grid(row=1, column=1, pady=2)

        # 這裡統一為毫秒 (ms) [cite: 2, 3]
        tk.Label(cfg, text="循環間隔 (毫秒):").grid(row=2, column=0, sticky="w")
        self.en_int = tk.Entry(cfg, width=10)
        self.en_int.insert(0, "1000") 
        self.en_int.grid(row=2, column=1, pady=2)

        self.var_rand = tk.BooleanVar(value=True)
        tk.Checkbutton(cfg, text="開啟高斯隨機化 (±20%)", variable=self.var_rand).grid(row=3, columnspan=2)

        btn_style = {"font": ("微軟正黑體", 10, "bold"), "height": 2, "width": 25}
        tk.Button(self.root, text="● 開始錄製 (F8)", bg="#e67e22", fg="white", **btn_style,
                  command=self.start_record).pack(pady=5)
        tk.Button(self.root, text="▶ 開始回放 (F9)", bg="#27ae60", fg="white", **btn_style,
                  command=self.start_play).pack(pady=5)
        tk.Button(self.root, text="■ 停止所有 (ESC)", bg="#c0392b", fg="white", **btn_style,
                  command=self.stop_all).pack(pady=5)

    def start_record(self):
        if self.is_running or self.is_recording: return
        self.is_recording = True
        self.lb_status.config(text="狀態: 錄製中...", fg="red")
        self.recorder.start()

    def start_play(self):
        if self.is_recording or self.is_running: return
        try:
            int(self.en_loop.get())
            float(self.en_int.get()) # 檢查間隔是否為有效數值 
        except ValueError:
            messagebox.showerror("格式錯誤", "請檢查輸入欄位是否為正確數字")
            return
        self.is_running = True
        threading.Thread(target=self._orchestrate, daemon=True).start()

    def stop_all(self):
        if self.is_recording: self.recorder.stop(); self.is_recording = False
        if self.is_running: self.is_running = False; self.player.stop()
        self.lb_status.config(text="狀態: 已停止", fg="blue")

    def _orchestrate(self):
        loops = int(self.en_loop.get())
        dur_sec = self._parse_hms(self.en_time.get())
        interval_ms = float(self.en_int.get()) # 取得毫秒單位 
        rand = self.var_rand.get()

        start_time = time.time()
        cnt = 0
        while self.is_running:
            if dur_sec > 0 and (time.time() - start_time) >= dur_sec: break
            elif loops > 0 and cnt >= loops: break

            self.lb_status.config(text=f"狀態: 第 {cnt + 1} 次執行", fg="green")
            self.player.play_once(use_random=rand)
            cnt += 1

            if not self.is_running: break
            self.lb_status.config(text=f"狀態: 休息中...", fg="orange")
            # 直接使用毫秒傳遞給高精度 sleep 
            self.player._precise_sleep_ms(interval_ms)

        self.is_running = False
        self.lb_status.config(text="狀態: 閒置", fg="blue")

    def _parse_hms(self, s):
        try:
            h, m, sec = map(int, s.split(':'))
            return h * 3600 + m * 60 + sec
        except: return 0

if __name__ == "__main__":
    root = tk.Tk()
    app = MimicLiteGUI(root)
    root.mainloop()
