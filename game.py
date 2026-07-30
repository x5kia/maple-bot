#import numpy as np
import win32gui
import win32con
import cv2
import math 
import os
import mss
import ctypes

# 解決 Windows DPI 縮放導致的截圖失真問題
ctypes.windll.user32.SetProcessDPIAware()

#class Game:
    def __init__(self, region, monitor_idx=1):
        self.hwnd = win32gui.FindWindow(None, "新楓之谷：經典版")
        if not self.hwnd:
            print("❌ 【嚴重錯誤】找不到目標視窗！請確保遊戲標題為 '新楓之谷：經典版'")
            raise Exception("Window not found")
            
        self.monitor_idx = monitor_idx
            
        try:
            with mss.mss() as sct:
                if self.monitor_idx >= len(sct.monitors):
                    print(f"⚠️ 找不到第 {self.monitor_idx} 台螢幕，強制退回第 1 台。")
                    self.monitor_idx = 1
                    
                target_monitor = sct.monitors[self.monitor_idx]
                mon_left = target_monitor["left"]
                mon_top = target_monitor["top"]

            # 強制將遊戲視窗移動到指定螢幕的左上角 (0, 0)
            win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
            win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOP, mon_left, mon_top, 0, 0, 
                                  win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
            win32gui.SetForegroundWindow(self.hwnd)
            print(f"🪟 [系統] 已成功將視窗鎖定至【第 {self.monitor_idx} 台螢幕】左上角 ({mon_left}, {mon_top}) 並置頂！")
        except Exception as e:
            print(f"⚠️ [警告] 視窗位移或置頂失敗，請手動確保遊戲在最上層: {e}")
        
        rect = win32gui.GetWindowRect(self.hwnd)
        self.window_width = rect[2] - rect[0]
        self.window_height = rect[3] - rect[1]
        
        self.top, self.left, self.bottom, self.right = region[0], region[1], region[2], region[3]
        self.monster_templates = []
        self.player_template = None

#    def load_monster_templates(self, file_names):
        print("\n🔍 開始載入怪物圖片模板...")
        for name in file_names:
            if os.path.exists(name):
                template = cv2.imread(name)
                if template is None:
                    continue
                self.monster_templates.append({
                    "name": name,
                    "img": template,
                    "h": template.shape[0],
                    "w": template.shape[1]
                })
                print(f"  ✔️ 成功載入: {name}")
            else:
                print(f"  ⚠️ 找不到檔案: {name} (已略過)")
                
    def load_player_template(self, filename="player.png"):
        print(f"\n🔍 檢查玩家小黃點模板: {filename}")
        if os.path.exists(filename):
            self.player_template = cv2.imread(filename)
            print(f"  ✔️ 發現既存的: {filename}")
        else:
            self.player_template = None
            print(f"  ⚠️ 尚未生成 {filename} (請進入遊戲後按 F8 讓系統自動生成)")

#    def find_player_on_minimap(self, threshold=0.6):
        if self.player_template is None:
            return None

        try:
            with mss.mss() as sct:
                monitor = sct.monitors[self.monitor_idx]
                sct_img = sct.grab(monitor)
                img = np.array(sct_img)
                
                # 裁切出小地圖範圍
                minimap_img = img[self.top:self.bottom, self.left:self.right]
                
                # 自動存一張圖供除錯檢查是否抓錯範圍
                if not hasattr(self, "debug_minimap_saved"):
                    cv2.imwrite("debug_minimap.png", minimap_img)
                    print(f"📸 【除錯】已將「尋找小黃點的區域」存成 'debug_minimap.png'！")
                    self.debug_minimap_saved = True
                
                if minimap_img.size == 0:
                    return None
                    
                minimap_bgr = cv2.cvtColor(minimap_img, cv2.COLOR_BGRA2BGR)
                res = cv2.matchTemplate(minimap_bgr, self.player_template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                
                if max_val >= threshold:
                    # 回傳小地圖內的相對中心點 X, Y
                    player_x = max_loc[0] + (self.player_template.shape[1] // 2)
                    player_y = max_loc[1] + (self.player_template.shape[0] // 2)
                    return (player_x, player_y)
        except Exception as e:
            print(f"❌ 尋找玩家時發生錯誤: {e}")
        return None

#    def auto_calibrate_player(self):
        """
        利用經典版小黃點的「專屬顏色」自動尋找玩家，
        並裁切生成 player.png 供後續 F5 和打怪時比對使用。
        """
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[self.monitor_idx]
                sct_img = sct.grab(monitor)
                img = np.array(sct_img)
                
                minimap_img = img[self.top:self.bottom, self.left:self.right]
                if minimap_img.size == 0:
                    return None
                    
                minimap_bgr = cv2.cvtColor(minimap_img, cv2.COLOR_BGRA2BGR)
                
                # 定義小黃點的 BGR 顏色範圍
                lower_yellow = np.array([50, 200, 240])
                upper_yellow = np.array([85, 240, 255])
                mask = cv2.inRange(minimap_bgr, lower_yellow, upper_yellow)
                
                y_coords, x_coords = np.where(mask > 0)
                
                if len(y_coords) > 0:
                    center_y = int(np.mean(y_coords))
                    center_x = int(np.mean(x_coords))
                    
                    half = 4 # 抓取 9x9 的正方形
                    if (center_y - half >= 0 and center_y + half + 1 <= minimap_bgr.shape[0] and
                        center_x - half >= 0 and center_x + half + 1 <= minimap_bgr.shape[1]):
                        
                        template = minimap_bgr[center_y - half : center_y + half + 1, center_x - half : center_x + half + 1]
                        cv2.imwrite("player.png", template)
                        self.player_template = template 
                        
                        # 回傳在小地圖上的相對座標供終端機顯示
                        return (center_x, center_y)
        except Exception as e:
            print(f"❌ 自動定位小黃點時發生錯誤: {e}")
        return None

#    def find_closest_monster(self, threshold=0.55, cross_platform=False, y_range=(150, 550)):
        if not self.monster_templates:
            return None

        center_x = self.window_width // 2
        center_y = self.window_height // 2
        best_match = None
        min_distance = float('inf')

        try:
            with mss.mss() as sct:
                monitor = sct.monitors[self.monitor_idx] 
                sct_img = sct.grab(monitor)
                img = np.array(sct_img)
                
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                for tpl in self.monster_templates:
                    res = cv2.matchTemplate(img_bgr, tpl["img"], cv2.TM_CCOEFF_NORMED)
                    loc = np.where(res >= threshold)
                    
                    for pt in zip(*loc[::-1]): 
                        match_x = pt[0] + (tpl["w"] // 2)
                        match_y = pt[1] + (tpl["h"] // 2)
                        
                        # --- 【關鍵】鎖定單一平台高度 ---
                        if not cross_platform:
                            if match_y < y_range[0] or match_y > y_range[1]:
                                continue # 怪物太高或太低 (不在同一層)，直接假裝沒看到
                        
                        distance = math.sqrt((match_x - center_x)**2 + (match_y - center_y)**2)
                        
                        if distance < min_distance:
                            min_distance = distance
                            best_match = (match_x, match_y, tpl["name"], distance)
        except Exception as e:
            print(f"❌ 視覺辨識發生錯誤: {e}")
            
        return best_match
