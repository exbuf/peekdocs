#!/bin/bash
# build_firmware.sh -- Cross-compile firmware for ARM Cortex-M4 target
# PEEKDOCS_TEST_MARKER

set -euo pipefail

TOOLCHAIN="arm-none-eabi"
BUILD_DIR="build/firmware"
SRC_DIR="src"
TARGET_MCU="STM32F407VG"
OPTIMIZATION="-Os"

echo "=== Firmware Build Script for ${TARGET_MCU} ==="

# Clean previous build
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

# Compile all C sources
for src in "${SRC_DIR}"/*.c; do
    obj="${BUILD_DIR}/$(basename "${src}" .c).o"
    echo "Compiling: ${src} -> ${obj}"
    ${TOOLCHAIN}-gcc ${OPTIMIZATION} -mcpu=cortex-m4 -mthumb \
        -DTARGET_MCU=${TARGET_MCU} \
        -I include/ -c "${src}" -o "${obj}"
done

# Link
echo "Linking firmware..."
${TOOLCHAIN}-ld -T linker_script.ld -o "${BUILD_DIR}/firmware.elf" "${BUILD_DIR}"/*.o

# Generate binary and hex
${TOOLCHAIN}-objcopy -O binary "${BUILD_DIR}/firmware.elf" "${BUILD_DIR}/firmware.bin"
${TOOLCHAIN}-objcopy -O ihex "${BUILD_DIR}/firmware.elf" "${BUILD_DIR}/firmware.hex"

echo "Build complete. Binary size: $(wc -c < "${BUILD_DIR}/firmware.bin") bytes"
