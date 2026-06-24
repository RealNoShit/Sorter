@echo off

echo Closing apps...
taskkill /F /IM "Downloads Sorter.exe" 2>nul
taskkill /F /IM "Downloads Sorter Dev.exe" 2>nul

echo Building...
py -m PyInstaller --noconfirm --windowed --name "Downloads Sorter Dev" main.py

echo.
echo Done.
pause