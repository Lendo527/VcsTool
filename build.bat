@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === 安装依赖 ===
pip install -r requirements.txt

echo === 打包（单文件 exe）===
pyinstaller --noconfirm --onefile --windowed ^
  --name "VcsHelper" ^
  --icon "icon.ico" ^
  --add-data "icon.ico;." ^
  main.py

echo.
echo === 完成 ===
echo 输出文件: dist\VcsHelper.exe
pause
