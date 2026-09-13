#include <assert.h>
#include <stdint.h>
#include <stdio.h>

#include "aspect_math.h"

static void expect(float aspect, uint32_t expected_lui, uint32_t expected_ori) {
    uint32_t lui = 0;
    uint32_t ori = 0;
    assert(tekken6_build_aspect_words(aspect, &lui, &ori));
    assert(lui == expected_lui);
    assert(ori == expected_ori);
}

int main(void) {
    expect(16.0f / 9.0f, 0x3c013fe3u, 0x34218e39u);
    expect(20.0f / 9.0f, 0x3c01400eu, 0x342138e4u);
    expect(21.0f / 9.0f, 0x3c014015u, 0x34215555u);
    expect(19.5f / 9.0f, 0x3c01400au, 0x3421aaabu);
    expect(16.0f / 10.0f, 0x3c013fccu, 0x3421cccdu);
    expect(4.0f / 3.0f, 0x3c013faau, 0x3421aaabu);
    assert(!tekken6_build_aspect_words(0.0f, 0, 0));
    puts("Tekken 6 aspect math tests passed");
    return 0;
}
