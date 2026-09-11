@echo off
setlocal
set "GAEA_UE58_ENGINE=%~1"
if not defined GAEA_UE58_ENGINE set "GAEA_UE58_ENGINE=C:\Program Files\Epic Games\UE_5.8"
py -3 "%~dp0package_plugin.py" --engine "%GAEA_UE58_ENGINE%"
set "GAEA_BUILD_RESULT=%ERRORLEVEL%"
if not "%GAEA_BUILD_RESULT%"=="0" echo Build failed. Requires Python 3, UE 5.8 and the UE C++ toolchain. See docs\UE-5.8.md.
pause
exit /b %GAEA_BUILD_RESULT%
