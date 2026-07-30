import time
import os
import json
import math
from interception import *
from advanced_game import Game
from player import Player

CONFIG_FILE = "bot_settings.json"
ATTACK_RANGE = 80.0  # 攻擊距離 (近戰劍士建議 70~90，未來若是遠程可調大至 200+)

def load_settings():
    """讀取上次的設定檔"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def save_settings(settings):
    """儲存設定檔"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"⚠️ 儲存設定失敗: {e}")

def setup_user_keys():
    """讓使用者輸入按鍵設定，並支援記憶功能"""
    print("\n===================================================")
    print("           MapleBot 經典版 - 智慧設定精靈")
    print("===================================================")
    
    saved_settings = load_settings()
    if saved_settings:
        print("\n💡 發現上次的設定：")
        print(f"   [1] 螢幕編號: {saved_settings.get('monitor', 1)}")
        print(f"   [2] 跳躍鍵:   {saved_settings.get('jump', 'ALT')}")
        print(f"   [3] 攻擊鍵:   {saved_settings.get('attack', 'CTRL')}")
        print(f"   [4] 撿物鍵:   {saved_settings.get('loot', 'Z')}")
        anti_stuck_opt = saved_settings.get('anti_stuck_attack', 'N')
        print(f"   [5] 卡牆反擊: {'是 (Y)' if anti_stuck_opt == 'Y' else '否 (N)'}")
        remote_mode = saved_settings.get('remote_mode', 'N')
        print(f"   [6] 遠端模式: {'是 (Y) - 免按鍵綁定' if remote_mode == 'Y' else '否 (N)'}")
        
        use_saved = input("\n👉 是否沿用上次設定？ (直接按 Enter 沿用 / 輸入 N 重新設定): ").strip().upper()
        if use_saved != 'N':
            return saved_settings

    print("\n請依序輸入您的按鍵設定 (或直接按 Enter 使用預設值)：")
    
    m_idx = input("請輸入遊戲所在的螢幕編號 (預設 1): ").strip()
    m_idx = int(m_idx) if m_idx.isdigit() else 1
    
    j_key = input("請輸入【跳躍】按鍵 (預設 ALT): ").strip().upper() or "ALT"
    a_key = input("請輸入【攻擊】按鍵 (預設 CTRL): ").strip().upper() or "CTRL"
    l_key = input("請輸入【撿物】按鍵 (預設 Z，若為寵物吸寶請輸入 0): ").strip().upper() or "Z"
    if l_key == "0":
        l_key = None
        print("  *(已啟用寵物吸寶，關閉手動撿取)*")
        
    anti_stuck = input("是否啟用【卡牆先揮刀反擊】功能？(Y/N，預設 N): ").strip().upper() or "N"
    remote = input("是否啟用【遠端連線模式】(跳過實體按鍵綁定)？(Y/N，預設 N): ").strip().upper() or "N"
    
    settings = {
        'monitor': m_idx,
        'jump': j_key,
        'attack': a_key,
        'loot': l_key,
        'anti_stuck_attack': anti_stuck,
        'remote_mode': remote
    }
    
    save_settings(settings)
    print("\n✅ 設定已自動記憶，下次可直接沿用！")
    return settings

def bind(context, remote_mode=False):
    """
    綁定硬體裝置。若開啟 remote_mode 則強制使用 device 0，
    解決遠端軟體無法觸發實體中斷的問題。
    """
    if remote_mode:
        print("\n🌐 [遠端模式啟用] 強制綁定預設鍵盤 (Device 1)...")
        # 直接回傳 1 作為預設鍵盤 ID
        return 1
        
    context.set_filter(interception.is_keyboard, interception_filter_key_state.INTERCEPTION_FILTER_KEY_ALL.value)
    print("\n請按下【實體鍵盤】上的任意鍵以綁定硬體 (Click any key on your keyboard)...")
    device = None
    while True:
        device = context.wait()
        if interception.is_keyboard(device):
            print(f"✅ 成功綁定鍵盤裝置 ID: {context.get_HWID(device)}.")
            context.set_filter(interception.is_keyboard, 0)
            break
    return device

if __name__ == "__main__":
    settings = setup_user_keys()
    
    c = interception()
    d = bind(c, remote_mode=(settings.get('remote_mode') == 'Y'))

    # 初始化遊戲視覺引擎 (小地圖範圍: Top, Left, Bottom, Right)
    # 【修改】長寬擴大為 400x300，確保完整拍下弓箭手訓練場等高地圖
    g = Game((0, 0, 400, 300), monitor_idx=settings['monitor']) 
    
    p = Player(c, d, g)
    p.jump_key = settings['jump']
    p.attack_key = settings['attack']
    p.loot_key = settings['loot']
    
    # 載入怪物圖片 (請在同資料夾放入 monster1.png, monster2.png...)
    monster_files = [f for f in os.listdir('.') if f.startswith('monster') and f.endswith('.png')]
    if not monster_files:
        print("⚠️ 找不到任何以 'monster' 開頭的 png 圖片，外掛將只會巡邏不會打怪！")
    g.load_monster_templates(monster_files)
    g.load_player_template()

    boundary_f5 = None
    boundary_f6 = None
    left_boundary = None
    right_boundary = None
    current_target = None
    
    is_running = False
    
    # 防卡牆變數
    last_x = 0
    stuck_counter = 0

    print("\n===================================================")
    print("⌨️  快捷鍵系統已啟用：")
    print("  [F8]  (開局必按) 瞬間記錄小黃點並自動產生 player.png 與 debug_minimap.png")
    print("  [F5]  設定巡邏邊界 A (走到左或右定點按一次)")
    print("  [F6]  設定巡邏邊界 B (走到另一端定點按一次)")
    print("  [F9]  ▶  開始腳本")
    print("  [F10] ⏸  暫停腳本 (角色停止，準備好可再按 F9 繼續)")
    print("===================================================\n")
    print("⏳ 等待指令中... 請進遊戲後先按 F8 產生圖片，再按 F5 與 F6 設定範圍，最後按 F9 開始。")

    while True:
        # 1. 處理快捷鍵觸發動作
        import win32api
        action_flag = None
        if getattr(win32api, 'GetAsyncKeyState', None):
            if win32api.GetAsyncKeyState(0x77) & 0x8000: action_flag = 'F8' # F8
            elif win32api.GetAsyncKeyState(0x74) & 0x8000: action_flag = 'F5' # F5
            elif win32api.GetAsyncKeyState(0x75) & 0x8000: action_flag = 'F6' # F6
            elif win32api.GetAsyncKeyState(0x78) & 0x8000: action_flag = 'F9' # F9
            elif win32api.GetAsyncKeyState(0x79) & 0x8000: action_flag = 'F10'# F10

        if action_flag:
            if action_flag == 'F8':
                print("\n📸 [F8] 尋找小黃點中... 請確保遊戲未被遮擋！")
                pos = g.auto_calibrate_player()
                if pos:
                    print(f"🎉 【系統超神】已自動擷取小黃點 (X={pos[0]:.1f}, Y={pos[1]:.1f})")
                    print(f"   已產生 'player.png' 與 'debug_minimap.png'，請去資料夾檢查！")
                else:
                    print("❌ [F8] 找不到人物小黃點，請檢查小地圖是否開啟或有被遮擋。")
                time.sleep(0.5)

            elif action_flag == 'F5':
                pos = g.find_player_on_minimap()
                if pos:
                    boundary_f5 = pos
                    print(f"📍 已記錄【邊界 A (F5)】: 真實座標 X={pos[0]:.1f}, Y={pos[1]:.1f}")
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
                    print(f"📍 已記錄【邊界 B (F6)】: 真實座標 X={pos[0]:.1f}, Y={pos[1]:.1f}")
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
                    print("⚠️ 請先使用 F5 與 F6 設定好左/右邊界，才能開始！")
                else:
                    if not is_running:
                        print("▶️ [F9] 腳本啟動！開始狩獵！")
                        is_running = True
                        current_target = right_boundary
                        p.release_all()
                time.sleep(0.3)

            elif action_flag == 'F10':
                if is_running:
                    print("⏸️ [F10] 腳本已暫停！")
                    is_running = False
                    p.release_all()
                time.sleep(0.3)

        if is_running:
            player_pos = g.find_player_on_minimap()
            if not player_pos:
                time.sleep(0.1)
                continue

            # ---------------- [防卡牆系統] ----------------
            if abs(player_pos[0] - last_x) < 1.0:
                stuck_counter += 1
            else:
                stuck_counter = 0
            last_x = player_pos[0]

            if stuck_counter > 20: 
                print("⚠️ 偵測到地形卡住！執行脫困機制...")
                p.release_all()
                
                # 選用的：卡牆先揮刀反擊功能 (打掉隱形怪或箱子)
                if settings.get('anti_stuck_attack') == 'Y':
                    print("   ⚔️ 卡牆反擊！揮刀一次清除可能的障礙物/隱形怪...")
                    p.press(p.attack_key)
                    time.sleep(0.5)
                
                # 反向跳躍脫困
                if current_target[0] > player_pos[0]:
                    print("   🔙 向左反向跳躍脫困...")
                    p.hold("LEFT")
                    time.sleep(0.1)
                    p.press(p.jump_key)
                    time.sleep(0.5)
                    p.release("LEFT")
                else:
                    print("   🔙 向右反向跳躍脫困...")
                    p.hold("RIGHT")
                    time.sleep(0.1)
                    p.press(p.jump_key)
                    time.sleep(0.5)
                    p.release("RIGHT")
                stuck_counter = 0
                continue

            # ---------------- [打怪與巡邏系統] ----------------
            # 鎖定單層平台 (預設鎖定畫面中間 150~550 高度的怪物，避免追上層或下層的怪卡牆)
            monster_info = g.find_closest_monster(y_range=(150, 550))

            # 嚴格邊界守衛：判斷追這隻怪會不會超出我們設定的 F5/F6 安全範圍
            valid_monster = None
            if monster_info:
                match_x, match_y, name, distance = monster_info
                
                if distance <= ATTACK_RANGE:
                    valid_monster = monster_info # 已經在攻擊範圍內，直接打
                else:
                    # 還沒進入攻擊範圍，判斷追擊方向是否會越界
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

            if valid_monster:
                match_x, match_y, name, distance = valid_monster
                print(f"🎯 追擊目標: {name} (距離: {distance:.1f})")
                
                if distance <= ATTACK_RANGE:
                    p.release_all() 
                    print("⚔️ 進入攻擊範圍，開砍！")
                    p.press(p.attack_key)
                    time.sleep(0.4) 
                    
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
                # 無怪時，乖乖在邊界內巡邏 (誤差縮小至 <= 3 像素才掉頭)
                if abs(player_pos[0] - current_target[0]) <= 3.0:
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
