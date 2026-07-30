import time
import keyboard
import os
import sys
import json
from interception import *
from advanced_game import Game
from player import Player

# 設定檔儲存路徑
CONFIG_FILE = "bot_settings.json"

def load_settings():
    """讀取上次儲存的設定檔"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 讀取設定檔失敗: {e}")
    return None

def save_settings(settings):
    """將設定儲存到檔案中"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"⚠️ 儲存設定檔失敗: {e}")

def setup_user_keys():
    """引導使用者輸入設定，並提供沿用上次設定的選項"""
    print("\n=================================")
    print("      MapleBot 進階掛機設定")
    print("=================================")
    
    old_settings = load_settings()
    if old_settings:
        print("\n📝 發現上次的設定檔：")
        print(f"  [1] 螢幕編號: {old_settings.get('monitor_idx', 1)}")
        print(f"  [2] 跳躍鍵: {old_settings.get('jump', 'ALT')}")
        print(f"  [3] 攻擊鍵: {old_settings.get('attack', 'CTRL')}")
        print(f"  [4] 撿取鍵: {old_settings.get('loot', '0 (無)')}")
        print(f"  [5] 卡牆反擊: {'開啟' if old_settings.get('anti_stuck_attack', False) else '關閉'}")
        print(f"  [6] 遠端模式: {'開啟 (免按鍵綁定)' if old_settings.get('remote_mode', False) else '關閉'}")
        
        choice = input("\n👉 是否沿用上次的設定？ (直接按 Enter 沿用 / 輸入 'N' 重新設定): ").strip().upper()
        if choice == '' or choice == 'Y':
            return old_settings

    print("\n⚙️ 請依照指示輸入新的按鍵 (例如: ALT, CTRL, Z, X, SHIFT, SPACE)...")
    
    try:
        monitor_idx = int(input("[1] 請輸入遊戲所在的螢幕編號 (通常主螢幕為 1, 副螢幕為 2): ") or 1)
    except:
        monitor_idx = 1
        
    jump_key = input("[2] 請輸入【跳躍】按鍵 (預設 ALT): ").strip().upper() or "ALT"
    attack_key = input("[3] 請輸入【攻擊】按鍵 (預設 CTRL): ").strip().upper() or "CTRL"
    loot_key = input("[4] 請輸入【撿取】按鍵 (填 0 代表不撿/寵物吸寶，預設 0): ").strip().upper() or "0"
    if loot_key == "0":
        loot_key = None
        
    anti_stuck = input("[5] 是否開啟【卡牆先揮刀打箱子/隱形怪】功能？ (Y/N, 預設 Y): ").strip().upper()
    anti_stuck_attack = False if anti_stuck == 'N' else True

    remote_input = input("[6] 是否為【遠端連線模式】(TeamViewer/AnyDesk)？開啟將跳過實體按鍵綁定 (Y/N, 預設 N): ").strip().upper()
    remote_mode = True if remote_input == 'Y' else False
        
    new_settings = {
        "monitor_idx": monitor_idx,
        "jump": jump_key,
        "attack": attack_key,
        "loot": loot_key,
        "anti_stuck_attack": anti_stuck_attack,
        "remote_mode": remote_mode
    }
    
    save_settings(new_settings)
    print("✅ 設定已儲存，下次開啟可直接沿用！")
    return new_settings

def bind(context, remote_mode=False):
    if remote_mode:
        print("🌐 [遠端模式] 已啟用！強制將硬體 ID 綁定至預設鍵盤 (Device 0)。")
        return 0 # 強制回傳第一把鍵盤的 ID，跳過 wait
        
    context.set_filter(interception.is_keyboard, interception_filter_key_state.INTERCEPTION_FILTER_KEY_ALL.value)
    print("請按下鍵盤上的任意鍵以綁定硬體 (若使用遠端軟體請重開並選擇遠端模式)...")
    device = None
    while True:
        device = context.wait()
        if interception.is_keyboard(device):
            print(f"✅ 成功綁定鍵盤裝置 ID: {context.get_HWID(device)}.")
            context.set_filter(interception.is_keyboard, 0)
            break
    return device

if __name__ == "__main__":
    user_settings = setup_user_keys()
    
    c = interception()
    d = bind(c, user_settings.get("remote_mode", False))

    print(f"\n⚙️ 最終設定套用 -> 跳躍:{user_settings['jump']} | 攻擊:{user_settings['attack']} | 撿取:{user_settings['loot'] if user_settings['loot'] else '無(寵物)'}")
    
    # 鎖定左上角小地圖範圍 (0, 0, 160, 250) 避免抓到遊戲內的傷害數字
    g = Game((0, 0, 160, 250), monitor_idx=user_settings["monitor_idx"]) 
    p = Player(c, d, g)
    p.jump_key = user_settings["jump"]
    p.attack_key = user_settings["attack"]
    p.loot_key = user_settings["loot"]
    
    g.load_monster_templates(["monster1.png", "monster2.png", "monster3.png"])
    g.load_player_template("player.png")
    
    is_running = False        
    action_flag = None        
    
    # 全新 F5 / F6 交叉比對系統變數
    boundary_f5 = None
    boundary_f6 = None
    left_boundary = None      
    right_boundary = None     
    
    current_target = None     
    ATTACK_RANGE = 75.0 # 近戰建議 70~90，遠程可自行調大 (如 250)

    def trigger_f5(): global action_flag; action_flag = 'F5'
    def trigger_f6(): global action_flag; action_flag = 'F6'
    def trigger_f8(): global action_flag; action_flag = 'F8'
    def trigger_f9(): global action_flag; action_flag = 'F9'
    def trigger_f10(): global action_flag; action_flag = 'F10'
    
    keyboard.add_hotkey('F5', trigger_f5)
    keyboard.add_hotkey('F6', trigger_f6)
    keyboard.add_hotkey('F8', trigger_f8)
    keyboard.add_hotkey('F9', trigger_f9)
    keyboard.add_hotkey('F10', trigger_f10)
    
    print("\n=================================")
    print("⌨️ 快捷鍵系統已啟用：")
    print(" [F8]  (開局必按) 瞬間記錄小黃點並自動產生 player.png")
    print(" [F5]  設定巡邏邊界 A (走到左或右定點按一次)")
    print(" [F6]  設定巡邏邊界 B (走到另一端定點按一次)")
    print(" [F9]  ▶️ 開始腳本")
    print(" [F10] ⏸️ 暫停腳本 (角色停止，準備好可再按 F9 繼續)")
    print("=================================\n")
    print("⏳ 等待指令中... 請進遊戲後先按 F8 產生圖片，再按 F5 與 F6 設定範圍，最後按 F9 開始。")

    last_player_pos = None
    stuck_counter = 0

    while True:
        # 1. 處理快捷鍵觸發動作
        if action_flag:
            if action_flag == 'F8':
                print("\n📸 [F8] 尋找小黃點中... 請確保遊戲未被遮擋！")
                pos = g.auto_calibrate_player()
                if pos:
                    print(f"🎉 【系統超神】已自動擷取您的小黃點，並在資料夾生成了完美的 'player.png'！")
                else:
                    print(f"❌ 擷取失敗，請確認是否在小地圖範圍內。")
                time.sleep(0.5)
                
            elif action_flag == 'F5':
                pos = g.find_player_on_minimap()
                if pos:
                    boundary_f5 = pos
                    print(f"📍 已記錄【邊界 A (F5)】: 依據小黃點 X={pos[0]:.1f}")
                    # 如果 F6 也設定了，就交叉比對決定左右
                    if boundary_f6:
                        left_boundary = (min(boundary_f5[0], boundary_f6[0]), pos[1])
                        right_boundary = (max(boundary_f5[0], boundary_f6[0]), pos[1])
                        print(f"✅ [系統] 雙點安全巡邏範圍設定完畢！")
                        print(f"   ⬅️ 左邊界 X: {left_boundary[0]:.1f}")
                        print(f"   ➡️ 右邊界 X: {right_boundary[0]:.1f}")
                else:
                    print("❌ [F5] 找不到人物小黃點，請確認是否已按過 F8！")
                time.sleep(0.3)
                
            elif action_flag == 'F6':
                pos = g.find_player_on_minimap()
                if pos:
                    boundary_f6 = pos
                    print(f"📍 已記錄【邊界 B (F6)】: 依據小黃點 X={pos[0]:.1f}")
                    # 如果 F5 也設定了，就交叉比對決定左右
                    if boundary_f5:
                        left_boundary = (min(boundary_f5[0], boundary_f6[0]), pos[1])
                        right_boundary = (max(boundary_f5[0], boundary_f6[0]), pos[1])
                        print(f"✅ [系統] 雙點安全巡邏範圍設定完畢！")
                        print(f"   ⬅️ 左邊界 X: {left_boundary[0]:.1f}")
                        print(f"   ➡️ 右邊界 X: {right_boundary[0]:.1f}")
                else:
                    print("❌ [F6] 找不到人物小黃點，請確認是否已按過 F8！")
                time.sleep(0.3)
            
            elif action_flag == 'F9':
                if not left_boundary or not right_boundary:
                    print("⚠️ [警告] 請先使用 F5 和 F6 分別設定左右巡邏邊界！")
                else:
                    is_running = True
                    # 預設先往右走
                    current_target = right_boundary
                    print("\n▶️ [F9] 腳本開始執行！")
            
            elif action_flag == 'F10':
                is_running = False
                p.release_all() # 暫停時立刻釋放所有按鍵
                print("\n⏸️ [F10] 腳本已暫停。")
                
            action_flag = None

        if is_running:
            player_pos = g.find_player_on_minimap()
            
            if not player_pos:
                print("❌ 找不到玩家 (小黃點)！請確認小地圖是否被遮擋。")
                p.release_all()
                time.sleep(1)
                continue
            
            # --- 防卡牆機制 (Anti-Stuck) ---
            if last_player_pos and abs(player_pos[0] - last_player_pos[0]) <= 1.0:
                stuck_counter += 1
            else:
                stuck_counter = 0
            last_player_pos = player_pos
            
            if stuck_counter >= 10:
                print("🧱 偵測到地形卡住！執行脫困機制...")
                p.release_all()
                
                # 選用的脫困攻擊機制：先揮一刀看看是不是撞到隱形怪/箱子
                if user_settings.get("anti_stuck_attack", True):
                    print("⚔️ 卡牆反擊！揮刀一次清除可能的障礙物/隱形怪...")
                    p.press(p.attack_key)
                    time.sleep(0.6)
                
                # 反向跳躍脫困
                if current_target == right_boundary:
                    print("↩️ 向左反向跳躍脫困...")
                    p.hold("LEFT")
                    time.sleep(0.1)
                    p.press(p.jump_key)
                    time.sleep(0.3)
                    p.release("LEFT")
                else:
                    print("↪️ 向右反向跳躍脫困...")
                    p.hold("RIGHT")
                    time.sleep(0.1)
                    p.press(p.jump_key)
                    time.sleep(0.3)
                    p.release("RIGHT")
                
                stuck_counter = 0
                time.sleep(0.5)
                continue

            # 鎖定單層平台 (預設鎖定畫面中間 150~550 高度的怪物，避免追上層或下層的怪卡牆)
            monster_info = g.find_closest_monster(y_range=(150, 550))

            # 嚴格邊界守衛：判斷追這隻怪會不會超出我們設定的 F5/F6 安全範圍
            valid_monster = None
            if monster_info:
                match_x, match_y, name, distance = monster_info
                
                if distance <= ATTACK_RANGE:
                    valid_monster = monster_info 
                else:
                    if match_x > (g.window_width // 2): 
                        if right_boundary and player_pos[0] >= right_boundary[0]:
                            pass 
                        else:
                            valid_monster = monster_info
                    else: 
                        if left_boundary and player_pos[0] <= left_boundary[0]:
                            pass 
                        else:
                            valid_monster = monster_info

            if valid_monster:
                match_x, match_y, name, distance = valid_monster
                print(f"🎯 追擊目標: {name} (距離: {distance:.1f})")
                
                if distance <= ATTACK_RANGE:
                    p.release_all() 
                    print("⚔️ 進入攻擊範圍，開砍！")
                    p.press(p.attack_key)
                    time.sleep(0.5) 
                    
                    if p.loot_key:
                        p.press(p.loot_key)
                        time.sleep(0.2)
                else:
                    if match_x > (g.window_width // 2):
                        p.release("LEFT")
                        p.hold("RIGHT")
                    else:
                        p.release("RIGHT")
                        p.hold("LEFT")
            
            else:
                if stuck_counter == 0: 
                    pass 
                
                # 抵達邊界判定：誤差縮小至 3 像素以內，確保真的走到邊界
                if abs(player_pos[0] - current_target[0]) <= 3:
                    if current_target == right_boundary:
                        current_target = left_boundary
                        print(f"↩️ 抵達右邊界 (X={player_pos[0]:.1f})，掉頭往左！")
                    else:
                        current_target = right_boundary
                        print(f"↪️ 抵達左邊界 (X={player_pos[0]:.1f})，掉頭往右！")
                
                if current_target[0] > player_pos[0]:
                    p.release("LEFT")
                    p.hold("RIGHT")
                else:
                    p.release("RIGHT")
                    p.hold("LEFT")
            
            # 給予一點微小的延遲降低 CPU 佔用，並讓長壓事件生效
            time.sleep(0.05)
