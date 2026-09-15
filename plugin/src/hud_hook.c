#include "hud_hook.h"

volatile uint32_t tekken6_hud_shell_depth;

int tekken6_hud_supported_aspect(float aspect) {
    /* Fixed 20:9 proof build. Dynamic coefficients come after this path is shipped safely. */
    return aspect >= 2.20f && aspect <= 2.24f;
}
