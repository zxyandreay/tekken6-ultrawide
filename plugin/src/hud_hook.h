#ifndef TEKKEN6_HUD_HOOK_H
#define TEKKEN6_HUD_HOOK_H

#include <stdint.h>

extern volatile uint32_t tekken6_hud_shell_depth;

int tekken6_hud_slot_builder_wrapper(uint32_t a0,
                                     uint32_t a1,
                                     uint32_t a2,
                                     uint32_t a3);

void tekken6_hud_rect_hook(void);

void tekken6_hud_gauge_draw_hook(void);

void tekken6_hud_side_strip_hook(void);

void tekken6_hud_winner_glow_hook(void);

int tekken6_hud_supported_aspect(float aspect);

#endif
