#include "aspect_math.h"

#include <stdint.h>

static uint32_t float_bits(float value) {
    union {
        float value;
        uint32_t bits;
    } converted;
    converted.value = value;
    return converted.bits;
}

int tekken6_aspect_is_valid(float aspect) {
    uint32_t bits = float_bits(aspect);
    return (bits & 0x7f800000u) != 0x7f800000u
        && aspect >= 1.0f
        && aspect <= 4.0f;
}

int tekken6_build_aspect_words(float aspect, uint32_t *lui_word, uint32_t *ori_word) {
    uint32_t bits;
    if (lui_word == 0 || ori_word == 0 || !tekken6_aspect_is_valid(aspect)) {
        return 0;
    }
    bits = float_bits(aspect);
    *lui_word = 0x3c010000u | (bits >> 16);
    *ori_word = 0x34210000u | (bits & 0xffffu);
    return 1;
}
