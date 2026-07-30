#from interception.stroke import key_stroke
import time

# 方向鍵專屬代碼
SC_DECIMAL_ARROW = {
    "LEFT": 75, "RIGHT": 77, "DOWN": 80, "UP": 72,
}

# 一般按鍵代碼
SC_DECIMAL = {
    "ALT": 56, "SPACE": 57, "CTRL": 29, "SHIFT": 42,
    "A": 30, "S": 31, "D": 32, "F": 33,
    "Q": 16, "W": 17, "E": 18, "R": 19,
    "Z": 44, "X": 45, "C": 46, "V": 47,
    "1": 2, "2": 3, "3": 4, "4": 5, "5": 6, "6": 7,
    "INSERT": 82, "HOME": 71, "PAGEUP": 73,
    "DELETE": 83, "END": 79, "PAGEDOWN": 81
}

#class Player:
    def __init__(self, context, device, game):
        self.game = game
        self.context = context
        self.device = device
        
        # 這些變數會在 main.py 啟動時由使用者設定覆寫
        self.jump_key = "ALT"
        self.attack_key = "CTRL"
        self.loot_key = "Z"

    def release_all(self):
        """釋放所有按鍵，防止卡鍵暴走"""
        for key in SC_DECIMAL_ARROW:
            self.context.send(self.device, key_stroke(SC_DECIMAL_ARROW[key], 3, 0))
        for key in SC_DECIMAL:
            self.context.send(self.device, key_stroke(SC_DECIMAL[key], 1, 0))

    def press(self, key):
        """模擬人類按下並放開按鍵 (約 50ms 延遲)"""
        if key in SC_DECIMAL_ARROW:
            self.context.send(self.device, key_stroke(SC_DECIMAL_ARROW[key], 2, 0))
            time.sleep(0.05)
            self.context.send(self.device, key_stroke(SC_DECIMAL_ARROW[key], 3, 0))
        else:
            self.context.send(self.device, key_stroke(SC_DECIMAL[key], 0, 0))
            time.sleep(0.05)
            self.context.send(self.device, key_stroke(SC_DECIMAL[key], 1, 0))

    def release(self, key):
        """單純放開按鍵"""
        if key in SC_DECIMAL_ARROW:
            self.context.send(self.device, key_stroke(SC_DECIMAL_ARROW[key], 3, 0))
        else:
            self.context.send(self.device, key_stroke(SC_DECIMAL[key], 1, 0))

    def hold(self, key):
        """單純按下按鍵不放"""
        if key in SC_DECIMAL_ARROW:
            self.context.send(self.device, key_stroke(SC_DECIMAL_ARROW[key], 2, 0))
        else:
            self.context.send(self.device, key_stroke(SC_DECIMAL[key], 0, 0))
