import gdi_capture
import numpy as np

# These are colors taken from the mini-map in BGRA format.
PLAYER_BGRA = (68, 221, 255, 255)
RUNE_BGRA = (255, 102, 221, 255)
ENEMY_BGRA = (0, 0, 255, 255)
GUILD_BGRA = (255, 102, 102, 255)
BUDDY_BGRA = (225, 221, 17, 255)


class Game:
    def __init__(self, region):
        # 【修改 2】捨棄原本靠 .exe 檔名尋找視窗的方法，改用精準的視窗標題尋找。
        # 這樣可以確保抓到的是「新楓之谷：經典版」而不是其他背景程式。
        self.hwnd = win32gui.FindWindow(None, "新楓之谷：經典版")
        if not self.hwnd:
            print("❌ 【嚴重錯誤】找不到目標視窗！")
            print("   👉 請檢查：")
            print("      1. 遊戲是否真的已經開啟？")
            print("      2. 遊戲視窗標題是否【完全符合】'新楓之谷：經典版'？(注意全半形與空格)")
            print("      3. 嘗試以系統管理員身分執行此 Python 腳本。")
            raise Exception("Window not found") # 找不到視窗直接中斷程式，避免後續連鎖錯誤

        # 這些值代表小地圖在螢幕上的像素位置 (上, 左, 下, 右)
        self.top, self.left, self.bottom, self.right = region[0], region[1], region[2], region[3]

    def get_rune_image(self):
# ... existing code ...
    def locate(self, *color):
        """
        Returns the median location of BGRA tuple(s).
        這裡的邏輯是純數學與像素比對，不需要修改，完全相容舊版。
        """
        with gdi_capture.CaptureWindow(self.hwnd) as img:
            locations = []
            if img is None:
                print("⚠️ 【警告】無法擷取遊戲畫面！")
                print("   👉 請檢查：")
                print("      1. 遊戲視窗是否被【最小化】了？(此擷取方法通常不支援最小化)")
                print("      2. 遊戲是否被全螢幕的應用程式完全遮擋？請嘗試保持遊戲在前景。")
            else:
                """
                The screenshot of the application window is returned as a 3-d np.ndarray, 
                containing 4-length np.ndarray(s) representing BGRA values of each pixel.
                """
                # Crop the image to show only the mini-map.
                try:
                    img_cropped = img[self.left:self.right, self.top:self.bottom]
                    height, width = img_cropped.shape[0], img_cropped.shape[1]
                    
                    if height == 0 or width == 0:
                        print("⚠️ 【警告】擷取到的小地圖範圍為空！")
                        print(f"   👉 當前傳入的範圍座標: Top={self.top}, Left={self.left}, Bottom={self.bottom}, Right={self.right}")
                        print("   👉 解決方法：請重新校準小地圖的擷取範圍 (region參數)。")
                        return locations

                    # Reshape the image from 3-d to 2-d by row-major order.
                    img_reshaped = np.reshape(img_cropped, ((width * height), 4), order="C")
                    
                    for c in color:
                        sum_x, sum_y, count = 0, 0, 0
                        # Find all index(s) of np.ndarray matching a specified BGRA tuple.
                        matches = np.where(np.all((img_reshaped == c), axis=1))[0]
                        for idx in matches:
# ... existing code ...
                        if count > 0:
                            x_pos = sum_x / count
                            y_pos = sum_y / count
                            locations.append((x_pos, y_pos))
                        else:
                            # 針對除錯模式的額外提示 (可選，避免洗頻平時可註解掉)
                            # print(f"🔍 【提示】在小地圖區域內找不到指定顏色: {c}")
                            # print("   👉 如果這是玩家(黃點)顏色，請檢查小地圖是否開啟，或確認 BGRA 色碼是否與舊版一致。")
                            pass
                            
                except Exception as e:
                    print(f"❌ 【錯誤】處理小地圖影像時發生例外狀況: {e}")
                    print("   👉 可能原因：傳入的 region (座標範圍) 超出了遊戲視窗的實際大小。")

            return locations

    def get_player_location(self):
        """
        Returns the (x, y) position of the player on the mini-map.
        """
        location = self.locate(PLAYER_BGRA)
        return location[0] if len(location) > 0 else None

    def get_rune_location(self):
        """
        Returns the (x, y) position of the rune on the mini-map.
        """
        location = self.locate(RUNE_BGRA)
        return location[0] if len(location) > 0 else None

    def get_other_location(self):
        """
        Returns a boolean value representing the presence of any other players on the mini-map.
        """
        location = self.locate(ENEMY_BGRA, GUILD_BGRA, BUDDY_BGRA)
        return len(location) > 0
