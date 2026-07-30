import time
import random
# 【修改 1】經典版沒有「輪 (Rune)」，所以我們直接移除原本負責解輪的視覺辨識模組，避免報錯。
# from rune_solver import find_arrow_directions 
from interception import *
from game import Game
from player import Player


def bind(context):
    context.set_filter(interception.is_keyboard, interception_filter_key_state.INTERCEPTION_FILTER_KEY_ALL.value)
    print("請按下鍵盤上的任意鍵以綁定硬體 (Click any key on your keyboard)...")
    device = None
    while True:
        device = context.wait()
        if interception.is_keyboard(device):
            print(f"✅ 成功綁定鍵盤裝置 ID: {context.get_HWID(device)}.")
            c.set_filter(interception.is_keyboard, 0)
            break
    return device

def solve_rune(g, p, target):
    """
    【修改 2】廢棄解輪邏輯。
    因為舊版 (Big Bang 以前) 根本沒有解輪機制，這個函式已經被廢棄。
    保留空函式是為了防止其他地方誤呼叫導致程式崩潰。
    """
    print("⚠️ 【警告】經典版沒有輪 (Rune)，不應該觸發此函式。請檢查邏輯。")
    pass


if __name__ == "__main__":
    # 這是 Interception 用來模擬真實硬體鍵盤輸入的必要設定
    c = interception()
    d = bind(c)

    # 【重點修改 3】小地圖的螢幕範圍 (Top, Left, Bottom, Right)
    # ⚠️ 這裡的 (5, 60, 180, 130) 是原版「現代 UI」的座標。
    # 根據你的截圖，舊版的小地圖在畫面「左上角」，請你的同事截圖量測後，把這四個數字換成舊版小地圖的真實像素範圍！
    g = Game((5, 60, 180, 130)) 
    
    p = Player(c, d, g)
    
    # 【重點修改 4】掛機的中心點座標 (X, Y)
    # 這是小地圖上的內部座標。機器人會試圖走到這個點。請依據你們當前練功地圖的中心點進行修改。
    target = (97, 32.5)

    print("🚀 經典版機器人已啟動！開始執行掛機邏輯...")
    
    while True:
        # 1. 偵測是否有其他玩家
        other_location = g.get_other_location()
        if other_location > 0:
            # 這裡可以由你的同事後續擴充：例如發現外人就自動換頻 (按 ESC -> 換頻 -> Enter)
            print("⚠️ 【警告】有其他玩家進入地圖！")

        # 【修改 5】移除偵測「輪」的程式碼
        # 原本這裡會呼叫 g.get_rune_location() 並去解輪，現在我們直接將其註解掉。
        # rune_location = g.get_rune_location()
        # if rune_location is not None:
        #     solve_rune(g, p, rune_location)

        print("🔄 執行攻擊循環...")
        
        # 【重點修改 6】自訂你的打怪腳本
        # 原作者寫的是「劍豪 (Hayato)」在「SS4」地圖的專屬接技 (Q, W, E)。
        # 請你的同事把下面的按鍵，改成舊版職業的按鍵，例如：
        # CTRL = 普攻, SHIFT = 撿物, A = 範圍技 等等。
        
        p.go_to(target) # 確保回到中心點
        
        # --- 以下為範例攻擊迴圈 (請同事自行修改) ---
        p.press("CTRL") # 範例：按 Ctrl 攻擊
        time.sleep(0.5)
        
        p.press("SHIFT") # 範例：按 Shift 撿取物品
        time.sleep(0.5)
        
        p.go_to(target) # 再次確認位置
        
        p.press("LEFT") # 面向左邊
        time.sleep(0.1)
        p.press("CTRL")
        time.sleep(0.5)
        
        p.press("RIGHT") # 面向右邊
        time.sleep(0.1)
        p.press("CTRL")
        time.sleep(1.0)
        # --- 攻擊迴圈結束 ---
