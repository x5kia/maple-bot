import gdi_capture
import numpy as np
import win32gui

# 這些是小地圖上圖示的 BGRA 顏色碼
PLAYER_BGRA = (68, 221, 255, 255)
RUNE_BGRA = (255, 102, 221, 255)
ENEMY_BGRA = (0, 0, 255, 255)
GUILD_BGRA = (255, 102, 102, 255)
BUDDY_BGRA = (225, 221, 17, 255)


class Game:
    def __init__(self, region):
        # 尋找指定標題的遊戲視窗
        self.hwnd = win32gui.FindWindow(None, "新楓之谷：經典版")
        if not self.hwnd:
            print("❌ 【嚴重錯誤】找不到目標視窗！")
            print("   👉 請檢查：遊戲是否真的已經開啟？視窗標題是否【完全符合】'新楓之谷：經典版'？")
            raise Exception("Window not found")

        # 設定小地圖的擷取範圍
        self.top, self.left, self.bottom, self.right = region[0], region[1], region[2], region[3]

    def get_rune_image(self):
        """
        【已廢棄】經典版沒有輪 (Rune)。
        直接回傳 None，避免 IndentationError 與後續錯誤。
        """
        return None

    def locate(self, *color):
        """
        尋找並回傳指定顏色 (BGRA) 在小地圖上的中心點座標。
        """
        with gdi_capture.CaptureWindow(self.hwnd) as img:
            locations = []
            if img is None:
                print("⚠️ 【警告】無法擷取遊戲畫面！請確定遊戲沒有被「最小化」。")
                return locations
            
            try:
                # 裁切小地圖範圍
                img_cropped = img[self.left:self.right, self.top:self.bottom]
                height, width = img_cropped.shape[0], img_cropped.shape[1]
                
                # 將 3D 陣列重塑為 2D 陣列以加速比對
                img_reshaped = np.reshape(img_cropped, ((width * height), 4), order="C")
                
                for c in color:
                    sum_x, sum_y, count = 0, 0, 0
                    # 找出所有符合該 BGRA 顏色的像素索引
                    matches = np.where(np.all((img_reshaped == c), axis=1))[0]
                    for idx in matches:
                        sum_x += idx % width
                        sum_y += idx // width
                        count += 1
                    if count > 0:
                        x_pos = sum_x / count
                        y_pos = sum_y / count
                        locations.append((x_pos, y_pos))
                        
            except Exception as e:
                print(f"❌ 【錯誤】處理小地圖影像時發生例外狀況: {e}")
                print(f"   👉 當前傳入的範圍座標: Top={self.top}, Left={self.left}, Bottom={self.bottom}, Right={self.right}")
                print("   👉 解決方法：請重新校準 main.py 中的 region 範圍，確保沒有超出遊戲視窗。")

            return locations

    def get_player_location(self):
        """回傳玩家(黃點)在小地圖上的 (x, y) 座標。"""
        location = self.locate(PLAYER_BGRA)
        return location[0] if len(location) > 0 else None

    def get_rune_location(self):
        """【已廢棄】經典版沒有輪。直接回傳 None。"""
        return None

    def get_other_location(self):
        """回傳 True/False 代表小地圖上是否有其他玩家/怪物。"""
        location = self.locate(ENEMY_BGRA, GUILD_BGRA, BUDDY_BGRA)
        return len(location) > 0
