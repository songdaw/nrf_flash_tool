@echo off

pip install pyinstaller
pyinstaller --clean -w -F .\flash_gui.py

echo make success

::end