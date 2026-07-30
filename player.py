from interception.stroke import key_stroke
import time

# Scancodes for arrow and alphanumeric/modifier keys should be separated. They have different key-states.
SC_DECIMAL_ARROW = {
    "LEFT": 75, "RIGHT": 77, "DOWN": 80, "UP": 72,
}

# 【重點修改】你可以在這裡擴充你要使用的按鍵，例如補上 Z, X, C, Insert 等等
SC_DECIMAL = {
    "ALT": 56, "SPACE": 57, "CTRL": 29, "SHIFT": 42,
    "A": 30, "S": 31, "D": 32, "F": 33,
    "Q": 16, "W": 17, "E": 18, "R": 19,
    "1": 2, "2": 3, "3": 4, "4": 5
}

# Change these to your own settings.
JUMP_KEY = "ALT"
# 經典版通常沒有上跳技能，所以把原本的 ROPE_LIFT 移除了


class Player:
    def __init__(self, context, device, game):
        self.game = game
        # interception
        self.context = context
        self.device = device

    def release_all(self):
        for key in SC_DECIMAL_ARROW:
            self.context.send(self.device, key_stroke(SC_DECIMAL_ARROW[key], 3, 0))
        for key in SC_DECIMAL:
            self.context.send(self.device, key_stroke(SC_DECIMAL[key], 1, 0))

    def press(self, key):
        """
        Mimics a human key-press.
        Delay between down-stroke and up-stroke was tested to be around 50 ms.
        """
        if key in SC_DECIMAL_ARROW:
            self.context.send(self.device, key_stroke(SC_DECIMAL_ARROW[key], 2, 0))
            time.sleep(0.05)
            self.context.send(self.device, key_stroke(SC_DECIMAL_ARROW[key], 3, 0))
        else:
            self.context.send(self.device, key_stroke(SC_DECIMAL[key], 0, 0))
            time.sleep(0.05)
            self.context.send(self.device, key_stroke(SC_DECIMAL[key], 1, 0))

    def release(self, key):
        if key in SC_DECIMAL_ARROW:
            self.context.send(self.device, key_stroke(SC_DECIMAL_ARROW[key], 3, 0))
        else:
            self.context.send(self.device, key_stroke(SC_DECIMAL[key], 1, 0))

    def hold(self, key):
        if key in SC_DECIMAL_ARROW:
            self.context.send(self.device, key_stroke(SC_DECIMAL_ARROW[key], 2, 0))
        else:
            self.context.send(self.device, key_stroke(SC_DECIMAL[key], 0, 0))

    def go_to(self, target):
        """
        【改寫版】只針對 X 軸（左右）移動，忽略 Y 軸（高度）。
        適合經典版無上跳技能的職業在平地來回巡邏打怪。
        """
        print(f"🏃 開始水平移動前往 X 座標: {target[0]} (忽略 Y 軸)")
        while True:
            player_location = self.game.get_player_location()
            if player_location is None:
                # 找不到玩家黃點時，先放開所有按鍵避免角色失控掉下平台
                self.release_all()
                time.sleep(0.5)
                continue

            x1, y1 = player_location
            x2, y2 = target

            # 判斷是否抵達目標 X 座標 (允許 2 像素的誤差範圍)
            if abs(x1 - x2) < 2:
                self.release_all()
                print(f"🎯 抵達目標 X 座標 ({x1})！")
                break
            else:
                # 判斷要往左走還是往右走
                if x1 < x2:
                    self.hold("RIGHT")
                else:
                    self.hold("LEFT")
                
                # 如果距離目標還很遠 (>30像素)，邊走邊跳躍以跨越小障礙物
                if abs(x2 - x1) > 30:
                    self.press(JUMP_KEY)
                    time.sleep(0.1) # 給予跳躍動作一點緩衝時間
            
            # 短暫暫停，避免無窮迴圈跑太快佔用過多 CPU 資源
            time.sleep(0.05)
