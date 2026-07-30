# ... existing code ...
    def go_to(self, target):
        """
        Attempts to move player to a specific (x, y) location on the screen.
        【重點修改】已將此函式簡化為「純水平(左右)移動」，忽略 Y 軸(高度)差異。
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
                # (如果你的掛機平台很平坦，不需要跳躍，可以把下面這兩行註解掉)
                if abs(x2 - x1) > 30:
                    self.press(JUMP_KEY)
                    time.sleep(0.1) # 給予跳躍動作一點緩衝時間
            
            # 短暫暫停，避免無窮迴圈跑太快佔用過多 CPU 資源
            time.sleep(0.05)
