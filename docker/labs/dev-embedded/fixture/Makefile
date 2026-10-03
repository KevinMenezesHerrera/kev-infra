OUT ?= build
SRC ?= .
CC = arm-none-eabi-gcc
FLAGS = -mcpu=cortex-m3 -mthumb -g -O0 -ffreestanding -Wall -Wextra -Werror
.PHONY: all
all: $(OUT)/firmware.elf $(OUT)/firmware.bin $(OUT)/firmware.hex
$(OUT):
	mkdir -p $@
$(OUT)/main.o: $(SRC)/main.c | $(OUT)
	$(CC) $(FLAGS) -c $< -o $@
$(OUT)/startup.o: $(SRC)/startup.S | $(OUT)
	$(CC) $(FLAGS) -c $< -o $@
$(OUT)/firmware.elf: $(OUT)/main.o $(OUT)/startup.o $(SRC)/linker.ld
	$(CC) $(FLAGS) -nostdlib -Wl,-T,$(SRC)/linker.ld,-Map,$(OUT)/firmware.map $(OUT)/main.o $(OUT)/startup.o -o $@
$(OUT)/firmware.bin: $(OUT)/firmware.elf
	arm-none-eabi-objcopy -O binary $< $@
$(OUT)/firmware.hex: $(OUT)/firmware.elf
	arm-none-eabi-objcopy -O ihex $< $@
