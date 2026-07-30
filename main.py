#import time
import os
import json
import keyboard
from interception import *
from advanced_game import Game
from player import Player

SETTINGS_FILE = "bot_settings.json"

#def setup_user_keys():
    """處理使用者設定，支援讀取上次的設定檔"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            print("\n📦 發現上次儲存的設定檔：")
            print(f"   [1] 螢幕編號: {saved.get('monitor_idx', 1)}")
            print(f"   [2] 跳躍按鍵: {saved.get('jump', 'ALT')}")
            print(f"   [3] 攻擊按鍵: {saved.get('attack', 'CTRL')}")
            print(f"   [4] 撿取按鍵: {saved.get('loot') if saved.get('loot') else '無 (寵物吸寶)'}")
            print(f"   [5] 卡牆攻擊: {'啟用' if saved.get('attack_when_stuck') else '關閉'}")
            print(f"   [6] 遠端模式: {'啟用' if saved.get('is_remote') else '關閉'} (免實體按鍵綁定)")
            
            ans = input("\n👉 是否沿用上次的設定？ (直接按 Enter 沿用，輸入 N 重新設定): ").upper().strip()
            if ans != 'N':
                return saved
        except Exception as e:
            print(f"⚠️ 讀取設定檔失敗，將重新設定。({e})")

    print("\n=== ⚙️ 請進行初始設定 (按 Enter 可使用預設值) ===")
    
    monitor_str = input("1. 請選擇要使用的螢幕 (1 或 2，預設 1): ").strip()
    monitor = int(monitor_str) if monitor_str.isdigit() else 1
    
    jump = input("2. 請輸入【跳躍】按鍵 (預設 ALT): ").upper().strip()
    if not jump: jump = "ALT"
        
    attack = input("3. 請輸入【攻擊】按鍵 (預設 CTRL): ").upper().strip()
    if not attack: attack = "CTRL"
        
    loot = input("4. 請輸入【撿取】按鍵 (預設 Z，有寵物請填 0): ").upper().strip()
    if not loot: loot = "Z"
    if loot == "0": loot = None 
    
    atk_stuck = input("5. 卡牆時是否自動揮刀攻擊一次？ (Y/N，預設 N): ").upper().strip()
    attack_when_stuck = True if atk_stuck == 'Y' else False

    remote_ans = input("6. 是否為遠端連線模式 (無法按實體鍵盤綁定)？ (Y/N，預設 N): ").upper().strip()
    is_remote = True if remote_ans == 'Y' else False
    
    settings = {
        "monitor_idx": monitor,
        "jump": jump,
        "attack": attack,
        "loot": loot,
        "attack_when_stuck": attack_when_stuck,
        "is_remote": is_remote
    }
    
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        print("✅ 設定已自動儲存，下次開啟可直接沿用！")
    except Exception as e:
        print(f"⚠️ 儲存設定檔失敗: {e}")
        
    return settings

#def bind(context, is_remote=False):
    """
    設定攔截過濾器，準備捕捉您實體鍵盤的硬體 ID。
    如果是遠端模式，則直接強制綁定到預設鍵盤 0。
    """
    if is_remote:
        print("\n🌐 [遠端模式啟動] 已跳過實體按鍵等待，強制綁定至系統預設鍵盤 (Device ID: 0)！")
        return 0

    context.set_filter(interception.is_keyboard, interception_filter_key_state.INTERCEPTION_FILTER_KEY_ALL.value)
    print("\n請按下鍵盤上的任意鍵以綁定硬體 (Click any key on your keyboard)...")
    device = None
    while True:
        device = context.wait()
        if interception.is_keyboard(device):
            print(f"✅ 成功綁定硬體鍵盤 ID: {context.get_HWID(device)}")
            print("🛡️ 硬體級防干擾模式已啟動 (不受遠端連線或軟體遮蔽影響)")
            context.set_filter(interception.is_keyboard, 0)
            break
    return device


#if __name__ == "__main__":
    user_settings = setup_user_keys()
    
    c = interception()
    d = bind(c, user_settings.get("is_remote", False))
    
    print(f"\n⚙️ 最終設定套用 -> 跳躍:{user_settings['jump']} | 攻擊:{user_settings['attack']} | 撿取:{user_settings['loot'] if user_settings['loot'] else '無(寵物)'} | 卡牆攻擊:{'啟用' if user_settings.get('attack_when_stuck') else '關閉'}")
    
    # 精準縮小搜尋範圍至左上角 (0, 0, 160, 250)，防止遊戲內傷害數字干擾小黃點辨識
    g = Game((0, 0, 160, 250), monitor_idx=user_settings["monitor_idx"]) 
    p = Player(c, d, g)
    p.jump_key = user_settings["jump"]
    p.attack_key = user_settings["attack"]
    p.loot_key = user_settings["loot"]
    
    g.load_monster_templates(["monster1.png", "monster2.png", "monster3.png"])
    g.load_player_template("player.png")
    
    is_running = False        
    action_flag = None        
    user_boundaries = []      
    left_boundary = None      
    right_boundary = None     
    current_target = None     

    # 近戰攻擊距離 (像素)。大約 70~90 適合劍士/盜賊，若未來玩弓箭手可調高至 200+
    ATTACK_RANGE = 85.0

    last_player_pos = None
    stuck_counter = 0

    def trigger_f5(): global action_flag; action_flag = 'F5'
    def trigger_f8(): global action_flag; action_flag = 'F8'
    def trigger_f9(): global action_flag; action_flag = 'F9'
    def trigger_f10(): global action_flag; action_flag = 'F10'
    
    keyboard.add_hotkey('F5', trigger_f5)
    keyboard.add_hotkey('F8', trigger_f8)
    keyboard.add_hotkey('F9', trigger_f9)
    keyboard.add_hotkey('F10', trigger_f10)
    
    print("\n=================================")
    print("⌨️ 快捷鍵系統已啟用：")
    print(" [F8]  (開局必按) 瞬間記錄小黃點並自動產生 player.png")
    print(" [F5]  設定安全巡邏邊界 (走到左邊按一次，走到右邊再按一次)")
    print(" [F9]  ▶️ 開始腳本")
    print(" [F10] ⏸️ 暫停腳本 (角色停止，準備好可再按 F9 繼續)")
    print("=================================\n")
    print("⏳ 等待指令中... 請進遊戲後先按 F8，再用 F5 定義安全區，最後按 F9 開始。")

#    while True:
        if action_flag:
            if action_flag == 'F8':
                print("📸 [F8] 啟動神級快門！正在尋找小黃點...")
                pos = g.auto_calibrate_player()
                if pos:
                    print(f"🎉 【系統超神】已自動擷取您的小黃點，生成了完美的 'player.png'！")
                    print(f"📍 小地圖相對基準座標: X={pos[0]}, Y={pos[1]}")
                else:
                    print("❌ [F8] 找不到黃點！請確保小地圖已打開且沒被遮擋。")
            
            elif action_flag == 'F5':
                pos = g.find_player_on_minimap()
                if pos:
                    user_boundaries.append(pos)
                    if len(user_boundaries) == 1:
                        print(f"📍 已記錄【第一邊界】: X={pos[0]:.1f}。請控制角色走到另一端，再按一次 F5。")
                    elif len(user_boundaries) >= 2:
                        left_boundary = (min(user_boundaries[0][0], user_boundaries[1][0]), pos[1])
                        right_boundary = (max(user_boundaries[0][0], user_boundaries[1][0]), pos[1])
                        print(f"✅ [F5] 雙點安全巡邏範圍設定完畢！")
                        print(f"   ⬅️ 左邊界 X: {left_boundary[0]:.1f}")
                        print(f"   ➡️ 右邊界 X: {right_boundary[0]:.1f}")
                        user_boundaries = [] 
                else:
                    print("❌ [F5] 找不到人物小黃點，請確認是否已按過 F8！")
            
            elif action_flag == 'F9':
                if not left_boundary or not right_boundary:
                    print("⚠️ 請先使用 F5 設定左右邊界！")
                else:
                    is_running = True
                    current_target = right_boundary 
                    last_player_pos = None
                    stuck_counter = 0
                    print("\n▶️ 腳本啟動！開始狩獵...")
                    
            elif action_flag == 'F10':
                is_running = False
                p.release_all() 
                print("\n⏸️ 腳本已暫停！角色進入發呆模式。")
                
            action_flag = None

#        if is_running:
            player_pos = g.find_player_on_minimap()
            if not player_pos:
                p.release_all()
                time.sleep(0.5)
                continue

            # --- 防卡牆機制：檢查 X 座標是否有變動 ---
            if last_player_pos and abs(player_pos[0] - last_player_pos[0]) <= 1.0:
                stuck_counter += 1
            else:
                stuck_counter = 0
            
            last_player_pos = player_pos

            if stuck_counter >= 12:
                print("🧱 偵測到地形卡住！執行脫困機制...")
                p.release_all() 
                
                if user_settings.get("attack_when_stuck"):
                    print("⚔️ 卡牆反擊！揮刀一次清除可能的障礙物/隱形怪...")
                    p.press(p.attack_key)
                    time.sleep(0.4) 
                
                trying_to_go_right = (current_target[0] > player_pos[0])
                if trying_to_go_right:
                    print("🤸 向左反向跳躍脫困...")
                    p.hold("LEFT")
                    p.press(p.jump_key)
                    time.sleep(0.4)
                    p.release("LEFT")
                else:
                    print("🤸 向右反向跳躍脫困...")
                    p.hold("RIGHT")
                    p.press(p.jump_key)
                    time.sleep(0.4)
                    p.release("RIGHT")
                    
                stuck_counter = 0
                continue

            # 鎖定單層平台 (預設鎖定畫面中間 150~550 高度的怪物)
            monster_info = g.find_closest_monster(y_range=(150, 550))

            # --- 嚴格邊界守衛：判斷追這隻怪會不會超出我們設定的 F5 安全範圍 ---
            valid_monster = None
            if monster_info:
                match_x, match_y, name, distance = monster_info
                
                if distance <= ATTACK_RANGE:
                    valid_monster = monster_info # 已經在攻擊範圍內，直接打
                else:
                    if match_x > (g.window_width // 2): # 怪在右邊，要往右追
                        if right_boundary and player_pos[0] >= right_boundary[0]:
                            pass # 超出右邊界，放棄這隻怪
                        else:
                            valid_monster = monster_info
                    else: # 怪在左邊，要往左追
                        if left_boundary and player_pos[0] <= left_boundary[0]:
                            pass # 超出左邊界，放棄這隻怪
                        else:
                            valid_monster = monster_info

#            if valid_monster:
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
                    # 怪物還沒進範圍，長壓方向鍵靠近
                    if match_x > (g.window_width // 2):
                        p.release("LEFT")
                        p.hold("RIGHT")
                    else:
                        p.release("RIGHT")
                        p.hold("LEFT")
            
            else:
                if stuck_counter == 0: 
                    pass 
                
                # 抵達邊界的判定誤差縮小至 3 像素，確實走到位才掉頭
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
            
            time.sleep(0.05)
