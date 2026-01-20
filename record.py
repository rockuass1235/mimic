import time
from pynput import mouse, keyboard

class ActionRecorder:
    def __init__(self, filename="script.txt"):
        self.filename = filename
        self.recording = False
        self.last_event_time = 0  # 用於計算兩個事件之間的差值
        self.script_file = None

    def _get_delay(self):
        """
        計算自「錄製開始」或「上一個事件」以來經過的時間。
        這就是您要求的：每次按下按鍵就記錄經過多少 time(ms)。
        """
        now = time.time()
        delay = now - self.last_event_time
        self.last_event_time = now
        return round(delay*1000)

    def _write_command(self, cmd_type, *args):
        """
        統一寫入指令的格式化函式。
        會先計算延遲，再寫入動作。
        """
        if not self.recording or not self.script_file:
            return

        # 1. 取得與上一個事件的時間差 (相對延遲)
        delay = self._get_delay()

        # 2. 寫入 WAIT 指令 (如果是第一個按鍵，這代表從「錄製開始」到「按下」的時間)
        if delay > 0:
            self.script_file.write(f"WAIT {delay}\n")

        # 3. 寫入動作指令
        data = "|".join(map(str, args))
        self.script_file.write(f"{cmd_type} {data}\n")
        self.script_file.flush()

    # --- 鍵盤事件監聽 ---
    def _on_press(self, key):
        if key == keyboard.Key.f8: return  # 假設 F8 是 GUI 的停止鍵，不錄入腳本
        self._write_command("KEY_DOWN", self._parse_key(key))

    def _on_release(self, key):
        if key == keyboard.Key.f8: return
        self._write_command("KEY_UP", self._parse_key(key))

    # --- 滑鼠事件監聽 ---
    def _on_click(self, x, y, button, pressed):
        action = "MOUSE_DOWN" if pressed else "MOUSE_UP"
        btn_name = str(button).replace("Button.", "")
        self._write_command(action, btn_name, int(x), int(y))

    def _on_scroll(self, x, y, dx, dy):
        self._write_command("MOUSE_WHEEL", dy, int(x), int(y))

    def _parse_key(self, key):
        try:
            return key.char
        except AttributeError:
            return str(key).replace("Key.", "")

    # --- 生命週期控制 ---
    def start(self):
        """
        開始錄製，初始化 event_time=0 的基準點。
        """
        self.script_file = open(self.filename, "w", encoding="utf-8")
        self.recording = True

        # 設定「事件時間基準點」為現在 (Time 0)
        self.last_event_time = time.time()

        # 啟動監聽執行緒
        self.kb_ln = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self.ms_ln = mouse.Listener(on_click=self._on_click, on_scroll=self._on_scroll)

        self.kb_ln.start()
        self.ms_ln.start()
        print(f"[Record] 錄製已開始（儲存至 {self.filename}）")

    def stop(self):
        self.recording = False
        if hasattr(self, 'kb_ln'): self.kb_ln.stop()
        if hasattr(self, 'ms_ln'): self.ms_ln.stop()
        if self.script_file:
            self.script_file.close()
            self.script_file = None
        print("[Record] 錄製已停止")


# 測試用
if __name__ == "__main__":
    rec = ActionRecorder()
    rec.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        rec.stop()