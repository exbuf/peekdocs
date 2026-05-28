# sample.makefile -- Build system for embedded firmware project
# PEEKDOCS_TEST_MARKER

CC       = arm-none-eabi-gcc
LD       = arm-none-eabi-ld
OBJCOPY  = arm-none-eabi-objcopy
SIZE     = arm-none-eabi-size

TARGET   = firmware
SRC_DIR  = src
INC_DIR  = include
BUILD    = build

CFLAGS   = -mcpu=cortex-m4 -mthumb -Os -Wall -Wextra
CFLAGS  += -I$(INC_DIR) -DUSE_HAL_DRIVER
LDFLAGS  = -T stm32f407.ld -nostdlib

SRCS     = $(wildcard $(SRC_DIR)/*.c)
OBJS     = $(patsubst $(SRC_DIR)/%.c, $(BUILD)/%.o, $(SRCS))

.PHONY: all clean flash size

all: $(BUILD)/$(TARGET).bin

$(BUILD)/%.o: $(SRC_DIR)/%.c | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/$(TARGET).elf: $(OBJS)
	$(LD) $(LDFLAGS) -o $@ $^

$(BUILD)/$(TARGET).bin: $(BUILD)/$(TARGET).elf
	$(OBJCOPY) -O binary $< $@

$(BUILD):
	mkdir -p $(BUILD)

size: $(BUILD)/$(TARGET).elf
	$(SIZE) $<

flash: $(BUILD)/$(TARGET).bin
	st-flash write $< 0x08000000

clean:
	rm -rf $(BUILD)
