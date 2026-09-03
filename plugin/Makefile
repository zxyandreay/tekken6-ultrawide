TARGET = Tekken6.PPSSPP.UltrawideFix
OBJS = main.o safe_area.o

CFLAGS = -O2 -Os -G0 -Wall -Wextra -fno-pic
LDFLAGS = -nostartfiles

BUILD_PRX = 1
PRX_EXPORTS = exports.exp

PSPSDK = $(shell psp-config --pspsdk-path)
include $(PSPSDK)/lib/build.mak
