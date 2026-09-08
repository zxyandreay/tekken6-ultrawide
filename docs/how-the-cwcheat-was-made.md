# How the Tekken 6 Ultrawide CWCheat Was Made

This document records the development process behind the aspect-ratio and camera portions of this project's Tekken 6 CWCheat for the USA release (`ULUS10466`). It also explains how the original 20:9 patch evolved into the multi-ratio version currently published in this repository.

## Original target

The first working patch was built around a specific target setup:

```text
Game:       Tekken 6
Region:     USA
Game ID:    ULUS10466
Display:    2400 x 1080
Aspect:     20:9
Emulator:   PPSSPP
```

The goal was not simply to fill a 20:9 screen. PPSSPP can already stretch the PSP framebuffer to do that.

The actual goal was:

> Make Tekken 6 calculate a wider 3D projection so the world gains horizontal view while characters and geometry keep the correct proportions.

The 2D HUD was allowed to remain stretched if correcting it independently proved unstable.

---

## 1. Calculate the target aspect ratio

For a 2400 x 1080 display:

```text
2400 / 1080
= 2.222222222...
= 20 / 9
```

As an IEEE-754 single-precision float:

```text
20:9
2.2222223
0x400E38E4
```

The original mathematical 16:9 value is:

```text
16:9
1.7777778
0x3FE38E39
```

These two values became the important signatures for the first patch:

```text
Original 16:9:  0x3FE38E39
Target 20:9:    0x400E38E4
```

---

## 2. Inspect the game executable

A decrypted/original `EBOOT.BIN` was used to inspect Tekken 6's PSP/MIPS executable code.

The useful discovery was that the game did not expose one convenient writable aspect-ratio float in a data table. The relevant projection code constructs the 16:9 value directly in MIPS instructions.

The original value:

```text
0x3FE38E39
```

is split into:

```text
upper = 0x3FE3
lower = 0x8E39
```

and reconstructed by:

```asm
lui  $at, 0x3FE3
ori  $at, $at, 0x8E39
```

Machine code:

```text
3C013FE3
34218E39
```

Together those two instructions construct:

```text
0x3FE38E39
= 1.7777778
≈ 16:9
```

That was the key 3D projection finding.

### EBOOT offsets and runtime addresses

When working from an `EBOOT.BIN`, a file offset is not automatically a PSP virtual address or a CWCheat offset.

The practical relationship is:

```text
EBOOT location
      ↓
map/locate the same code in loaded PSP memory
      ↓
runtime PSP address
      ↓
CWCheat offset
```

The released CWCheat offsets discussed below are the final confirmed locations used by the patch. They should not be assumed to be literal `EBOOT.BIN` file offsets.

---

## 3. Find every relevant 16:9 projection load

The same 16:9 construction appeared in four relevant projection locations.

The confirmed CWCheat offsets are:

```text
0x00145F10 / 0x00145F14
0x00146794 / 0x00146798
0x00146BC8 / 0x00146BCC
0x00147D90 / 0x00147D94
```

Using the PSP user-memory base `0x08800000`, the corresponding runtime PSP addresses are:

```text
0x08945F10 / 0x08945F14
0x08946794 / 0x08946798
0x08946BC8 / 0x08946BCC
0x08947D90 / 0x08947D94
```

At the original 16:9 setting, every pair reconstructs the same constant:

```text
3C013FE3
34218E39
```

Finding all four was important. Changing only one occurrence could leave other rendering or camera/projection paths at the stock value.

---

## 4. Convert 20:9 into equivalent MIPS instructions

The target 20:9 float is:

```text
0x400E38E4
```

Split it into upper and lower 16-bit halves:

```text
upper = 0x400E
lower = 0x38E4
```

Preserve the original instruction structure and replace only the constant:

```asm
lui  $at, 0x400E
ori  $at, $at, 0x38E4
```

Machine code:

```text
3C01400E
342138E4
```

Comparison:

```text
Original 16:9
3C013FE3
34218E39

20:9
3C01400E
342138E4
```

The surrounding game logic remains unchanged. Only the value being constructed is replaced.

That small, targeted change is one reason the final 3D patch proved stable.

---

## 5. Convert the projection changes into CWCheat writes

CWCheat type `2` performs a 32-bit write.

The first 20:9 replacement is:

```text
_L 0x20145F10 0x3C01400E
_L 0x20145F14 0x342138E4
```

The same replacement is applied to the remaining three confirmed paths:

```text
_L 0x20146794 0x3C01400E
_L 0x20146798 0x342138E4

_L 0x20146BC8 0x3C01400E
_L 0x20146BCC 0x342138E4

_L 0x20147D90 0x3C01400E
_L 0x20147D94 0x342138E4
```

That was the original stable 20:9 projection patch.

---

## 6. Why PPSSPP Stretch is still required

Changing the game's internal projection does not change the size of the PSP framebuffer itself.

PPSSPP therefore still needs to scale that framebuffer to fill the physical display.

Without the cheat:

```text
16:9 game projection
        ↓
PPSSPP Stretch
        ↓
20:9 display
        ↓
horizontally distorted 3D
```

With the cheat:

```text
20:9 game projection
        ↓
normal PSP framebuffer
        ↓
PPSSPP Stretch
        ↓
20:9 display
        ↓
correctly proportioned 3D
```

So the intended setup is:

```text
matching aspect-ratio CWCheat
+
PPSSPP Stretch
```

Stretch fills the display; the cheat corrects the game's 3D projection for that shape.

---

## 7. Verify that the result is true ultrawide

The important test was not whether the screen became full-width. Stretch already guarantees that.

The useful test was whether:

- fighters retained normal proportions
- world geometry retained normal proportions
- additional horizontal scene content became visible
- the result behaved like a wider camera/projection rather than a stretched image

Conceptually:

```text
Original 16:9

      Fighter       Fighter
    |--------------------|

True 20:9

      Fighter       Fighter
|------------------------------|
  more world visible on the sides

Fake stretch

    WIDE Fighter   WIDE Fighter
|------------------------------|
```

That distinction confirmed that the patched values were controlling the 3D projection rather than merely changing output scaling.

---

## 8. Camera framing was handled separately

After widening the projection, camera framing was experimented with independently.

The useful camera CWCheat offset is:

```text
0x0015350C
```

The stock value exposed by the final cheat is:

```text
0x3F80
```

Small increments produced progressively wider framing:

```text
Original        0x3F80
Slightly Wider  0x3F81
Wider           0x3F82
Widest          0x3F83
```

The corresponding CWCheat entries are:

```text
_C0 Original
_L 0x1015350C 0x00003F80

_C0 Slightly Wider
_L 0x1015350C 0x00003F81

_C0 Wider
_L 0x1015350C 0x00003F82

_C0 Widest
_L 0x1015350C 0x00003F83
```

A deliberate design choice was made to keep projection and camera changes separate.

The aspect-ratio entry corrects projection. The camera presets are optional framing choices.

Only one camera preset should be enabled at a time because every preset writes the same address.

---

## 9. HUD correction was investigated separately

Once the 3D projection was correct at 20:9, the remaining obvious issue was the 2D interface.

The 3D scene was corrected, but the following still used the original PSP-oriented 2D layout and became horizontally stretched by PPSSPP Stretch:

- health bars
- round graphics
- battle overlays
- menu elements
- pause-screen graphics
- sprites and text

The ideal target would have been:

```text
+---------------------------------------+
|                                       |
|          original-proportion HUD      |
|        +---------------------+        |
|        | Health       Health |        |
|        |                     |        |
|        +---------------------+        |
|                                       |
|          wider 20:9 3D world          |
+---------------------------------------+
```

Unlike the 3D projection, however, the HUD did not reduce to one clean global aspect-ratio constant.

### Broad rendering experiments

Several broader 2D/sprite rendering paths were tested.

Those experiments caused regressions including effects such as:

- missing pause-screen dark overlays
- rectangular rendering artifacts
- incorrect sprite rendering
- battle HUD corruption

That showed that broad 2D rendering changes were affecting systems beyond the intended HUD scaling.

### Narrower health-bar experiments

More targeted health-bar changes were also attempted.

Those were less destructive, but still did not correct the whole UI assembly consistently. For example, one modification could affect the health-bar fill while leaving its surrounding frame, icons, background, or related elements unchanged.

Conceptually:

```text
Frame:
|====================|

Fill after partial correction:
|============        |
```

Trying to extend the same correction further could cause empty or otherwise incorrect bars.

At that point the difference in stability was clear:

```text
3D projection patch
→ small, predictable, stable

HUD patch
→ spread across multiple rendering paths
→ invasive
→ regression-prone
```

The HUD work was therefore stopped rather than shipping a fragile "complete" fix.

That is why the public patch intentionally corrects the 3D presentation while leaving the original 2D HUD/menu limitation documented.

---

## 10. Restore all experimental HUD changes

Because many executable instructions had been modified while testing HUD approaches, cleanup was treated as a separate step rather than assuming that disabling experimental cheats would return everything to a known-good state.

The original Tekken 6 executable was used as the reference, and **98 executable addresses** touched during the HUD experiments were restored to their original instructions.

Only after returning to that clean baseline were the proven 3D projection and camera changes reapplied.

This was important for two reasons:

1. it removed hidden experimental state from the final result
2. it ensured the public patch was based only on changes that had been deliberately validated

---

## 11. Build the clean initial patch

The first clean final version kept only:

- the proven 20:9 projection patch
- optional camera presets
- no HUD modifications

The 20:9 portion was:

```text
_C0 Screen - 20:9 Ultrawide
_L 0x20145F10 0x3C01400E
_L 0x20145F14 0x342138E4
_L 0x20146794 0x3C01400E
_L 0x20146798 0x342138E4
_L 0x20146BC8 0x3C01400E
_L 0x20146BCC 0x342138E4
_L 0x20147D90 0x3C01400E
_L 0x20147D94 0x342138E4
```

Camera choices remained separate:

```text
_C0 Camera - Original
_L 0x1015350C 0x00003F80

_C0 Camera - Slightly Wider
_L 0x1015350C 0x00003F81

_C0 Camera - Wider
_L 0x1015350C 0x00003F82

_C0 Camera - Widest
_L 0x1015350C 0x00003F83
```

The naming was later simplified when the repository was expanded to support multiple aspect ratios.

---

## 12. Keep an explicit restore option

The original projection instructions were recorded rather than relying on the game to refresh them automatically.

Original 16:9 instructions:

```text
3C013FE3
34218E39
```

Original camera value:

```text
0x3F80
```

The current restore entry is:

```text
_C0 Restore Aspect + Camera
_L 0x20145F10 0x3C013FE3
_L 0x20145F14 0x34218E39
_L 0x20146794 0x3C013FE3
_L 0x20146798 0x34218E39
_L 0x20146BC8 0x3C013FE3
_L 0x20146BCC 0x34218E39
_L 0x20147D90 0x3C013FE3
_L 0x20147D94 0x34218E39
_L 0x1015350C 0x00003F80
```

Having an explicit restore path is safer than assuming that disabling a cheat mid-session will immediately reconstruct every modified instruction.

---

## 13. Generalize the proven 20:9 method to other ratios

Once the four projection paths were proven, supporting additional aspect ratios no longer required finding new projection code.

The same four locations can be reused while changing only the IEEE-754 aspect-ratio constant.

For each ratio:

```text
ratio = width / height
```

Convert that value to IEEE-754 single precision, split it into upper and lower 16-bit halves, then preserve the same MIPS instruction structure:

```asm
lui  $at, upper
ori  $at, $at, lower
```

The current repository contains:

| Ratio | Decimal | IEEE-754 | `lui` | `ori` |
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

Those are the exact values in the current `ULUS10466.ini`.

### Example: 21:9

```text
21 / 9
= 2.3333333
= 0x40155555
```

Split into:

```text
upper = 0x4015
lower = 0x5555
```

Result:

```text
3C014015
34215555
```

The same four projection sites are then patched with those words.

---

## 14. Python as a reproducible analysis helper

The exact helper tooling used during the first discovery pass is not part of this repository. The following Python snippets reproduce the useful analysis steps: identifying MIPS instruction pairs that construct plausible aspect-ratio floats and generating replacement values once a projection path has been confirmed.

### Candidate scanner

For an already decrypted `EBOOT.BIN`, a simple scanner can walk aligned MIPS words and look for a `lui` followed by an `ori` that uses the same register.

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
    word1 = struct.unpack_from("<I", data, offset)[0]
    word2 = struct.unpack_from("<I", data, offset + 4)[0]

    op1 = (word1 >> 26) & 0x3F
    rs1 = (word1 >> 21) & 0x1F
    rt1 = (word1 >> 16) & 0x1F
    imm1 = word1 & 0xFFFF

    op2 = (word2 >> 26) & 0x3F
    rs2 = (word2 >> 21) & 0x1F
    rt2 = (word2 >> 16) & 0x1F
    imm2 = word2 & 0xFFFF

    is_lui = op1 == 0x0F and rs1 == 0
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

This is only a candidate finder. It does not prove that a matching value controls projection.

For better accuracy, restrict analysis to executable sections/segments and inspect surrounding disassembly.

### Ratio/instruction generator

Once a projection path is confirmed, exact replacement instructions can be generated mechanically:

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

    lui = 0x3C010000 | upper
    ori = 0x34210000 | lower

    print(
        f"{name:7} "
        f"float=0x{bits:08X} "
        f"lui=0x{lui:08X} "
        f"ori=0x{ori:08X}"
    )
```

---

## 15. Reusable workflow for another PSP game

The Tekken 6 work suggests the following process for another 3D PSP title.

1. Confirm the exact game ID, region, and revision.
2. Obtain an original/decrypted `EBOOT.BIN`.
3. Determine the game's stock aspect ratio.
4. Calculate its expected IEEE-754 float.
5. Search the executable for:
   - the stock aspect-ratio float
   - instructions constructing that float
   - nearby projection-related constants
6. Disassemble the surrounding MIPS code.
7. Determine whether each candidate belongs to:
   - perspective projection
   - orthographic/UI rendering
   - camera logic
   - unrelated math
8. Identify every 3D projection path that uses the candidate.
9. Map EBOOT candidates to actual runtime PSP addresses before converting them to CWCheat offsets.
10. Test an obvious temporary replacement while preserving the original instruction structure.
11. Verify that characters retain their proportions and more horizontal geometry becomes visible.
12. Test several stages, transitions, replays, effects, and other rendering states.
13. Once confirmed, generate the exact target ratio and MIPS words.
14. Record the original instructions before publishing the patch.
15. Include an explicit restore entry.
16. Treat camera/FOV changes separately from aspect correction.
17. Treat HUD correction as a separate project unless the game exposes a clearly independent HUD transform.

### Use an extreme diagnostic value when useful

For future games, an exaggerated temporary ratio can make candidate validation easier than immediately jumping from 16:9 to a subtle target such as 20:9.

For example, temporarily testing something around `3.5:1` can make it obvious whether a candidate actually controls projection.

If the 3D scene becomes extremely wide while maintaining the expected type of projection change, that is strong evidence that the correct path has been found.

Then replace the diagnostic value with the exact desired ratio.

This is a recommended diagnostic technique for future work; it is not required by the released Tekken 6 patch itself.

---

## Why this works better for 3D than for HUD/UI

A conventional 3D renderer ultimately needs projection parameters equivalent to concepts such as:

```text
field of view
aspect ratio
near plane
far plane
```

Even in lower-level PSP/MIPS code, some representation of that projection math usually has to exist.

That creates identifiable targets such as:

```text
1.7777778
```

or the instructions that construct it.

A 2D UI can instead consist of many unrelated values:

```text
sprite x
sprite width
text x
health bar x
health fill x
overlay quad coordinates
```

There may be no single global HUD aspect-ratio control.

Tekken 6 demonstrated that difference clearly: the 3D projection was corrected with four small instruction pairs, while HUD work spread into multiple rendering systems and produced regressions.

---

## Current repository state

The current public `ULUS10466.ini` is the generalized version of the original 20:9 work.

It contains:

- nine selectable aspect ratios from 4:3 through 21:9
- the same four confirmed 3D projection paths for every ratio
- four optional camera presets
- an explicit restore option
- no experimental HUD modifications

The core discovery remains the same:

```text
Original 16:9 float
0x3FE38E39

MIPS construction
3C013FE3
34218E39
```

Changing only those immediate values to the IEEE-754 representation of another `width / height` ratio produces the aspect-ratio entries in the released cheat.

The most important development lesson was also simple:

```text
find the 3D projection constant
        ↓
verify every relevant path
        ↓
replace the stock 16:9 value
with the exact target ratio
        ↓
validate the wider 3D result
        ↓
leave unrelated rendering systems alone
unless they can be corrected independently and safely
```

---

## Useful references

- PPSSPP process-hacking reference: https://www.ppsspp.org/docs/reference/process-hacks/
- PPSSPP CWCheat syntax discussion: https://forums.ppsspp.org/showthread.php?tid=25041
- Community PSP cheat-creation documentation: https://github.com/raing3/psp-cheat-documentation
