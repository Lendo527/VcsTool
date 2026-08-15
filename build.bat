@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === 安装依赖 ===
pip install -r requirements.txt
pip install pyinstaller

echo === 打包（单文件 exe）===
pyinstaller --noconfirm --onefile --windowed ^
  --name "VCSTool" ^
  --icon "icon.ico" ^
  --add-data "icon.ico;." ^
  --collect-all keyboard ^
  main.py

echo.
echo === 完成 ===
echo 输出文件: dist\VCSTool.exe
pause
