#include <pspuser.h>
#include <pspiofilemgr.h>
#include <pspthreadman.h>
#include <stdint.h>

PSP_MODULE_INFO("Tekken6UltrawideFix", PSP_MODULE_USER, 1, 0);
PSP_NO_CREATE_MAIN_THREAD();

#define CONFIG_PATH "ms0:/PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/Tekken6.PPSSPP.UltrawideFix.ini"
#define LOG_PATH    "ms0:/PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/Tekken6.PPSSPP.UltrawideFix.log"

#define EMULATOR_DEVCTL_GET_ASPECT_RATIO 0x31
#define BASE_ASPECT (16.0f / 9.0f)

/*
 * ULUS10466 verified 3D aspect-dispatch case-0 sites.
 * These are the same four locations used by the known-good CWCheat.
 */
static const uint32_t kAspectSites[4] = {
    0x08945F10,
    0x08946794,
    0x08946BC8,
    0x08947D90,
};

/*
 * Experimental Warriors-style HUD candidates from the current research.
 * Group A ranks as the stronger general 2D/render-descriptor candidate.
 * Group B appears mask-like and is kept separate so it can be classified.
 */
static const uint32_t kHudGroupA[3] = {
    0x08A39288,
    0x08A392F4,
    0x08A39360,
};

static const uint32_t kHudGroupB[3] = {
    0x08AA6314,
    0x08AA63B8,
    0x08AA64C0,
};

typedef struct Config {
    int enable3D;
    int hudMode;              /* 0=off, 1=A, 2=B, 3=A+B */
    int hudVirtualWidth;      /* 0=derive from aspect */
    int debugLogging;
    int aspectAuto;
    int aspectNum;
    int aspectDen;
} Config;

static Config g_cfg = { 1, 1, 600, 1, 0, 20, 9 };

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

static void log_text(const char *s) {
    SceUID fd;
    if (!g_cfg.debugLogging || !s) return;
    fd = sceIoOpen(LOG_PATH, PSP_O_WRONLY | PSP_O_CREAT | PSP_O_APPEND, 0777);
    if (fd >= 0) {
        sceIoWrite(fd, s, str_len(s));
        sceIoClose(fd);
    }
}

static void hex8(uint32_t value, char out[9]) {
    static const char h[] = "0123456789ABCDEF";
    int i;
    for (i = 0; i < 8; i++) {
        out[7 - i] = h[value & 0xF];
        value >>= 4;
    }
    out[8] = 0;
}

static void log_addr(const char *prefix, uint32_t address, const char *suffix) {
    char h[9];
    hex8(address, h);
    log_text(prefix);
    log_text("0x");
    log_text(h);
    log_text(suffix);
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
    else if (str_eq(key, "HUDMode")) g_cfg.hudMode = parse_int(value, g_cfg.hudMode);
    else if (str_eq(key, "HUDVirtualWidth")) g_cfg.hudVirtualWidth = parse_int(value, g_cfg.hudVirtualWidth);
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
    if (fd < 0) return;
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

    if (g_cfg.hudMode < 0 || g_cfg.hudMode > 3) g_cfg.hudMode = 0;
}

static uint32_t read32(uint32_t address) {
    return *(volatile uint32_t *)address;
}

static void write32(uint32_t address, uint32_t value) {
    *(volatile uint32_t *)address = value;
}

static int is_aspect_pair(uint32_t address) {
    uint32_t a = read32(address);
    uint32_t b = read32(address + 4);
    return ((a & 0xFFFF0000u) == 0x3C010000u) &&
           ((b & 0xFFFF0000u) == 0x34210000u);
}

static int wait_for_game_code(void) {
    int i;
    for (i = 0; i < 300; i++) {
        if (is_aspect_pair(kAspectSites[0])) return 1;
        sceKernelDelayThread(10000); /* 10 ms */
    }
    return 0;
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
        log_text("Aspect: PPSSPP auto query failed; using configured ratio\n");
    }

    if (g_cfg.aspectNum <= 0 || g_cfg.aspectDen <= 0) return BASE_ASPECT;
    return (float)g_cfg.aspectNum / (float)g_cfg.aspectDen;
}

static int patch_3d(float aspect) {
    union { float f; uint32_t u; } bits;
    uint32_t hi;
    uint32_t lo;
    int i;
    int patched = 0;

    bits.f = aspect;
    hi = (bits.u >> 16) & 0xFFFFu;
    lo = bits.u & 0xFFFFu;

    for (i = 0; i < 4; i++) {
        uint32_t address = kAspectSites[i];
        if (!is_aspect_pair(address)) {
            log_addr("3D: signature mismatch at ", address, "; skipped\n");
            continue;
        }
        write32(address,     0x3C010000u | hi); /* lui at, upper(aspect) */
        write32(address + 4, 0x34210000u | lo); /* ori at, at, lower(aspect) */
        log_addr("3D: patched ", address, "\n");
        patched++;
    }
    return patched;
}

static int patch_hud_site(uint32_t address, float virtualWidth) {
    union { float f; uint32_t u; } bits;
    uint32_t word = read32(address);
    uint32_t currentUpper;
    uint32_t targetUpper;

    bits.f = virtualWidth;
    targetUpper = (bits.u >> 16) & 0xFFFFu;

    /* These candidate sites are LUI float loads. A one-word patch is only
       exact when the target float has a zero lower half, as 600.0 does. */
    if ((bits.u & 0xFFFFu) != 0) {
        log_text("HUD: virtual width cannot be represented by safe one-word LUI patch; skipped\n");
        return 0;
    }
    if ((word >> 26) != 0x0Fu) {
        log_addr("HUD: expected LUI at ", address, "; skipped\n");
        return 0;
    }

    currentUpper = word & 0xFFFFu;
    if (currentUpper != 0x43F0u && currentUpper != targetUpper) {
        log_addr("HUD: unexpected 480.0 signature at ", address, "; skipped\n");
        return 0;
    }

    write32(address, (word & 0xFFFF0000u) | targetUpper);
    log_addr("HUD: patched candidate at ", address, "\n");
    return 1;
}

static int patch_hud_group(const uint32_t *sites, int count, float virtualWidth) {
    int i;
    int patched = 0;
    for (i = 0; i < count; i++) patched += patch_hud_site(sites[i], virtualWidth);
    return patched;
}

static int patch_hud(float aspect) {
    float width;
    int patched = 0;

    if (g_cfg.hudMode == 0) return 0;

    if (g_cfg.hudVirtualWidth > 0) width = (float)g_cfg.hudVirtualWidth;
    else width = 480.0f * (aspect / BASE_ASPECT);

    if (g_cfg.hudMode == 1 || g_cfg.hudMode == 3)
        patched += patch_hud_group(kHudGroupA, 3, width);
    if (g_cfg.hudMode == 2 || g_cfg.hudMode == 3)
        patched += patch_hud_group(kHudGroupB, 3, width);

    return patched;
}

int module_start(SceSize args, void *argp) {
    float aspect;
    int p3d = 0;
    int phud = 0;
    (void)args;
    (void)argp;

    read_config();
    log_text("\n=== Tekken6.PPSSPP.UltrawideFix start ===\n");

    if (!wait_for_game_code()) {
        log_text("Game code signature was not found. No patches applied.\n");
        return 0;
    }

    aspect = get_target_aspect();

    if (g_cfg.enable3D) p3d = patch_3d(aspect);
    phud = patch_hud(aspect);

    sceKernelDcacheWritebackAll();
    sceKernelIcacheInvalidateAll();

    if (p3d == 4) log_text("3D: all four verified aspect sites patched successfully\n");
    else log_text("3D: not all verified aspect sites were patched; inspect log/signatures\n");

    if (g_cfg.hudMode != 0) {
        if (phud > 0) log_text("HUD: experimental candidate patch applied; visual validation required\n");
        else log_text("HUD: experimental patch did not apply\n");
    }

    log_text("=== patch pass complete ===\n");
    return 0;
}

int module_stop(SceSize args, void *argp) {
    (void)args;
    (void)argp;
    return 0;
}
