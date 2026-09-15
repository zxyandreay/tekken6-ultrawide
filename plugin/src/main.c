#include <pspiofilemgr.h>
#include <pspkernel.h>
#include <pspthreadman.h>
#include <psputils.h>

#include <stdint.h>

#include "aspect_math.h"
#include "hud_hook.h"

PSP_MODULE_INFO("Tekken6Ultrawide", 0, 1, 1);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

#define PPSSPP_EMULATOR_DEVICE "emulator:"
#define PPSSPP_DEVCTL_IS_EMULATOR 3
#define PPSSPP_DEVCTL_GET_ASPECT_RATIO 0x31

#define INIT_ATTEMPTS 1200
#define INIT_DELAY_US 5000

#define STOCK_LUI 0x3c013fe3u
#define STOCK_ORI 0x34218e39u

static const uint32_t kAspectAddresses[][2] = {
    {0x08945f10u, 0x08945f14u},
    {0x08946794u, 0x08946798u},
    {0x08946bc8u, 0x08946bccu},
    {0x08947d90u, 0x08947d94u},
};

typedef struct {
    uint32_t address;
    uint32_t original;
    int link;
} HudHookSite;

/* Every slot-creation route is wrapped, including the three tail-call routes. */
static const HudHookSite kHudSlotBuilderSites[] = {
    {0x08929854u, 0x0E24B67Eu, 1},
    {0x08929958u, 0x0E24B67Eu, 1},
    {0x089299E8u, 0x0E24B67Eu, 1},
    {0x08929DF0u, 0x0E24B67Eu, 1},
    {0x08929F3Cu, 0x0E24B67Eu, 1},
    {0x0892A10Cu, 0x0E24B67Eu, 1},
    {0x0892A170u, 0x0E24B67Eu, 1},
    {0x0892A1B4u, 0x0E24B67Eu, 1},
    {0x0892A1F0u, 0x0E24B67Eu, 1},
    {0x0892A268u, 0x0E24B67Eu, 1},
    {0x08929228u, 0x0A24B67Eu, 0},
    {0x089292F4u, 0x0A24B67Eu, 0},
    {0x08929D4Cu, 0x0A24B67Eu, 0},
};

static const HudHookSite kHudRectBuilderSites[] = {
    {0x08AB9798u, 0x0E2AE4E0u, 1},
    {0x08AB98ACu, 0x0E2AE4E0u, 1},
};

/* The two proven CGaugeTcb_t layer submissions, before the shared sprite path. */
static const HudHookSite kHudGaugeDrawSites[] = {
    {0x0892C1F0u, 0x0E24A3FDu, 1},
    {0x0892C26Cu, 0x0A24A3FDu, 0},
};

static const HudHookSite kHudSideStripSites[] = {
    {0x0892D56Cu, 0x0E2097ABu, 1},
    {0x0892D5B0u, 0x0E2097ABu, 1},
};

/* Case-4 0x80019E converter call. Device A/B testing proved the narrow
 * source-vertex predicate in tekken6_hud_winner_glow_hook owns the residual
 * winner-orb glow on both sides. */
static const HudHookSite kHudWinnerGlowSites[] = {
    {0x08AC9C38u, 0x0E2BA529u, 1},
};

#define ASPECT_PAIR_COUNT (sizeof(kAspectAddresses) / sizeof(kAspectAddresses[0]))

static uint32_t read32(uint32_t address) {
    return *(volatile const uint32_t *)(uintptr_t)address;
}

static void write32(uint32_t address, uint32_t value);

static uint32_t make_jump_word(uint32_t target, int link) {
    return (link ? 0x0C000000u : 0x08000000u) | ((target >> 2) & 0x03FFFFFFu);
}

static int jump_target_is_reachable(uint32_t site, uint32_t target) {
    return (site & 0xF0000000u) == (target & 0xF0000000u);
}

static int hud_hooks_are_safe(uint32_t slot_hook, uint32_t rect_hook, uint32_t gauge_hook,
                              uint32_t side_strip_hook, uint32_t winner_glow_hook) {
    unsigned int index;

    if (!jump_target_is_reachable(kHudSlotBuilderSites[0].address, slot_hook)
        || !jump_target_is_reachable(kHudRectBuilderSites[0].address, rect_hook)
        || !jump_target_is_reachable(kHudGaugeDrawSites[0].address, gauge_hook)
        || !jump_target_is_reachable(kHudSideStripSites[0].address, side_strip_hook)
        || !jump_target_is_reachable(kHudWinnerGlowSites[0].address, winner_glow_hook)) {
        return 0;
    }

    for (index = 0; index < sizeof(kHudSlotBuilderSites) / sizeof(kHudSlotBuilderSites[0]); ++index) {
        uint32_t current = read32(kHudSlotBuilderSites[index].address);
        uint32_t replacement = make_jump_word(slot_hook, kHudSlotBuilderSites[index].link);
        if (current != kHudSlotBuilderSites[index].original && current != replacement) {
            return 0;
        }
    }

    for (index = 0; index < sizeof(kHudRectBuilderSites) / sizeof(kHudRectBuilderSites[0]); ++index) {
        uint32_t current = read32(kHudRectBuilderSites[index].address);
        uint32_t replacement = make_jump_word(rect_hook, kHudRectBuilderSites[index].link);
        if (current != kHudRectBuilderSites[index].original && current != replacement) {
            return 0;
        }
    }

    for (index = 0; index < sizeof(kHudGaugeDrawSites) / sizeof(kHudGaugeDrawSites[0]); ++index) {
        uint32_t current = read32(kHudGaugeDrawSites[index].address);
        uint32_t replacement = make_jump_word(gauge_hook, kHudGaugeDrawSites[index].link);
        if (current != kHudGaugeDrawSites[index].original && current != replacement) {
            return 0;
        }
    }

    for (index = 0; index < sizeof(kHudSideStripSites) / sizeof(kHudSideStripSites[0]); ++index) {
        uint32_t current = read32(kHudSideStripSites[index].address);
        uint32_t replacement = make_jump_word(side_strip_hook, kHudSideStripSites[index].link);
        if (current != kHudSideStripSites[index].original && current != replacement) {
            return 0;
        }
    }

    for (index = 0; index < sizeof(kHudWinnerGlowSites) / sizeof(kHudWinnerGlowSites[0]); ++index) {
        uint32_t current = read32(kHudWinnerGlowSites[index].address);
        uint32_t replacement = make_jump_word(winner_glow_hook, kHudWinnerGlowSites[index].link);
        if (current != kHudWinnerGlowSites[index].original && current != replacement) {
            return 0;
        }
    }

    return 1;
}

static void apply_hud_hooks(void) {
    unsigned int index;
    uint32_t slot_hook = (uint32_t)(uintptr_t)&tekken6_hud_slot_builder_wrapper;
    uint32_t rect_hook = (uint32_t)(uintptr_t)&tekken6_hud_rect_hook;
    uint32_t gauge_hook = (uint32_t)(uintptr_t)&tekken6_hud_gauge_draw_hook;
    uint32_t side_strip_hook = (uint32_t)(uintptr_t)&tekken6_hud_side_strip_hook;
    uint32_t winner_glow_hook = (uint32_t)(uintptr_t)&tekken6_hud_winner_glow_hook;

    for (index = 0; index < sizeof(kHudSlotBuilderSites) / sizeof(kHudSlotBuilderSites[0]); ++index) {
        write32(kHudSlotBuilderSites[index].address,
                make_jump_word(slot_hook, kHudSlotBuilderSites[index].link));
    }
    for (index = 0; index < sizeof(kHudRectBuilderSites) / sizeof(kHudRectBuilderSites[0]); ++index) {
        write32(kHudRectBuilderSites[index].address,
                make_jump_word(rect_hook, kHudRectBuilderSites[index].link));
    }
    for (index = 0; index < sizeof(kHudGaugeDrawSites) / sizeof(kHudGaugeDrawSites[0]); ++index) {
        write32(kHudGaugeDrawSites[index].address,
                make_jump_word(gauge_hook, kHudGaugeDrawSites[index].link));
    }
    for (index = 0; index < sizeof(kHudSideStripSites) / sizeof(kHudSideStripSites[0]); ++index) {
        write32(kHudSideStripSites[index].address,
                make_jump_word(side_strip_hook, kHudSideStripSites[index].link));
    }
    for (index = 0; index < sizeof(kHudWinnerGlowSites) / sizeof(kHudWinnerGlowSites[0]); ++index) {
        write32(kHudWinnerGlowSites[index].address,
                make_jump_word(winner_glow_hook, kHudWinnerGlowSites[index].link));
    }

    sceKernelDcacheWritebackInvalidateAll();
    for (index = 0; index < sizeof(kHudSlotBuilderSites) / sizeof(kHudSlotBuilderSites[0]); ++index) {
        sceKernelIcacheInvalidateRange((const void *)(uintptr_t)kHudSlotBuilderSites[index].address, 4u);
    }
    for (index = 0; index < sizeof(kHudRectBuilderSites) / sizeof(kHudRectBuilderSites[0]); ++index) {
        sceKernelIcacheInvalidateRange((const void *)(uintptr_t)kHudRectBuilderSites[index].address, 4u);
    }
    for (index = 0; index < sizeof(kHudGaugeDrawSites) / sizeof(kHudGaugeDrawSites[0]); ++index) {
        sceKernelIcacheInvalidateRange((const void *)(uintptr_t)kHudGaugeDrawSites[index].address, 4u);
    }
    for (index = 0; index < sizeof(kHudSideStripSites) / sizeof(kHudSideStripSites[0]); ++index) {
        sceKernelIcacheInvalidateRange((const void *)(uintptr_t)kHudSideStripSites[index].address, 4u);
    }
    for (index = 0; index < sizeof(kHudWinnerGlowSites) / sizeof(kHudWinnerGlowSites[0]); ++index) {
        sceKernelIcacheInvalidateRange((const void *)(uintptr_t)kHudWinnerGlowSites[index].address, 4u);
    }
}

static void write32(uint32_t address, uint32_t value) {
    *(volatile uint32_t *)(uintptr_t)address = value;
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
        return 0;
    }

    *aspect = 0.0f;
    result = sceIoDevctl(PPSSPP_EMULATOR_DEVICE,
                         PPSSPP_DEVCTL_GET_ASPECT_RATIO,
                         NULL,
                         0,
                         aspect,
                         sizeof(*aspect));

    return result >= 0 && tekken6_aspect_is_valid(*aspect);
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

static void apply_aspect(uint32_t target_lui, uint32_t target_ori) {
    unsigned int index;

    for (index = 0; index < ASPECT_PAIR_COUNT; ++index) {
        write32(kAspectAddresses[index][0], target_lui);
        write32(kAspectAddresses[index][1], target_ori);
    }

    sceKernelDcacheWritebackInvalidateAll();
    for (index = 0; index < ASPECT_PAIR_COUNT; ++index) {
        sceKernelIcacheInvalidateRange((const void *)(uintptr_t)kAspectAddresses[index][0], 8u);
    }
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
    unsigned int attempt;

    (void)args;
    (void)argp;

    for (attempt = 0; attempt < INIT_ATTEMPTS && !executable_ready(); ++attempt) {
        sceKernelDelayThread(INIT_DELAY_US);
    }
    if (!executable_ready()) {
        return 0;
    }

    if (!query_ppsspp_aspect(&aspect)) {
        return 0;
    }
    if (!tekken6_build_aspect_words(aspect, &target_lui, &target_ori)) {
        return 0;
    }
    if (!state_is_safe(target_lui, target_ori)) {
        return 0;
    }

    apply_aspect(target_lui, target_ori);
    (void)verify_aspect(target_lui, target_ori);

    if (tekken6_hud_supported_aspect(aspect)) {
        uint32_t slot_hook = (uint32_t)(uintptr_t)&tekken6_hud_slot_builder_wrapper;
        uint32_t rect_hook = (uint32_t)(uintptr_t)&tekken6_hud_rect_hook;
        uint32_t gauge_hook = (uint32_t)(uintptr_t)&tekken6_hud_gauge_draw_hook;
        uint32_t side_strip_hook = (uint32_t)(uintptr_t)&tekken6_hud_side_strip_hook;
        uint32_t winner_glow_hook = (uint32_t)(uintptr_t)&tekken6_hud_winner_glow_hook;
        if (hud_hooks_are_safe(slot_hook, rect_hook, gauge_hook, side_strip_hook,
                               winner_glow_hook)) {
            apply_hud_hooks();
        }
    }

    return 0;
}

int module_stop(SceSize args, void *argp) {
    (void)args;
    (void)argp;
    return 0;
}
