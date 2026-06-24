@echo off

echo Cleaning old build...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

echo Building Downloads Sorter...
py -m PyInstaller --windowed --name "Downloads Sorter" main.py

echo.
echo Build complete!
pause