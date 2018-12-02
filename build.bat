@echo off
py -m PyInstaller --upx-dir=upx/ main.spec
del dist\Brink\vcruntime140.dll
copy %WINDIR%\System32\vcruntime140.dll dist\Brink
