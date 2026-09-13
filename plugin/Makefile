TARGET = Tekken6Ultrawide
OBJS = src/main.o src/aspect_math.o exports.o

CFLAGS = -O2 -G0 -std=c11 -Wall -Wextra -Werror
ASFLAGS = $(CFLAGS)

PSPSDK := $(shell psp-config --pspsdk-path)
include $(PSPSDK)/lib/build_prx.mak
