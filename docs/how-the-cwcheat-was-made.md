# How the Tekken 6 Ultrawide CWCheat Was Made

This document explains a reproducible reverse-engineering workflow behind the aspect-ratio portion of this project's Tekken 6 CWCheat for the USA release (`ULUS10466`).

## What the patch is actually changing

PPSSPP can stretch the final PSP framebuffer to fill a wider display, but that alone does not change the game's internal 3D projection. Without correcting the projection, the image is simply stretched horizontally.

The goal is therefore to find how Tekken 6 represents its normal 16:9 projection inside PSP/MIPS code, identify the code paths that use it, and replace that value with another target aspect ratio.

For the original widescreen projection:

```text
16 / 9 = 1.777777777...
```

As an IEEE-754 single-precision float:

```text
1.7777778 = 0x3FE38E39
```

That numerical signature gives us something useful to search for, but the important part of the process is not to assume in advance how the game stores or constructs it.

## 1. Start from the mathematical signature of 16:9

A straightforward first thought is to search the game's executable or runtime memory for the raw bytes representing `0x3FE38E39`.

That can work for games that store the aspect ratio as a normal float in a data table, but the Tekken 6 projection paths patched here reconstruct the value in MIPS instructions instead.

The confirmed code uses this pair:

```asm
lui  $at, 0x3FE3
ori  $at, $at, 0x8E39
```

Machine code:

```text
3C013FE3
34218E39
```

The two 16-bit immediates reconstruct:

```text
0x3FE3 << 16 | 0x8E39
= 0x3FE38E39
= 1.7777778
≈ 16:9
```

The useful reverse-engineering task is therefore not simply to search for `3C013FE3 34218E39`. Before that pattern is known, code can be scanned for instruction sequences that construct plausible floating-point constants and then ranked against common aspect ratios.

## 2. Use a decrypted EBOOT.BIN for static analysis

A useful static-analysis input is the game's decrypted `EBOOT.BIN`. PPSSPP can produce a decrypted executable for analysis, giving access to the PSP/MIPS machine code without having to inspect every instruction manually while the game is running.

The important distinction is that an `EBOOT.BIN` file offset is not automatically a runtime PSP address or a CWCheat offset.

```text
EBOOT file offset
        ↓
map executable segment into PSP virtual memory
        ↓
runtime PSP address
        ↓
convert to CWCheat offset
```

The EBOOT is therefore most useful for discovering candidate instructions. Runtime memory or the PPSSPP debugger is then used to confirm where those instructions are loaded and whether changing them actually affects the projection.

For quick triage, a script can scan the binary on 4-byte boundaries. For more precise analysis, restrict the scan to executable sections or segments rather than treating every byte in the file as code.

## 3. Use Python to discover candidate MIPS aspect-ratio constants

Python can walk through the decrypted EBOOT's MIPS instructions and look for the general pattern:

```asm
lui  register, HIGH16
ori  same_register, same_register, LOW16
```

For every matching pair it can reconstruct the 32-bit value:

```text
(HIGH16 << 16) | LOW16
```

The reconstructed bits can then be interpreted as an IEEE-754 float and compared against common aspect ratios such as 4:3, 16:10, 16:9, 2:1, 20:9, and 21:9.

A minimal scanner looks like this:

```python
import struct

TARGET_RATIOS = {
    "4:3": 4 / 3,
    "16:10": 16 / 10,
    "16:9": 16 / 9,
    "2:1": 2.0,
    "20:9": 20 / 9,
    "21:9": 21 / 9,
}

with open("EBOOT.BIN", "rb") as f:
    data = f.read()


def bits_to_float(bits):
    return struct.unpack(">f", bits.to_bytes(4, "big"))[0]


for offset in range(0, len(data) - 8, 4):
    # PSP MIPS instructions are little-endian.
    word1 = struct.unpack_from("<I", data, offset)[0]
    word2 = struct.unpack_from("<I", data, offset + 4)[0]

    # Decode fields from the first instruction.
    op1 = (word1 >> 26) & 0x3F
    rs1 = (word1 >> 21) & 0x1F
    rt1 = (word1 >> 16) & 0x1F
    imm1 = word1 & 0xFFFF

    # Decode fields from the second instruction.
    op2 = (word2 >> 26) & 0x3F
    rs2 = (word2 >> 21) & 0x1F
    rt2 = (word2 >> 16) & 0x1F
    imm2 = word2 & 0xFFFF

    # LUI rt, immediate
    is_lui = op1 == 0x0F and rs1 == 0

    # ORI rt, rt, immediate
    is_ori_same_register = (
        op2 == 0x0D
        and rs2 == rt1
        and rt2 == rt1
    )

    if not (is_lui and is_ori_same_register):
        continue

    bits = (imm1 << 16) | imm2

    try:
        value = bits_to_float(bits)
    except (OverflowError, struct.error):
        continue

    for name, ratio in TARGET_RATIOS.items():
        if abs(value - ratio) < 0.00001:
            print(
                f"file_offset=0x{offset:08X} "
                f"words={word1:08X} {word2:08X} "
                f"float={value:.9f} candidate={name}"
            )
```

This does not require knowing the final Tekken 6 instruction pair beforehand. It recognizes the instruction structure first, reconstructs the constant, and then asks whether that constant looks like an aspect ratio.

A broader version can also print any reconstructed float in a plausible range, such as:

```python
if 1.2 <= value <= 3.0:
    print(...)
```

Those results can be ranked by distance from common aspect ratios. This is useful when a game uses a nearby projection constant instead of an exact conventional ratio.

The scanner is a candidate finder, not proof. False positives are possible, especially when scanning an entire binary rather than only executable code sections.

## 4. Identify the Tekken 6 candidates

For Tekken 6, the relevant candidates reconstruct the original 16:9 value:

```text
0x3FE38E39
= 1.777777791...
≈ 16 / 9
```

using the instruction pair:

```text
3C013FE3
34218E39
```

The released cheat patches four occurrences:

```text
CWCheat offsets

0x00145F10 / 0x00145F14
0x00146794 / 0x00146798
0x00146BC8 / 0x00146BCC
0x00147D90 / 0x00147D94
```

In PSP user memory, those correspond to:

```text
0x08945F10 / 0x08945F14
0x08946794 / 0x08946798
0x08946BC8 / 0x08946BCC
0x08947D90 / 0x08947D94
```

At the original 16:9 setting, each pair reconstructs the same float.

### Mapping EBOOT results to runtime addresses

If a candidate was found in the decrypted EBOOT, its file offset must first be mapped through the executable's loaded segment layout to determine the corresponding PSP virtual address.

Do not assume:

```text
EBOOT offset 0x00145F10
=
PSP address 0x08945F10
```

That relationship is only valid if the file layout and loaded memory layout happen to line up in that way. The runtime address should be confirmed using the executable's segment mapping or by locating the same instruction sequence in PPSSPP memory/disassembly.

Once the runtime addresses are confirmed, they can be converted into CWCheat offsets.

## 5. Validate the candidates in PPSSPP

Finding several matching 16:9 instruction sequences is only candidate discovery. It does not prove that every occurrence controls projection.

The next step is controlled runtime experimentation.

A useful temporary test value is 2:1 because its IEEE-754 representation is simple:

```text
2.0 = 0x40000000
```

Using the same instruction pattern gives:

```asm
lui  $at, 0x4000
ori  $at, $at, 0x0000
```

Machine code:

```text
3C014000
34210000
```

Candidate locations can then be patched individually or in groups while the game is running.

The goal is to determine whether the 3D projection changes in a way consistent with an aspect-ratio adjustment rather than an unrelated gameplay or rendering variable.

Useful states to test include:

- normal gameplay
- multiple stages
- round intros and transitions
- replays
- other scenes that may initialize or use a different projection path

If changing one occurrence affects only some scenes, that is evidence that other matching paths may also need to be patched. The released Tekken 6 cheat modifies all four confirmed occurrences so the correction remains consistent across the relevant rendering paths.

## 6. Generate target ratios with Python

Once the candidate instructions are confirmed to control the projection, the final replacement values are no longer guesses.

For each target aspect ratio:

```text
ratio = width / height
```

Python can convert the ratio to an IEEE-754 single-precision value and preserve the original `lui` / `ori` instruction structure.

A compact generator is:

```python
import struct

RATIOS = {
    "21:9": 21 / 9,
    "20:9": 20 / 9,
    "19.5:9": 19.5 / 9,
    "19:9": 19 / 9,
    "18.5:9": 18.5 / 9,
    "18:9": 18 / 9,
    "16:9": 16 / 9,
    "16:10": 16 / 10,
    "4:3": 4 / 3,
}

for name, ratio in RATIOS.items():
    bits = struct.unpack(">I", struct.pack(">f", ratio))[0]

    upper = (bits >> 16) & 0xFFFF
    lower = bits & 0xFFFF

    # Preserve Tekken 6's original register/instruction pattern:
    # lui $at, upper
    # ori $at, $at, lower
    lui = 0x3C010000 | upper
    ori = 0x34210000 | lower

    print(
        f"{name:7} "
        f"float=0x{bits:08X} "
        f"lui=0x{lui:08X} "
        f"ori=0x{ori:08X}"
    )
```

For the ratios included in this project, that produces:

| Ratio | Decimal value | IEEE-754 | `lui` | `ori` |
| --- | ---: | --- | --- | --- |
| 21:9 | 2.3333333 | `0x40155555` | `0x3C014015` | `0x34215555` |
| 20:9 | 2.2222223 | `0x400E38E4` | `0x3C01400E` | `0x342138E4` |
| 19.5:9 | 2.1666667 | `0x400AAAAB` | `0x3C01400A` | `0x3421AAAB` |
| 19:9 | 2.1111112 | `0x40071C72` | `0x3C014007` | `0x34211C72` |
| 18.5:9 | 2.0555556 | `0x40038E39` | `0x3C014003` | `0x34218E39` |
| 18:9 / 2:1 | 2.0000000 | `0x40000000` | `0x3C014000` | `0x34210000` |
| 16:9 | 1.7777778 | `0x3FE38E39` | `0x3C013FE3` | `0x34218E39` |
| 16:10 | 1.6000000 | `0x3FCCCCCD` | `0x3C013FCC` | `0x3421CCCD` |
| 4:3 | 1.3333334 | `0x3FAAAAAB` | `0x3C013FAA` | `0x3421AAAB` |

These are the values in the released cheat.

## 7. Example: deriving the 20:9 patch

Take 20:9:

```text
20 / 9 = 2.2222222...
IEEE-754 = 0x400E38E4
```

Split the float bits into upper and lower halves:

```text
upper = 0x400E
lower = 0x38E4
```

Substitute those into the same instruction structure used by the original code:

```asm
lui  $at, 0x400E
ori  $at, $at, 0x38E4
```

Machine code:

```text
3C01400E
342138E4
```

The final 20:9 entry writes those words to all four confirmed projection paths:

```text
_L 0x20145F10 0x3C01400E
_L 0x20145F14 0x342138E4

_L 0x20146794 0x3C01400E
_L 0x20146798 0x342138E4

_L 0x20146BC8 0x3C01400E
_L 0x20146BCC 0x342138E4

_L 0x20147D90 0x3C01400E
_L 0x20147D94 0x342138E4
```

### 21:9 example

```text
21 / 9 = 2.3333333
IEEE-754 = 0x40155555

upper = 0x4015
lower = 0x5555
```

Which becomes:

```text
3C014015
34215555
```

These are the exact instruction values used by the released 21:9 entry.

## 8. Convert confirmed runtime addresses into CWCheat writes

For simple CWCheat patches, type `2` is a 32-bit write.

When working from PSP user memory, CWCheat addresses are represented as offsets from `0x08800000`:

```text
cwcheat_offset = psp_address - 0x08800000
```

For example:

```text
PSP address:    0x08945F10
CWCheat offset: 0x00145F10
```

A 32-bit write of `0x3C01400E` becomes:

```text
_L 0x20145F10 0x3C01400E
```

The leading `2` denotes the 32-bit write type; it is not part of the underlying offset.

This conversion should only be done after the EBOOT candidate has been mapped to and verified at its actual runtime PSP address.

## 9. Verify that the result is a real projection correction

A value changing the image is not enough to prove that the correct parameter has been found.

Testing is done with PPSSPP's **Stretch** option enabled so the PSP framebuffer fills the target display. The cheat then corrects the game's internal 3D projection for the same shape.

A good result should:

- restore normal character and world proportions instead of leaving a horizontally stretched image
- reveal more horizontal 3D scene content as the target ratio becomes wider
- behave consistently across the gameplay states using the patched paths
- return cleanly to the original presentation when the 16:9 instructions are restored

Testing several mathematically related ratios is also useful as a sanity check. If the patched value really is an aspect-ratio parameter, moving from 4:3 through 16:9, 2:1, 20:9, and 21:9 should produce a predictable progression rather than unrelated visual effects.

## Why PPSSPP Stretch is still required

The cheat changes the game's internal 3D projection constant. It does not itself resize PPSSPP's output surface.

The intended combination is therefore:

```text
PPSSPP Stretch
+
matching aspect-ratio CWCheat
```

Stretch fills the display; the cheat corrects the 3D projection for that shape.

## HUD limitation

The original 2D HUD and menus are separate from the 3D projection paths described above. Correcting the 3D aspect ratio does not independently reposition or rescale those UI elements.

That is why the released patch fixes the 3D presentation while retaining the documented HUD/menu limitation.

A complete HUD fix would be a separate reverse-engineering task involving the game's 2D rendering, sprite coordinates, scaling, or orthographic projection logic.

## Camera patch is separate

The camera presets in `ULUS10466.ini` are not part of the aspect-ratio calculation above.

They write a separate 16-bit value at CWCheat offset:

```text
0x0015350C
```

The released presets are:

```text
Original        0x3F80
Slightly Wider  0x3F81
Wider           0x3F82
Widest          0x3F83
```

This changes gameplay framing independently of the projection correction. It should be treated as a separate camera adjustment rather than as part of the ultrawide aspect-ratio formula.

## Reproducing the method for another PSP game

The Tekken 6 process can be generalized, but the exact code structure will vary from game to game.

A practical workflow is:

1. Identify the game's normal aspect ratio and calculate its expected IEEE-754 float.
2. Obtain a decrypted `EBOOT.BIN` for static analysis.
3. Inspect the executable's segment layout so file offsets can later be mapped correctly into PSP virtual memory.
4. Use Python to scan aligned MIPS instructions for patterns that construct plausible aspect-ratio floats instead of relying only on a raw-byte search.
5. Rank or filter candidates by closeness to common ratios such as 4:3, 16:10, or 16:9.
6. Record candidate EBOOT offsets, instruction words, and surrounding code.
7. Map promising EBOOT candidates to their loaded PSP addresses and verify the same instructions in PPSSPP memory/disassembly.
8. Generate an obvious temporary replacement ratio, such as 2:1, while preserving the original instruction/register structure.
9. Test candidates in PPSSPP and observe whether the 3D projection changes correctly.
10. Test across multiple gameplay/rendering states to find every path that must be patched.
11. Once the projection paths are confirmed, use Python to generate exact IEEE-754 target values and replacement MIPS instructions.
12. Convert the confirmed runtime PSP addresses into CWCheat offsets using the correct memory base and write type.
13. Test several ratios and restoration values to confirm predictable behavior.
14. Treat HUD scaling, culling, camera distance, FMVs, and other rendering issues as separate reverse-engineering problems unless testing shows they share the same code path.

Some games will be easier and store a normal float directly in writable data. Others may use `lui` plus another instruction, separate X/Y scale constants, matrix coefficients, values regenerated every frame, or entirely different projection logic.

The Python scanner should therefore be treated as a way to find and rank strong candidates, not as proof that a match is the game's aspect-ratio control. In-game validation is still required.

## Useful references

- PPSSPP process-hacking reference: https://www.ppsspp.org/docs/reference/process-hacks/
- PPSSPP CWCheat syntax discussion explaining the `0x08800000` base and 32-bit type-2 writes: https://forums.ppsspp.org/showthread.php?tid=25041
- Community PSP cheat-creation documentation: https://github.com/raing3/psp-cheat-documentation

## Final result

The Tekken 6 ultrawide patch can be reproduced through this workflow:

```text
decrypted EBOOT.BIN
        ↓
Python scans MIPS code for instructions constructing plausible ratio floats
        ↓
identify candidate 0x3FE38E39 / 16:9 instruction paths
        ↓
map EBOOT candidates to runtime PSP addresses
        ↓
test replacements in PPSSPP
        ↓
confirm the four relevant projection paths
        ↓
generate exact target float + MIPS values with Python
        ↓
convert confirmed runtime addresses to CWCheat entries
        ↓
validate multiple ratios in-game
```

For Tekken 6, the confirmed original projection constant is:

```text
0x3FE38E39
```

and the relevant code reconstructs it as:

```text
3C013FE3
34218E39
```

Replacing those immediate values with the IEEE-754 representation of the target `width / height` ratio produces the aspect-ratio entries in `ULUS10466.ini`.

The released cheat patches all four confirmed projection paths and keeps the camera adjustment separate.
