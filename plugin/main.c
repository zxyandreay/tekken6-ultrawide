#include <pspuser.h>
#include <pspiofilemgr.h>
#include <pspthreadman.h>
#include <pspmodulemgr.h>
#include <psputils.h>
#include <stdint.h>

PSP_MODULE_INFO("Tekken6UltrawideFix", PSP_MODULE_USER, 1, 1);
PSP_NO_CREATE_MAIN_THREAD();

#define CONFIG_PATH "ms0:/PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/Tekken6.PPSSPP.UltrawideFix.ini"
#define LOG_PATH    "ms0:/PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/Tekken6.PPSSPP.UltrawideFix.log"

#define EMULATOR_DEVCTL_GET_ASPECT_RATIO 0x31
#define BASE_ASPECT (16.0f / 9.0f)
#define ASPECT_SITE_COUNT 4
#define MAX_MODULES 64

#define ORIGINAL_ASPECT_HI 0x3C013FE3u
#define ORIGINAL_ASPECT_LO 0x34218E39u

/*
 * Relative spacing between the four verified ULUS10466 aspect-dispatch
 * case-0 instruction pairs.  This is used as a runtime signature rather
 * than assuming that the main module is always loaded at the same address.
 */
static const uint32_t kAspectRelative[ASPECT_SITE_COUNT] = {
    0x0000u,
    0x0884u,
    0x0CB8u,
    0x1E80u,
};

/* Known ULUS10466 addresses retained only as a signature-checked fallback
 * and for diagnostics.  No fallback write is performed unless all four
 * locations contain the expected original/target instruction shape.
 */
static const uint32_t kKnownAspectSites[ASPECT_SITE_COUNT] = {
    0x08945F10u,
    0x08946794u,
    0x08946BC8u,
    0x08947D90u,
};

typedef struct Config {
    int enable3D;
    int debugLogging;
    int aspectAuto;
    int aspectNum;
    int aspectDen;
} Config;

static Config g_cfg = { 1, 1, 0, 20, 9 };
static uint32_t g_aspectSites[ASPECT_SITE_COUNT];
static int g_sitesFound = 0;

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
    int sign = 1;
    int value = 0;
    int any = 0;
    if (!s) return fallback;
    if (*s == '-') { sign = -1; s++; }
    while (*s >= '0' && *s <= '9') {
        value = value * 10 + (*s - '0');
        any = 1;
        s++;
    }
    return any ? value * sign : fallback;
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
    if (!g_cfg.debugLogging) return;
    raw_log(s);
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

static void log_hex(const char *prefix, uint32_t value, const char *suffix) {
    char h[9];
    if (!g_cfg.debugLogging) return;
    hex8(value, h);
    raw_log(prefix);
    raw_log("0x");
    raw_log(h);
    raw_log(suffix);
}

static void log_pair(const char *prefix, uint32_t address) {
    uint32_t a = *(volatile uint32_t *)address;
    uint32_t b = *(volatile uint32_t *)(address + 4u);
    if (!g_cfg.debugLogging) return;
    raw_log(prefix);
    log_hex("", address, " = ");
    log_hex("", a, " ");
    log_hex("", b, "\n");
}

static void parse_aspect_value(char *value) {
    char *colon;
    if (str_eq(value, "auto")) {
        g_cfg.aspectAuto = 1;
        return;
    }

    colon = value;
    while (*colon && *colon != ':') colon++;
    if (*colon == ':') {
        *colon = 0;
        colon++;
        g_cfg.aspectNum = parse_int(trim(value), 20);
        g_cfg.aspectDen = parse_int(trim(colon), 9);
        if (g_cfg.aspectNum <= 0) g_cfg.aspectNum = 20;
        if (g_cfg.aspectDen <= 0) g_cfg.aspectDen = 9;
        g_cfg.aspectAuto = 0;
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
    else if (str_eq(key, "DebugLogging")) g_cfg.debugLogging = parse_int(value, g_cfg.debugLogging) != 0;
    else if (str_eq(key, "ForceAspectRatio")) parse_aspect_value(value);
}

static void read_config(void) {
    SceUID fd;
    char buf[4096];
    int size;
    int i;
    char *line;

    fd = sceIoOpen(CONFIG_PATH, PSP_O_RDONLY, 0);
    if (fd < 0) {
        raw_log("Config: could not open INI; using built-in 20:9 defaults\n");
        return;
    }

    size = sceIoRead(fd, buf, sizeof(buf) - 1);
    sceIoClose(fd);
    if (size <= 0) {
        raw_log("Config: INI was empty/unreadable; using defaults\n");
        return;
    }
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
    float aspect;
    if (g_cfg.aspectAuto) {
        aspect = 0.0f;
        if (sceIoDevctl("kemulator:", EMULATOR_DEVCTL_GET_ASPECT_RATIO,
                       0, 0, &aspect, sizeof(aspect)) >= 0 && aspect > 1.0f) {
            log_text("Aspect: PPSSPP auto value accepted\n");
            return aspect;
        }
        log_text("Aspect: PPSSPP auto query failed; using configured fallback\n");
    }

    if (g_cfg.aspectNum <= 0 || g_cfg.aspectDen <= 0) return BASE_ASPECT;
    return (float)g_cfg.aspectNum / (float)g_cfg.aspectDen;
}

static void aspect_instructions(float aspect, uint32_t *hiInstr, uint32_t *loInstr) {
    union { float f; uint32_t u; } bits;
    bits.f = aspect;
    *hiInstr = 0x3C010000u | ((bits.u >> 16) & 0xFFFFu);
    *loInstr = 0x34210000u | (bits.u & 0xFFFFu);
}

static int pair_is(uint32_t address, uint32_t a, uint32_t b) {
    return *(volatile uint32_t *)address == a &&
           *(volatile uint32_t *)(address + 4u) == b;
}

static int pair_is_original_or_target(uint32_t address, uint32_t targetHi, uint32_t targetLo) {
    if (pair_is(address, ORIGINAL_ASPECT_HI, ORIGINAL_ASPECT_LO)) return 1;
    if (pair_is(address, targetHi, targetLo)) return 1;
    return 0;
}

static int validate_relative_signature(uint32_t first, uint32_t textEnd,
                                       uint32_t targetHi, uint32_t targetLo,
                                       uint32_t outSites[ASPECT_SITE_COUNT]) {
    int i;
    if (first + kAspectRelative[ASPECT_SITE_COUNT - 1] + 8u > textEnd) return 0;

    for (i = 0; i < ASPECT_SITE_COUNT; i++) {
        uint32_t address = first + kAspectRelative[i];
        if (!pair_is_original_or_target(address, targetHi, targetLo)) return 0;
        outSites[i] = address;
    }
    return 1;
}

static int find_sites_in_module(const SceKernelModuleInfo *info,
                                uint32_t targetHi, uint32_t targetLo,
                                uint32_t outSites[ASPECT_SITE_COUNT]) {
    uint32_t start;
    uint32_t end;
    uint32_t address;

    if (!info || info->text_size < 0x200000u) return 0;
    start = info->text_addr;
    end = info->text_addr + info->text_size;

    for (address = start; address + kAspectRelative[ASPECT_SITE_COUNT - 1] + 8u <= end; address += 4u) {
        if (!pair_is_original_or_target(address, targetHi, targetLo)) continue;
        if (validate_relative_signature(address, end, targetHi, targetLo, outSites)) return 1;
    }
    return 0;
}

static int discover_aspect_sites(float aspect) {
    SceUID modules[MAX_MODULES];
    int moduleCount = 0;
    int result;
    int i;
    uint32_t targetHi;
    uint32_t targetLo;

    aspect_instructions(aspect, &targetHi, &targetLo);

    result = sceKernelGetModuleIdList(modules, sizeof(modules), &moduleCount);
    if (result >= 0) {
        log_hex("Modules: count=", (uint32_t)moduleCount, "\n");
        if (moduleCount > MAX_MODULES) moduleCount = MAX_MODULES;

        for (i = 0; i < moduleCount; i++) {
            SceKernelModuleInfo info;
            info.size = sizeof(info);
            if (sceKernelQueryModuleInfo(modules[i], &info) < 0) continue;

            if (g_cfg.debugLogging) {
                raw_log("Module: ");
                raw_log(info.name);
                log_hex(" text=", info.text_addr, "");
                log_hex(" size=", info.text_size, "\n");
            }

            if (find_sites_in_module(&info, targetHi, targetLo, g_aspectSites)) {
                g_sitesFound = 1;
                raw_log("3D: verified four-site relative signature found in module ");
                raw_log(info.name);
                raw_log("\n");
                for (i = 0; i < ASPECT_SITE_COUNT; i++)
                    log_pair("3D discovery: ", g_aspectSites[i]);
                return 1;
            }
        }
    } else {
        log_text("Modules: sceKernelGetModuleIdList failed\n");
    }

    /* Signature-checked fixed-address fallback for this exact ULUS10466 EBOOT. */
    for (i = 0; i < ASPECT_SITE_COUNT; i++) {
        if (!pair_is_original_or_target(kKnownAspectSites[i], targetHi, targetLo)) {
            log_text("3D: fixed-address fallback signature check failed\n");
            return 0;
        }
    }

    for (i = 0; i < ASPECT_SITE_COUNT; i++) g_aspectSites[i] = kKnownAspectSites[i];
    g_sitesFound = 1;
    log_text("3D: using verified fixed-address ULUS10466 fallback\n");
    for (i = 0; i < ASPECT_SITE_COUNT; i++) log_pair("3D fallback: ", g_aspectSites[i]);
    return 1;
}

static int patch_3d(float aspect) {
    uint32_t targetHi;
    uint32_t targetLo;
    int i;
    int patched = 0;

    if (!g_sitesFound) return 0;
    aspect_instructions(aspect, &targetHi, &targetLo);

    for (i = 0; i < ASPECT_SITE_COUNT; i++) {
        uint32_t address = g_aspectSites[i];

        if (!pair_is_original_or_target(address, targetHi, targetLo)) {
            log_pair("3D: unexpected pair before patch: ", address);
            continue;
        }

        *(volatile uint32_t *)address = targetHi;
        *(volatile uint32_t *)(address + 4u) = targetLo;

        /* Use precise range invalidation. PPSSPP maps this user syscall to
         * deferred JIT invalidation for the modified code range. */
        sceKernelDcacheWritebackRange((const void *)address, 8u);
        sceKernelIcacheInvalidateRange((const void *)address, 8u);

        if (pair_is(address, targetHi, targetLo)) {
            log_pair("3D patched/readback: ", address);
            patched++;
        } else {
            log_pair("3D: readback mismatch: ", address);
        }
    }

    return patched;
}

static int verify_3d(float aspect) {
    uint32_t targetHi;
    uint32_t targetLo;
    int i;
    if (!g_sitesFound) return 0;
    aspect_instructions(aspect, &targetHi, &targetLo);
    for (i = 0; i < ASPECT_SITE_COUNT; i++) {
        if (!pair_is(g_aspectSites[i], targetHi, targetLo)) return 0;
    }
    return 1;
}

static int delayed_verify_thread(SceSize args, void *argp) {
    float aspect;
    int pass;
    (void)args;
    (void)argp;

    aspect = get_target_aspect();

    /* Verify several times during early boot. This is diagnostic: if the game
     * or a savestate restores the original instructions after module_start,
     * the log will expose that and we reapply while this thread remains alive.
     */
    for (pass = 1; pass <= 12; pass++) {
        sceKernelDelayThread(250000); /* 250 ms */
        if (!g_sitesFound) {
            if (discover_aspect_sites(aspect) && g_cfg.enable3D) {
                log_text("3D monitor: sites discovered after module_start; patching now\n");
                patch_3d(aspect);
            }
            continue;
        }

        if (g_cfg.enable3D && !verify_3d(aspect)) {
            log_text("3D monitor: patch was reverted/changed; reapplying\n");
            patch_3d(aspect);
        }
    }

    if (g_sitesFound && verify_3d(aspect))
        log_text("3D monitor: target instructions remained present through early boot\n");
    else
        log_text("3D monitor: target instructions were not stable/present\n");

    return 0;
}

int module_start(SceSize args, void *argp) {
    float aspect;
    int patched = 0;
    SceUID thread;
    int i;
    (void)args;
    (void)argp;

    /* Always reset/create a fresh log before INI parsing.  If this file does
     * not appear, PPSSPP did not start this PRX (wrong memstick, plugins off,
     * unsupported game ID, or load failure). */
    sceIoRemove(LOG_PATH);
    raw_log("=== Tekken6.PPSSPP.UltrawideFix v0.2 runtime diagnostic ===\n");
    raw_log("Plugin module_start reached successfully\n");

    read_config();
    aspect = get_target_aspect();

    for (i = 0; i < ASPECT_SITE_COUNT; i++)
        log_pair("Known-address pre-scan: ", kKnownAspectSites[i]);

    if (discover_aspect_sites(aspect)) {
        if (g_cfg.enable3D) patched = patch_3d(aspect);
        else log_text("3D: disabled in configuration\n");
    } else {
        log_text("3D: could not identify verified Tekken aspect sites; no write performed\n");
    }

    if (patched == ASPECT_SITE_COUNT)
        log_text("3D: all four sites patched and immediate readback verified\n");
    else if (g_cfg.enable3D)
        log_text("3D: four-site patch did not fully verify; inspect this log\n");

    thread = sceKernelCreateThread("T6UWVerify", delayed_verify_thread, 0x20, 0x3000, 0, 0);
    if (thread >= 0) {
        if (sceKernelStartThread(thread, 0, 0) >= 0)
            log_text("3D monitor: early-boot verification thread started\n");
        else
            log_text("3D monitor: failed to start verification thread\n");
    } else {
        log_text("3D monitor: failed to create verification thread\n");
    }

    raw_log("=== module_start complete ===\n");
    return 0;
}

int module_stop(SceSize args, void *argp) {
    (void)args;
    (void)argp;
    return 0;
}
