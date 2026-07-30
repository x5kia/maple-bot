"""
【檔案說明】
此檔案定義了 Interception 驅動程式所使用的各種常數 (Constants)。
Interception 是一個能攔截並模擬「硬體層級」鍵鼠輸入的驅動程式，這也是為什麼這款外掛能繞過大部分防掛系統的原因。

⚠️ 【給同事的建議】：
除非你需要開發極度特殊的硬體控制功能，否則 **通常不需要修改此檔案**。
這裡就像是一本「字典」，讓主程式 (main.py) 和玩家控制 (player.py) 來查閱對應的硬體訊號代碼。
"""

from enum import Enum

class interception_key_state(Enum):
    """
    鍵盤按鍵的「狀態」代碼。
    在硬體層級，按下 (Down) 和彈起 (Up) 是兩個完全獨立的訊號。
    """
    INTERCEPTION_KEY_DOWN = 0x00 # 鍵盤按鍵被「按下」
    INTERCEPTION_KEY_UP = 0x01   # 鍵盤按鍵被「釋放/彈起」
    INTERCEPTION_KEY_E0 = 0x02   # 延伸按鍵標記 (例如：方向鍵、Insert、Delete 等通常帶有 E0 標記)
    INTERCEPTION_KEY_E1 = 0x04   # 另一種延伸按鍵標記 (較少見，如 Pause/Break 鍵)
    # 以下為遠端桌面服務 (Terminal Services) 相關的特殊訊號，外掛通常用不到
    INTERCEPTION_KEY_TERMSRV_SET_LED = 0x08
    INTERCEPTION_KEY_TERMSRV_SHADOW = 0x10
    INTERCEPTION_KEY_TERMSRV_VKPACKET = 0x20

class interception_filter_key_state(Enum):
    """
    鍵盤的「攔截過濾器」設定。
    用來告訴 Interception 驅動程式：「我想要監聽哪種鍵盤事件？」。
    例如在 main.py 中綁定鍵盤時，會用到 INTERCEPTION_FILTER_KEY_ALL 來捕捉你按下的任意鍵。
    """
    INTERCEPTION_FILTER_KEY_NONE = 0x0000 # 不攔截任何按鍵
    INTERCEPTION_FILTER_KEY_ALL = 0xFFFF  # 攔截所有按鍵事件 (最常用)
    
    # 以下是針對特定狀態的精細攔截 (透過位移運算符 << 1 轉換為過濾器格式)
    INTERCEPTION_FILTER_KEY_DOWN = interception_key_state.INTERCEPTION_KEY_UP.value
    INTERCEPTION_FILTER_KEY_UP = interception_key_state.INTERCEPTION_KEY_UP.value << 1
    INTERCEPTION_FILTER_KEY_E0 = interception_key_state.INTERCEPTION_KEY_E0.value << 1
    INTERCEPTION_FILTER_KEY_E1 = interception_key_state.INTERCEPTION_KEY_E1.value << 1
    INTERCEPTION_FILTER_KEY_TERMSRV_SET_LED = interception_key_state.INTERCEPTION_KEY_TERMSRV_SET_LED.value << 1
    INTERCEPTION_FILTER_KEY_TERMSRV_SHADOW = interception_key_state.INTERCEPTION_KEY_TERMSRV_SHADOW.value << 1
    INTERCEPTION_FILTER_KEY_TERMSRV_VKPACKET = interception_key_state.INTERCEPTION_KEY_TERMSRV_VKPACKET.value << 1

class interception_mouse_state(Enum):
    """
    滑鼠動作的「狀態」代碼。
    定義了滑鼠左中右鍵的按下與放開，以及滾輪事件。
    """
    INTERCEPTION_MOUSE_LEFT_BUTTON_DOWN = 0x001   # 左鍵按下
    INTERCEPTION_MOUSE_LEFT_BUTTON_UP = 0x002     # 左鍵放開
    INTERCEPTION_MOUSE_RIGHT_BUTTON_DOWN = 0x004  # 右鍵按下
    INTERCEPTION_MOUSE_RIGHT_BUTTON_UP = 0x008    # 右鍵放開
    INTERCEPTION_MOUSE_MIDDLE_BUTTON_DOWN = 0x010 # 中鍵(滾輪)按下
    INTERCEPTION_MOUSE_MIDDLE_BUTTON_UP = 0x020   # 中鍵(滾輪)放開

    # 為了相容性定義的別名 (Button 1=左鍵, Button 2=右鍵, Button 3=中鍵)
    INTERCEPTION_MOUSE_BUTTON_1_DOWN = INTERCEPTION_MOUSE_LEFT_BUTTON_DOWN
    INTERCEPTION_MOUSE_BUTTON_1_UP = INTERCEPTION_MOUSE_LEFT_BUTTON_UP
    INTERCEPTION_MOUSE_BUTTON_2_DOWN = INTERCEPTION_MOUSE_RIGHT_BUTTON_DOWN
    INTERCEPTION_MOUSE_BUTTON_2_UP = INTERCEPTION_MOUSE_RIGHT_BUTTON_UP
    INTERCEPTION_MOUSE_BUTTON_3_DOWN = INTERCEPTION_MOUSE_MIDDLE_BUTTON_DOWN
    INTERCEPTION_MOUSE_BUTTON_3_UP = INTERCEPTION_MOUSE_MIDDLE_BUTTON_UP

    # 側邊額外按鍵 (電競滑鼠常見的側鍵 4 和 5)
    INTERCEPTION_MOUSE_BUTTON_4_DOWN = 0x040
    INTERCEPTION_MOUSE_BUTTON_4_UP = 0x080
    INTERCEPTION_MOUSE_BUTTON_5_DOWN = 0x100
    INTERCEPTION_MOUSE_BUTTON_5_UP = 0x200

    # 滾輪滾動
    INTERCEPTION_MOUSE_WHEEL = 0x400  # 垂直滾動
    INTERCEPTION_MOUSE_HWHEEL = 0x800 # 水平滾動 (較少見)

class interception_filter_mouse_state(Enum):
    """
    滑鼠的「攔截過濾器」設定。
    告訴驅動程式你要監聽哪些滑鼠動作。
    """
    INTERCEPTION_FILTER_MOUSE_NONE = 0x0000 # 不攔截
    INTERCEPTION_FILTER_MOUSE_ALL = 0xFFFF  # 攔截所有滑鼠事件

    # 將 mouse_state 映射過來作為過濾條件
    INTERCEPTION_FILTER_MOUSE_LEFT_BUTTON_DOWN = interception_mouse_state.INTERCEPTION_MOUSE_LEFT_BUTTON_DOWN.value
    INTERCEPTION_FILTER_MOUSE_LEFT_BUTTON_UP = interception_mouse_state.INTERCEPTION_MOUSE_LEFT_BUTTON_UP.value
    INTERCEPTION_FILTER_MOUSE_RIGHT_BUTTON_DOWN = interception_mouse_state.INTERCEPTION_MOUSE_RIGHT_BUTTON_DOWN.value
    INTERCEPTION_FILTER_MOUSE_RIGHT_BUTTON_UP = interception_mouse_state.INTERCEPTION_MOUSE_RIGHT_BUTTON_UP.value
    INTERCEPTION_FILTER_MOUSE_MIDDLE_BUTTON_DOWN = interception_mouse_state.INTERCEPTION_MOUSE_MIDDLE_BUTTON_DOWN.value
    INTERCEPTION_FILTER_MOUSE_MIDDLE_BUTTON_UP = interception_mouse_state.INTERCEPTION_MOUSE_MIDDLE_BUTTON_UP.value

    INTERCEPTION_FILTER_MOUSE_BUTTON_1_DOWN = interception_mouse_state.INTERCEPTION_MOUSE_BUTTON_1_DOWN.value
    INTERCEPTION_FILTER_MOUSE_BUTTON_1_UP = interception_mouse_state.INTERCEPTION_MOUSE_BUTTON_1_UP.value
    INTERCEPTION_FILTER_MOUSE_BUTTON_2_DOWN = interception_mouse_state.INTERCEPTION_MOUSE_BUTTON_2_DOWN.value
    INTERCEPTION_FILTER_MOUSE_BUTTON_2_UP = interception_mouse_state.INTERCEPTION_MOUSE_BUTTON_2_UP.value
    INTERCEPTION_FILTER_MOUSE_BUTTON_3_DOWN = interception_mouse_state.INTERCEPTION_MOUSE_BUTTON_3_DOWN.value
    INTERCEPTION_FILTER_MOUSE_BUTTON_3_UP = interception_mouse_state.INTERCEPTION_MOUSE_BUTTON_3_UP.value

    INTERCEPTION_FILTER_MOUSE_BUTTON_4_DOWN = interception_mouse_state.INTERCEPTION_MOUSE_BUTTON_4_DOWN.value
    INTERCEPTION_FILTER_MOUSE_BUTTON_4_UP = interception_mouse_state.INTERCEPTION_MOUSE_BUTTON_4_UP.value
    INTERCEPTION_FILTER_MOUSE_BUTTON_5_DOWN = interception_mouse_state.INTERCEPTION_MOUSE_BUTTON_5_DOWN.value
    INTERCEPTION_FILTER_MOUSE_BUTTON_5_UP = interception_mouse_state.INTERCEPTION_MOUSE_BUTTON_5_UP.value

    INTERCEPTION_FILTER_MOUSE_WHEEL = interception_mouse_state.INTERCEPTION_MOUSE_WHEEL.value
    INTERCEPTION_FILTER_MOUSE_HWHEEL = interception_mouse_state.INTERCEPTION_MOUSE_HWHEEL.value
    
    # 監聽滑鼠游標「移動」事件
    INTERCEPTION_FILTER_MOUSE_MOVE = 0x1000

class interception_mouse_flag(Enum):
    """
    滑鼠的移動模式標記。
    這決定了我們在程式裡下達 (X, Y) 座標時，系統會怎麼解釋這個座標。
    """
    # 【相對移動】：類似 FPS 射擊遊戲的視角轉動。給 (10, 0) 代表滑鼠往右移動 10 像素。
    INTERCEPTION_MOUSE_MOVE_RELATIVE = 0x000 
    # 【絕對移動】：類似直接點擊螢幕某個確切位置。給 (100, 100) 代表游標直接瞬移到螢幕 (100, 100) 座標。
    # 楓之谷這類 2D 遊戲如果需要模擬滑鼠點擊，通常會使用這個絕對座標模式。
    INTERCEPTION_MOUSE_MOVE_ABSOLUTE = 0x001 
    
    # 其他進階系統屬性 (較少用)
    INTERCEPTION_MOUSE_VIRTUAL_DESKTOP = 0x002 # 映射到整個虛擬桌面(多螢幕)
    INTERCEPTION_MOUSE_ATTRIBUTES_CHANGED = 0x004
    INTERCEPTION_MOUSE_MOVE_NOCOALESCE = 0x008 # 禁用滑鼠軌跡合併(提高精準度)
    INTERCEPTION_MOUSE_TERMSRV_SRC_SHADOW = 0x100
