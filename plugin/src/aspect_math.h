#ifndef TEKKEN6_ASPECT_MATH_H
#define TEKKEN6_ASPECT_MATH_H

#include <stdint.h>

int tekken6_aspect_is_valid(float aspect);
int tekken6_build_aspect_words(float aspect, uint32_t *lui_word, uint32_t *ori_word);

#endif
