#include <pspuser.h>
#include <pspiofilemgr.h>
#include <pspthreadman.h>
#include <psputils.h>
#include <stdint.h>

PSP_MODULE_INFO("Tekken6UltrawideFix", PSP_MODULE_USER, 1, 5);
PSP_NO_CREATE_MAIN_THREAD();

#define CONFIG_PATH "ms0:/PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/Tekken6.PPSSPP.UltrawideFix.ini"
#define LOG_PATH    "ms0:/PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/Tekken6.PPSSPP.UltrawideFix.log"

#define BASE_ASPECT (16.0f / 9.0f)
#define BASE_UI_WIDTH 480.0f
#define ASPECT_SITE_COUNT 4
#define HUD_CALLSITE_COUNT 3
#define CAMERA_SITE 0x0895350Cu
#define HUD_INIT_B 0x08A392F0u
#define DEFAULT_PATCH_INTERVAL_MS 77

#define ORIGINAL_ASPECT_HI 0x3C013FE3u
#define ORIGINAL_ASPECT_LO 0x34218E39u
#define ORIGINAL_CAMERA_WORD 0x3C013F80u
#define ORIGINAL_HUD_INIT_JAL 0x0E28E4BCu
#define MIPS_EMUHACK_OPCODE 0x68000000u
#define MIPS_EMUHACK_MASK   0xFC000000u

static const uint32_t kAspectSites[ASPECT_SITE_COUNT] = {
    0x08945F10u,
    0x08946794u,
    0x08946BC8u,
    0x08947D90u,
};

static const uint32_t kHudInitCallsites[HUD_CALLSITE_COUNT] = {
    0x089A92D8u,
    0x089AB3A4u,
    0x089AD87Cu,
};

typedef struct Config {
    int enable3D;
    int enableCamera;
    int cameraPreset;
    int enableHUDExperimental;
    int debugLogging;
    int aspectNum;
    int aspectDen;
    int patchIntervalMs;
} Config;

/*
 * Built-in defaults remain conservative if the INI is missing: validated 3D
 * and camera stay enabled, while the new v0.5 HUD hook stays opt-in.
 */
static Config g_cfg = { 1, 1, 2, 0, 0, 20, 9, DEFAULT_PATCH_INTERVAL_MS };
static volatile int g_running = 1;
static int g_loggedUnexpected3D = 0;
static int g_loggedUnexpectedCamera = 0;
static int g_loggedUnexpectedHUD = 0;
static float g_hudCanvasWidth = BASE_UI_WIDTH;
static uint32_t g_hudHookJal = 0;

typedef int (*HudInitFn)(void *descriptor);

static int str_len(const char *s) {
    int n = 0;
    while (s && s[n]) n++;
    return n;
}

static int str_eq(const char *a, const char *b) {
    int i = 0;
    if (!a || !b) return 0;
    while (a[i] && b[i]) {
        if (a[i] != b[i]) return 0;
        i++;
    }
    return a[i] == 0 && b[i] == 0;
}

static char *trim(char *s) {
    char *end;
    if (!s) return s;
    while (*s == ' ' || *s == '\t' || *s == '\r') s++;
    end = s + str_len(s);
    while (end > s && (end[-1] == ' ' || end[-1] == '\t' || end[-1] == '\r')) end--;
    *end = 0;
    return s;
}

static int parse_int(const char *s, int fallback) {
    int value = 0;
    int any = 0;
    if (!s) return fallback;
    while (*s >= '0' && *s <= '9') {
        value = value * 10 + (*s - '0');
        any = 1;
        s++;
    }
    return any ? value : fallback;
}

static void raw_log(const char *s) {
    SceUID fd;
    if (!s) return;
    fd = sceIoOpen(LOG_PATH, PSP_O_WRONLY | PSP_O_CREAT | PSP_O_APPEND, 0777);
    if (fd >= 0) {
        sceIoWrite(fd, s, str_len(s));
        sceIoClose(fd);
    }
}

static void log_text(const char *s) {
    if (g_cfg.debugLogging) raw_log(s);
}

static void hex8(uint32_t value, char out[9]) {
    static const char h[] = "0123456789ABCDEF";
    int i;
    for (i = 0; i < 8; i++) {
        out[7 - i] = h[value & 0xFu];
        value >>= 4;
    }
    out[8] = 0;
}

static void log_pair(const char *prefix, uint32_t address) {
    char h[9];
    uint32_t a = *(volatile uint32_t *)(uintptr_t)address;
    uint32_t b = *(volatile uint32_t *)(uintptr_t)(address + 4u);
    if (!g_cfg.debugLogging) return;
    raw_log(prefix);
    hex8(address, h); raw_log("0x"); raw_log(h); raw_log(" = ");
    hex8(a, h); raw_log("0x"); raw_log(h); raw_log(" ");
    hex8(b, h); raw_log("0x"); raw_log(h); raw_log("\n");
}

static void log_word(const char *prefix, uint32_t address) {
    char h[9];
    uint32_t value = *(volatile uint32_t *)(uintptr_t)address;
    if (!g_cfg.debugLogging) return;
    raw_log(prefix);
    hex8(address, h); raw_log("0x"); raw_log(h); raw_log(" = ");
    hex8(value, h); raw_log("0x"); raw_log(h); raw_log("\n");
}

static void parse_aspect(char *value) {
    char *colon = value;
    while (*colon && *colon != ':') colon++;
    if (*colon == ':') {
        *colon = 0;
        colon++;
        g_cfg.aspectNum = parse_int(trim(value), 20);
        g_cfg.aspectDen = parse_int(trim(colon), 9);
        if (g_cfg.aspectNum <= 0) g_cfg.aspectNum = 20;
        if (g_cfg.aspectDen <= 0) g_cfg.aspectDen = 9;
    }
}

static void parse_config_line(char *line) {
    char *eq;
    char *key;
    char *value;
    char *p;

    line = trim(line);
    if (!*line || *line == ';' || *line == '#' || *line == '[') return;

    p = line;
    while (*p) {
        if (*p == ';' || *p == '#') { *p = 0; break; }
        p++;
    }

    eq = line;
    while (*eq && *eq != '=') eq++;
    if (*eq != '=') return;
    *eq = 0;
    eq++;

    key = trim(line);
    value = trim(eq);

    if (str_eq(key, "Enable3D")) g_cfg.enable3D = parse_int(value, g_cfg.enable3D) != 0;
    else if (str_eq(key, "EnableCamera")) g_cfg.enableCamera = parse_int(value, g_cfg.enableCamera) != 0;
    else if (str_eq(key, "CameraPreset")) {
        g_cfg.cameraPreset = parse_int(value, g_cfg.cameraPreset);
        if (g_cfg.cameraPreset < 0) g_cfg.cameraPreset = 0;
        if (g_cfg.cameraPreset > 3) g_cfg.cameraPreset = 3;
    }
    else if (str_eq(key, "EnableHUDExperimental"))
        g_cfg.enableHUDExperimental = parse_int(value, g_cfg.enableHUDExperimental) != 0;
    else if (str_eq(key, "DebugLogging")) g_cfg.debugLogging = parse_int(value, g_cfg.debugLogging) != 0;
    else if (str_eq(key, "ForceAspectRatio")) parse_aspect(value);
    else if (str_eq(key, "PatchIntervalMs")) {
        g_cfg.patchIntervalMs = parse_int(value, DEFAULT_PATCH_INTERVAL_MS);
        if (g_cfg.patchIntervalMs < 16) g_cfg.patchIntervalMs = 16;
        if (g_cfg.patchIntervalMs > 1000) g_cfg.patchIntervalMs = 1000;
    }
}

static void read_config(void) {
    SceUID fd;
    char buf[4096];
    int size;
    int i;
    char *line;

    fd = sceIoOpen(CONFIG_PATH, PSP_O_RDONLY, 0);
    if (fd < 0) {
        raw_log("Config: could not open INI; using built-in defaults\n");
        return;
    }

    size = sceIoRead(fd, buf, sizeof(buf) - 1);
    sceIoClose(fd);
    if (size <= 0) return;
    buf[size] = 0;

    line = buf;
    for (i = 0; i <= size; i++) {
        if (buf[i] == '\n' || buf[i] == 0) {
            buf[i] = 0;
            parse_config_line(line);
            line = &buf[i + 1];
        }
    }
}

static float get_target_aspect(void) {
    if (g_cfg.aspectNum <= 0 || g_cfg.aspectDen <= 0) return BASE_ASPECT;
    return (float)g_cfg.aspectNum / (float)g_cfg.aspectDen;
}

static uint32_t get_target_camera_word(void) {
    int preset = g_cfg.cameraPreset;
    if (preset < 0) preset = 0;
    if (preset > 3) preset = 3;
    return 0x3C010000u | (uint32_t)(0x3F80 + preset);
}

static void aspect_instructions(float aspect, uint32_t *hiInstr, uint32_t *loInstr) {
    union { float f; uint32_t u; } bits;
    bits.f = aspect;
    *hiInstr = 0x3C010000u | ((bits.u >> 16) & 0xFFFFu);
    *loInstr = 0x34210000u | (bits.u & 0xFFFFu);
}

static int pair_is(uint32_t address, uint32_t a, uint32_t b) {
    return *(volatile uint32_t *)(uintptr_t)address == a &&
           *(volatile uint32_t *)(uintptr_t)(address + 4u) == b;
}

static int word_is(uint32_t address, uint32_t value) {
    return *(volatile uint32_t *)(uintptr_t)address == value;
}

static int is_emuhack(uint32_t word) {
    return (word & MIPS_EMUHACK_MASK) == MIPS_EMUHACK_OPCODE;
}

static uint32_t make_jal(uint32_t site, uintptr_t target, int *ok) {
    if (((site + 4u) & 0xF0000000u) != ((uint32_t)target & 0xF0000000u)) {
        *ok = 0;
        return 0;
    }
    *ok = 1;
    return 0x0C000000u | (((uint32_t)target >> 2) & 0x03FFFFFFu);
}

/*
 * Experimental v0.5 HUD hook.
 *
 * The original initializer at 0x08A392F0 builds a 2D descriptor with a
 * 480x272 logical canvas. Static tracing isolated three external UI caller
 * sites which pass the descriptor in a0. We preserve the original call and
 * return value, then widen only descriptor +0x28. Nothing else in the
 * descriptor (including +0x4C) is changed.
 */
__attribute__((noinline))
static int hud_init_wide_canvas(void *descriptor) {
    HudInitFn original = (HudInitFn)(uintptr_t)HUD_INIT_B;
    int result = original(descriptor);

    if (descriptor && g_cfg.enableHUDExperimental)
        *(volatile float *)((uintptr_t)descriptor + 0x28u) = g_hudCanvasWidth;

    return result;
}

/*
 * v0.3/v0.4 invalidated and rewrote code on every 77 ms poll. That behavior
 * proved the patch could survive PPSSPP JIT/emuhack handling, but it creates
 * unnecessary code-cache churn once a translated block already contains the
 * requested patch.
 *
 * v0.5 keeps the known-good invalidate-before-write operation for initial
 * installation and actual restoration, then treats a visible target or the
 * expected PPSSPP emuhack state as healthy. This makes the runtime much less
 * invasive and reduces an avoidable compatibility variable for texture packs.
 */
static int patch_one_aspect_site(uint32_t address, uint32_t targetHi, uint32_t targetLo,
                                 int force, int verbose) {
    uint32_t a;
    uint32_t b;

    if (!force) {
        a = *(volatile uint32_t *)(uintptr_t)address;
        b = *(volatile uint32_t *)(uintptr_t)(address + 4u);

        if (a == targetHi && b == targetLo)
            return 1;

        if (is_emuhack(a) && b == targetLo)
            return 1;

        if (!((a == ORIGINAL_ASPECT_HI && b == ORIGINAL_ASPECT_LO) || is_emuhack(a))) {
            if (verbose || !g_loggedUnexpected3D) {
                log_pair("3D: unexpected live pair; skipped: ", address);
                g_loggedUnexpected3D = 1;
            }
            return 0;
        }
    }

    sceKernelIcacheInvalidateRange((const void *)(uintptr_t)address, 8u);
    a = *(volatile uint32_t *)(uintptr_t)address;
    b = *(volatile uint32_t *)(uintptr_t)(address + 4u);

    if (is_emuhack(a)) {
        if (verbose) log_pair("3D: emuhack still present after invalidate: ", address);
        return 0;
    }

    if (!((a == ORIGINAL_ASPECT_HI && b == ORIGINAL_ASPECT_LO) ||
          (a == targetHi && b == targetLo))) {
        if (verbose || !g_loggedUnexpected3D) {
            log_pair("3D: unexpected restored pair; skipped: ", address);
            g_loggedUnexpected3D = 1;
        }
        return 0;
    }

    *(volatile uint32_t *)(uintptr_t)address = targetHi;
    *(volatile uint32_t *)(uintptr_t)(address + 4u) = targetLo;
    sceKernelDcacheWritebackRange((const void *)(uintptr_t)address, 8u);

    if (verbose) log_pair("3D: installed/readback: ", address);
    return pair_is(address, targetHi, targetLo);
}

static int patch_aspect_cycle(float aspect, int force, int verbose) {
    uint32_t targetHi;
    uint32_t targetLo;
    int i;
    int ok = 0;

    aspect_instructions(aspect, &targetHi, &targetLo);
    for (i = 0; i < ASPECT_SITE_COUNT; i++)
        ok += patch_one_aspect_site(kAspectSites[i], targetHi, targetLo, force, verbose);
    return ok;
}

static int patch_camera(int force, int verbose) {
    uint32_t current;
    uint32_t target = get_target_camera_word();

    if (!force) {
        current = *(volatile uint32_t *)CAMERA_SITE;
        if (current == target || is_emuhack(current))
            return 1;
        if (current != ORIGINAL_CAMERA_WORD) {
            if (verbose || !g_loggedUnexpectedCamera) {
                log_word("Camera: unexpected live word; skipped: ", CAMERA_SITE);
                g_loggedUnexpectedCamera = 1;
            }
            return 0;
        }
    }

    sceKernelIcacheInvalidateRange((const void *)CAMERA_SITE, 4u);
    current = *(volatile uint32_t *)CAMERA_SITE;

    if (is_emuhack(current)) {
        if (verbose) log_word("Camera: emuhack still present after invalidate: ", CAMERA_SITE);
        return 0;
    }

    if (!(current == ORIGINAL_CAMERA_WORD || current == target)) {
        if (verbose || !g_loggedUnexpectedCamera) {
            log_word("Camera: unexpected restored word; skipped: ", CAMERA_SITE);
            g_loggedUnexpectedCamera = 1;
        }
        return 0;
    }

    *(volatile uint32_t *)CAMERA_SITE = target;
    sceKernelDcacheWritebackRange((const void *)CAMERA_SITE, 4u);

    if (verbose) log_word("Camera: installed/readback: ", CAMERA_SITE);
    return word_is(CAMERA_SITE, target);
}

static int patch_one_hud_callsite(uint32_t address, int force, int verbose) {
    uint32_t current;

    if (!g_hudHookJal)
        return 0;

    if (!force) {
        current = *(volatile uint32_t *)(uintptr_t)address;
        if (current == g_hudHookJal || is_emuhack(current))
            return 1;
        if (current != ORIGINAL_HUD_INIT_JAL) {
            if (verbose || !g_loggedUnexpectedHUD) {
                log_word("HUD: unexpected live callsite; skipped: ", address);
                g_loggedUnexpectedHUD = 1;
            }
            return 0;
        }
    }

    sceKernelIcacheInvalidateRange((const void *)(uintptr_t)address, 4u);
    current = *(volatile uint32_t *)(uintptr_t)address;

    if (is_emuhack(current)) {
        if (verbose) log_word("HUD: emuhack still present after invalidate: ", address);
        return 0;
    }

    if (!(current == ORIGINAL_HUD_INIT_JAL || current == g_hudHookJal)) {
        if (verbose || !g_loggedUnexpectedHUD) {
            log_word("HUD: unexpected restored callsite; skipped: ", address);
            g_loggedUnexpectedHUD = 1;
        }
        return 0;
    }

    *(volatile uint32_t *)(uintptr_t)address = g_hudHookJal;
    sceKernelDcacheWritebackRange((const void *)(uintptr_t)address, 4u);

    if (verbose) log_word("HUD: installed targeted initializer hook: ", address);
    return word_is(address, g_hudHookJal);
}

static int patch_hud_cycle(int force, int verbose) {
    int i;
    int ok = 0;
    for (i = 0; i < HUD_CALLSITE_COUNT; i++)
        ok += patch_one_hud_callsite(kHudInitCallsites[i], force, verbose);
    return ok;
}

static int patch_thread(SceSize args, void *argp) {
    float aspect = get_target_aspect();
    int first3D = 1;
    int firstCamera = 1;
    int firstHUD = 1;
    (void)args;
    (void)argp;

    while (g_running) {
        if (g_cfg.enable3D) {
            int ok = patch_aspect_cycle(aspect, first3D, first3D);
            if (first3D) {
                if (ok == ASPECT_SITE_COUNT)
                    log_text("3D: initial low-churn cycle installed all four sites\n");
                else
                    log_text("3D: initial low-churn cycle did not install all four sites\n");
                first3D = 0;
            }
        }

        if (g_cfg.enableCamera) {
            int ok = patch_camera(firstCamera, firstCamera);
            if (firstCamera) {
                if (ok)
                    log_text("Camera: initial low-churn cycle installed the camera site\n");
                else
                    log_text("Camera: initial low-churn cycle did not install the camera site\n");
                firstCamera = 0;
            }
        }

        if (g_cfg.enableHUDExperimental && g_hudHookJal) {
            int ok = patch_hud_cycle(firstHUD, firstHUD);
            if (firstHUD) {
                if (ok == HUD_CALLSITE_COUNT)
                    log_text("HUD: installed all three targeted experimental UI hooks\n");
                else
                    log_text("HUD: did not install all three targeted experimental UI hooks\n");
                firstHUD = 0;
            }
        }

        sceKernelDelayThread((unsigned int)g_cfg.patchIntervalMs * 1000u);
    }
    return 0;
}

int module_start(SceSize args, void *argp) {
    SceUID thread;
    float aspect;
    int jalOk = 0;
    (void)args;
    (void)argp;

    sceIoRemove(LOG_PATH);
    raw_log("=== Tekken6.PPSSPP.UltrawideFix v0.5 ===\n");
    raw_log("Plugin module_start reached successfully\n");

    read_config();
    aspect = get_target_aspect();
    g_hudCanvasWidth = BASE_UI_WIDTH * (aspect / BASE_ASPECT);
    g_hudHookJal = make_jal(kHudInitCallsites[0], (uintptr_t)&hud_init_wide_canvas, &jalOk);

    if (g_cfg.enableHUDExperimental && !jalOk) {
        g_hudHookJal = 0;
        raw_log("HUD: hook target is outside the callsites' JAL region; experimental HUD disabled\n");
    }

    thread = sceKernelCreateThread("T6UWRuntime", patch_thread, 0x20, 0x3000, 0, 0);
    if (thread >= 0 && sceKernelStartThread(thread, 0, 0) >= 0)
        log_text("Runtime: low-churn maintenance thread started\n");
    else
        raw_log("Runtime: failed to start maintenance thread\n");

    raw_log("=== module_start complete ===\n");
    return 0;
}

int module_stop(SceSize args, void *argp) {
    (void)args;
    (void)argp;
    g_running = 0;
    return 0;
}
