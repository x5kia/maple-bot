@echo off
:: 設定終端機顯示 UTF-8 中文，避免亂碼
chcp 65001 >nul
title 🚀 MapleBot (經典版) 啟動器

echo ===================================================
echo             MapleBot (經典版) 快速啟動程式
echo ===================================================
echo.

:: 檢查是否具有系統管理員權限
net session >nul 2>&1
if %errorLevel% == 0 (
echo [✅] 權限檢查：已取得系統管理員權限！
) else (
echo [⚠️] 權限檢查：尚未取得系統管理員權限。
echo 正在嘗試自動要求權限，請在彈出的視窗中點選「是」...
:: 呼叫 PowerShell 重新以管理員身分啟動自己
powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
exit
)

echo.
echo [⏳] 正在檢查 Python 環境...
python --version >nul 2>&1
if %errorLevel% NEQ 0 (
echo [❌] 嚴重錯誤：找不到 Python！
echo 請確認這台電腦是否已安裝 Python 3，並且在安裝時有勾選「Add Python to PATH」。
echo.
pause
exit
)
echo [✅] Python 檢查通過。

echo.
echo ===================================================
echo 準備啟動主程式...
echo 啟動後，請注意終端機的提示，並隨便按一個鍵盤按鍵來綁定。
echo ===================================================
echo.

:: 執行主程式
python main.py

echo.
echo ===================================================
echo 程式已中斷或發生錯誤。請查看上方的錯誤訊息。
echo ===================================================
pause
