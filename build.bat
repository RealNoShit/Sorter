@echo off

echo Closing old app if running...
taskkill /IM "Downloads Sorter.exe" /F 2>nul

echo Cleaning old build...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del *.spec 2>nul

echo Building Downloads Sorter...
py -m PyInstaller --noconfirm --windowed --name "Downloads Sorter" main.py

echo.
echo Build complete!
pause