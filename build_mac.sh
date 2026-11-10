#!/bin/bash
# Gera dist/Diagnostico.app (rodar no Mac, com Python 3.10+ instalado)
set -e
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt pyinstaller
python3 -m PyInstaller --windowed --name Diagnostico run_gui.py
echo
echo "Pronto! O app esta em: dist/Diagnostico.app"
