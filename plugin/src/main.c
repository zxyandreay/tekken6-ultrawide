#include <pspiofilemgr.h>
#include <pspkernel.h>
#include <pspthreadman.h>
#include <psputils.h>

#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "aspect_math.h"

PSP_MODULE_INFO("Tekken6Ultrawide", 0, 1, 1);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

#define PPSSPP_EMULATOR_DEVICE "emulator:"
#define PPSSPP_DEVCTL_IS_EMULATOR 3
#define PPSSPP_DEVCTL_GET_ASPECT_RATIO 0x31
#define PPSSPP_DEVCTL_SEND_OUTPUT 2
#define INIT_ATTEMPTS 600
#define INIT_DELAY_US 10000

#define STOCK_LUI 0x3c013fe3u
#define STOCK_ORI 0x34218e39u

static const uint32_t kAspectAddresses[][2] = {
    {0x08945f10u, 0x08945f14u},
    {0x08946794u, 0x08946798u},
    {0x08946bc8u, 0x08946bccu},
    {0x08947d90u, 0x08947d94u},
};

#define ASPECT_PAIR_COUNT (sizeof(kAspectAddresses) / sizeof(kAspectAddresses[0]))

static uint32_t read32(uint32_t address) {
    return *(volatile const uint32_t *)(uintptr_t)address;
}

static void write32(uint32_t address, uint32_t value) {
    *(volatile uint32_t *)(uintptr_t)address = value;
}

static void send_log(const char *message) {
    if (message == NULL) {
        return;
    }
    sceIoDevctl(PPSSPP_EMULATOR_DEVICE,
                PPSSPP_DEVCTL_SEND_OUTPUT,
                (void *)message,
                (int)strlen(message),
                NULL,
                0);
}

static int query_ppsspp_aspect(float *aspect) {
    int result;
    if (aspect == NULL) {
        return 0;
    }

    result = sceIoDevctl(PPSSPP_EMULATOR_DEVICE,
                         PPSSPP_DEVCTL_IS_EMULATOR,
                         NULL,
                         0,
                         NULL,
                         0);
    if (result != 0) {
        send_log("Tekken6 Ultrawide: PPSSPP emulator API unavailable; no patch applied.\n");
        return 0;
    }

    *aspect = 0.0f;
    result = sceIoDevctl(PPSSPP_EMULATOR_DEVICE,
                         PPSSPP_DEVCTL_GET_ASPECT_RATIO,
                         NULL,
                         0,
                         aspect,
                         sizeof(*aspect));
    if (result < 0 || !tekken6_aspect_is_valid(*aspect)) {
        send_log("Tekken6 Ultrawide: PPSSPP returned no valid landscape aspect; no patch applied.\n");
        return 0;
    }
    return 1;
}

static int executable_ready(void) {
    unsigned int index;
    for (index = 0; index < ASPECT_PAIR_COUNT; ++index) {
        if (read32(kAspectAddresses[index][0]) == 0u
            || read32(kAspectAddresses[index][1]) == 0u) {
            return 0;
        }
    }
    return 1;
}

static int state_is_safe(uint32_t target_lui, uint32_t target_ori) {
    unsigned int index;
    for (index = 0; index < ASPECT_PAIR_COUNT; ++index) {
        uint32_t current_lui = read32(kAspectAddresses[index][0]);
        uint32_t current_ori = read32(kAspectAddresses[index][1]);
        int is_stock = current_lui == STOCK_LUI && current_ori == STOCK_ORI;
        int is_target = current_lui == target_lui && current_ori == target_ori;
        if (!is_stock && !is_target) {
            return 0;
        }
    }
    return 1;
}

static void invalidate_patch_ranges(void) {
    unsigned int index;
    sceKernelDcacheWritebackInvalidateAll();
    for (index = 0; index < ASPECT_PAIR_COUNT; ++index) {
        sceKernelIcacheInvalidateRange((const void *)(uintptr_t)kAspectAddresses[index][0], 8u);
    }
}

static void apply_aspect(uint32_t target_lui, uint32_t target_ori) {
    unsigned int index;
    for (index = 0; index < ASPECT_PAIR_COUNT; ++index) {
        write32(kAspectAddresses[index][0], target_lui);
        write32(kAspectAddresses[index][1], target_ori);
    }
    invalidate_patch_ranges();
}

static int verify_aspect(uint32_t target_lui, uint32_t target_ori) {
    unsigned int index;
    for (index = 0; index < ASPECT_PAIR_COUNT; ++index) {
        if (read32(kAspectAddresses[index][0]) != target_lui
            || read32(kAspectAddresses[index][1]) != target_ori) {
            return 0;
        }
    }
    return 1;
}

int module_start(SceSize args, void *argp) {
    float aspect;
    uint32_t target_lui;
    uint32_t target_ori;
    char message[128];
    unsigned int attempt;

    (void)args;
    (void)argp;

    if (!query_ppsspp_aspect(&aspect)) {
        return 0;
    }

    for (attempt = 0; attempt < INIT_ATTEMPTS && !executable_ready(); ++attempt) {
        sceKernelDelayThread(INIT_DELAY_US);
    }
    if (!executable_ready()) {
        send_log("Tekken6 Ultrawide: executable load timeout; no patch applied.\n");
        return 0;
    }
    if (!tekken6_build_aspect_words(aspect, &target_lui, &target_ori)) {
        send_log("Tekken6 Ultrawide: aspect conversion failed; no patch applied.\n");
        return 0;
    }

    snprintf(message, sizeof(message),
             "Tekken6 Ultrawide v1.1.0-dev: display aspect %.6f -> %08lx/%08lx\n",
             (double)aspect,
             (unsigned long)target_lui,
             (unsigned long)target_ori);
    send_log(message);

    if (!state_is_safe(target_lui, target_ori)) {
        send_log("Tekken6 Ultrawide: projection signature mismatch (disable aspect CWCheats); no patch applied.\n");
        return 0;
    }

    apply_aspect(target_lui, target_ori);
    if (!verify_aspect(target_lui, target_ori)) {
        send_log("Tekken6 Ultrawide: verification failed after patch.\n");
        return 0;
    }

    send_log("Tekken6 Ultrawide: automatic projection aspect applied successfully.\n");
    return 0;
}

int module_stop(SceSize args, void *argp) {
    (void)args;
    (void)argp;
    return 0;
}
