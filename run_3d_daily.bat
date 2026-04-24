@echo off
chcp 65001 >nul
cd /d C:\Users\maxin
echo === 开始更新福彩3D数据 === %date% %time%
python C:\Users\maxin\fetch_3d_lottery.py
echo === 数据分析 ===
python C:\Users\maxin\analyze_3d_advanced.py
echo === 完成 === %date% %time%
pause
