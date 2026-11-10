@echo off
REM Gera dist\Diagnostico.exe (rodar no Windows, com Python 3.10+ instalado)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --onefile --windowed --name Diagnostico run_gui.py
echo.
echo Pronto! O executavel esta em: dist\Diagnostico.exe
pause
