"""
【檔案說明】
此檔案是 MapleBot 與底層 `interception.dll` 及系統驅動程式溝通的「橋樑」。
它使用了 Python 的 `ctypes` 模組，直接呼叫 Windows 的核心 API (kernel32.dll)。
透過這種方式，外掛發出的鍵盤/滑鼠訊號會被系統認為是「真正的硬體」發出的，藉此繞過遊戲防護。

⚠️ 【給同事的建議】：
此檔案涉及複雜的記憶體操作與 Windows I/O 控制指令 (DeviceIoControl)。
除非你需要優化底層效能或修復驅動層級的 Bug，否則 **強烈建議不要修改此檔案的任何邏輯**。
如果在執行時發生錯誤，通常是因為沒有以系統管理員身分執行，或是尚未安裝 Interception 驅動程式。
"""

from ctypes import *
from interception.stroke import *

# 定義最大支援的硬體裝置數量
MAX_DEVICES = 20
MAX_KEYBOARD = 10
MAX_MOUSE = 10

# 載入 Windows 核心 API
k32 = windll.LoadLibrary('kernel32')


class interception():
    """
    Interception 驅動程式的主要管理器。
    負責初始化所有鍵盤和滑鼠裝置的連線，並提供等待 (wait) 和發送 (send) 訊號的介面。
    """
    _context = []
    k32 = None
    _c_events = (c_void_p * MAX_DEVICES)()

    def __init__(self):
        try:
            # 嘗試連接系統中所有可能的 Interception 虛擬裝置 (通常是 /dev/interception00 ~ 19)
            for i in range(MAX_DEVICES):
                _device = device(k32.CreateFileA(b'\\\\.\\interception%02d' % i,
                                                 0x80000000, 0, 0, 3, 0, 0),
                                 k32.CreateEventA(0, 1, 0, 0),
                                 interception.is_keyboard(i))
                self._context.append(_device)
                self._c_events[i] = _device.event

        except Exception as e:
            # 如果初始化失敗，清理已建立的連線並拋出錯誤
            self._destroy_context()
            raise e

    def wait(self, milliseconds=-1):
        """
        等待並捕捉硬體訊號。
        在 main.py 的 bind 階段，程式會呼叫這個函式來「聽」你按下了哪個真實鍵盤按鍵，
        藉此鎖定要將偽造的訊號發送到哪一個裝置 ID。
        """
        result = k32.WaitForMultipleObjects(MAX_DEVICES, self._c_events, 0, milliseconds)
        if result == -1 or result == 0x102:
            return 0
        else:
            return result

    def set_filter(self, predicate, filter):
        """設定裝置的過濾器，決定要攔截哪些種類的按鍵/滑鼠事件。"""
        for i in range(MAX_DEVICES):
            if predicate(i):
                result = self._context[i].set_filter(filter)

    def get_HWID(self, device: int):
        """取得指定裝置的硬體識別碼 (Hardware ID)。"""
        if not interception.is_invalid(device):
            try:
                return self._context[device].get_HWID().decode("utf-16")
            except:
                pass
        return ""

    def receive(self, device: int):
        """從指定的裝置接收一個按鍵或滑鼠動作。"""
        if not interception.is_invalid(device):
            return self._context[device].receive()

    def send(self, device: int, stroke: stroke):
        """
        【最核心的函式】：將偽造的按鍵 (stroke) 發送到指定的裝置 (device)。
        當在 player.py 呼叫 p.press() 時，最終都會流向這裡。
        """
        if not interception.is_invalid(device):
            self._context[device].send(stroke)

    # 以下為判斷裝置類型的靜態方法
    @staticmethod
    def is_keyboard(device):
        return device + 1 > 0 and device + 1 <= MAX_KEYBOARD

    @staticmethod
    def is_mouse(device):
        return device + 1 > MAX_KEYBOARD and device + 1 <= MAX_KEYBOARD + MAX_MOUSE

    @staticmethod
    def is_invalid(device):
        return device + 1 <= 0 or device + 1 > (MAX_KEYBOARD + MAX_MOUSE)

    def _destroy_context(self):
        """關閉並銷毀所有與裝置的連線。"""
        for device in self._context:
            device.destroy()


class device_io_result:
    """封裝 Windows DeviceIoControl 呼叫的回傳結果與數據。"""
    result = 0
    data = None
    data_bytes = None

    def __init__(self, result, data):
        self.result = result
        if data != None:
            self.data = list(data)
            self.data_bytes = bytes(data)


def device_io_call(decorated):
    """
    這是一個 Python 裝飾器 (Decorator)。
    用來簡化 device 類別中呼叫底層 DeviceIoControl 的繁瑣語法。
    """
    def decorator(device, *args, **kwargs):
        command, inbuffer, outbuffer = decorated(device, *args, **kwargs)
        return device._device_io_control(command, inbuffer, outbuffer)

    return decorator


class device():
    """
    代表一個單一的硬體裝置 (一個鍵盤或一個滑鼠)。
    負責處理具體的記憶體拷貝與 I/O 控制指令。
    """
    handle = 0
    event = 0
    is_keyboard = False
    _parser = None
    # ctypes 需要的 C 語言型別變數
    _bytes_returned = (c_int * 1)(0)
    _c_byte_500 = (c_byte * 500)()
    _c_int_2 = (c_int * 2)()
    _c_ushort_1 = (c_ushort * 1)()
    _c_int_1 = (c_int * 1)()
    _c_recv_buffer = None

    def __init__(self, handle, event, is_keyboard: bool):
        self.is_keyboard = is_keyboard
        # 鍵盤封包大小為 12 bytes，滑鼠為 24 bytes
        if is_keyboard:
            self._c_recv_buffer = (c_byte * 12)()
            self._parser = key_stroke
        else:
            self._c_recv_buffer = (c_byte * 24)()
            self._parser = mouse_stroke

        if handle == -1 or event == 0:
            raise Exception("Can't create device (無法建立裝置連線，請確認驅動是否安裝或權限不足)")
        self.handle = handle
        self.event = event

        if self._device_set_event().result == 0:
            raise Exception("Can't communicate with driver (無法與驅動程式通訊)")

    def destroy(self):
        """關閉裝置的控制代碼 (Handle)。"""
        if self.handle != -1:
            k32.CloseHandle(self.handle)
        if self.event != 0:
            k32.CloseHandle(self.event)

    # 以下包含諸多 0x222XXX 的魔術數字，這些是 Windows Driver 內部定義的 IOCTL (I/O 控制碼)
    # 用來指示驅動程式執行特定的動作 (例如：設定過濾器、發送按鍵等)

    @device_io_call
    def get_precedence(self):
        return 0x222008, 0, self._c_int_1

    @device_io_call
    def set_precedence(self, precedence: int):
        self._c_int_1[0] = precedence
        return 0x222004, self._c_int_1, 0

    @device_io_call
    def get_filter(self):
        return 0x222020, 0, self._c_ushort_1

    @device_io_call
    def set_filter(self, filter):
        self._c_ushort_1[0] = filter
        return 0x222010, self._c_ushort_1, 0

    @device_io_call
    def _get_HWID(self):
        return 0x222200, 0, self._c_byte_500

    def get_HWID(self):
        data = self._get_HWID().data_bytes
        return data[:self._bytes_returned[0]]

    @device_io_call
    def _receive(self):
        return 0x222100, 0, self._c_recv_buffer

    def receive(self):
        data = self._receive().data_bytes
        return self._parser.parse_raw(data)

    def send(self, stroke: stroke):
        if type(stroke) == self._parser:
            self._send(stroke)

    @device_io_call
    def _send(self, stroke: stroke):
        """
        將組裝好的按鍵資料 (stroke) 複製到記憶體緩衝區 (memmove)，
        並透過 IOCTL 0x222080 指令交由驅動程式發送出去。
        """
        memmove(self._c_recv_buffer, stroke.data_raw, len(self._c_recv_buffer))
        return 0x222080, self._c_recv_buffer, 0

    @device_io_call
    def _device_set_event(self):
        self._c_int_2[0] = self.event
        return 0x222040, self._c_int_2, 0

    def _device_io_control(self, command, inbuffer, outbuffer) -> device_io_result:
        """
        呼叫 Windows 核心 API `DeviceIoControl`。
        這是所有硬體溝通的最終出口點。
        """
        res = k32.DeviceIoControl(self.handle, command, inbuffer,
                                  len(bytes(inbuffer)) if inbuffer != 0 else 0,
                                  outbuffer,
                                  len(bytes(outbuffer)) if outbuffer != 0 else 0,
                                  self._bytes_returned, 0)

        return device_io_result(res, outbuffer if outbuffer != 0 else None)
