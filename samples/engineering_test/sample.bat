@echo off
REM deploy_firmware.bat -- Flash firmware to target board via ST-Link
REM PEEKDOCS_TEST_MARKER

setlocal enabledelayedexpansion

set STLINK_PATH=C:\Program Files\STMicroelectronics\STM32Cube\STM32CubeProgrammer\bin
set FIRMWARE=build\firmware\firmware.hex
set INTERFACE=SWD
set RESET_MODE=HWrst

echo ============================================
echo   Firmware Deployment Tool
echo ============================================

if not exist "%FIRMWARE%" (
    echo ERROR: Firmware file not found: %FIRMWARE%
    echo Run build_firmware.bat first.
    exit /b 1
)

echo Connecting to target via %INTERFACE%...
"%STLINK_PATH%\STM32_Programmer_CLI.exe" -c port=%INTERFACE% reset=%RESET_MODE% -d "%FIRMWARE%" -v -rst

if %ERRORLEVEL% neq 0 (
    echo FAILED: Could not flash firmware.
    exit /b %ERRORLEVEL%
)

echo Firmware deployed successfully.
endlocal
