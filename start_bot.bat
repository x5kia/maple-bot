@echo off
:: 【關鍵修復】強制將工作目錄切換到這個 bat 檔所在的資料夾
cd /d "%~dp0"

:: 設定終端機顯示 UTF-8 中文，避免亂碼
chcp 65001 >nul
title 🚀 MapleBot (經典版) 啟動器

echo ===================================================
echo             MapleBot (經典版) 快速啟動程式
echo ===================================================
echo.

:: 檢查是否具有系統管理員權限
net session >nul 2>&1
if %errorLevel% neq 0 (
echo [⚠️] 權限檢查：尚未取得系統管理員權限。
echo 正在嘗試自動要求權限，請在彈出的視窗中點選「是」...

:: 使用 VBS 腳本來要求權限 (比 PowerShell 更穩定，不閃退)
echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
echo UAC.ShellExecute "cmd.exe", "/c ""%~s0""", "", "runas", 1 >> "%temp%\getadmin.vbs"
"%temp%\getadmin.vbs"
del "%temp%\getadmin.vbs"

:: 關閉原本沒有權限的舊視窗
exit /B


)

echo [✅] 權限檢查：已取得系統管理員權限！
echo.
echo [⏳] 正在檢查 Python 環境...
python --version >nul 2>&1
if %errorLevel% NEQ 0 (
echo [❌] 嚴重錯誤：找不到 Python！
echo 請確認這台電腦是否已安裝 Python 3，並且在安裝時有勾選「Add Python to PATH」。
echo.
pause
exit /B
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
echo 程式已中斷。
echo 如果上方出現 Exception 錯誤，請往上捲動查看紅字。
echo ===================================================
pause
