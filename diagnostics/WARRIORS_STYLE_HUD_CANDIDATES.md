# Warriors-style HUD candidate ranking

This report is a heuristic ranking, not proof of HUD ownership. It intentionally favors functions that combine PSP-sized screen constants with floating-point/render-state setup, while penalizing the A/B/C orthographic paths that produced no visible change and the broad viewport path that historically broke overlays.

## 1. `0x08AA62D8`–`0x08AA655C` — score 64
- size: `0x284` bytes
- screen constants: `480.0` @ `0x08AA6314`, `272.0` @ `0x08AA6330`, `480.0` @ `0x08AA63B8`, `272.0` @ `0x08AA63D0`, `480.0` @ `0x08AA64C0`, `272.0` @ `0x08AA64E0`
- `swc1`: 27; `lwc1`: 16; COP1 instructions: 37
- direct calls: 6
  - `0x08AA6364` -> `0x08ACE1E0`
  - `0x08AA6370` -> `0x08ADB6A8`
  - `0x08AA6404` -> `0x08ACE1E0`
  - `0x08AA6410` -> `0x08ADB6A8`
  - `0x08AA6504` -> `0x08ACE1E0`
  - `0x08AA6510` -> `0x08ADB6A8`

## 2. `0x08A3916C`–`0x08A396D8` — score 62
- size: `0x56C` bytes
- screen constants: `480.0` @ `0x08A39288`, `272.0` @ `0x08A3929C`, `480.0` @ `0x08A392F4`, `272.0` @ `0x08A39308`, `480.0` @ `0x08A39360`, `272.0` @ `0x08A3936C`
- `swc1`: 50; `lwc1`: 7; COP1 instructions: 59
- direct calls: 13
  - `0x08A39194` -> `0x08ACE1F8`
  - `0x08A391A0` -> `0x08ACE1E0`
  - `0x08A391C0` -> `0x08ADB6A8`
  - `0x08A391E4` -> `0x08ACE178`
  - `0x08A39230` -> `0x08ADB6A8`
  - `0x08A39474` -> `0x08ACE1F8`
  - `0x08A39480` -> `0x08ACE1E0`
  - `0x08A3949C` -> `0x08ACE178`
  - `0x08A394EC` -> `0x08ADB6A8`
  - `0x08A39594` -> `0x08ACE1F8`
  - `0x08A395A0` -> `0x08ACE1E0`
  - `0x08A395B8` -> `0x08ACE178`

## 3. `0x08A39080`–`0x08A3916C` — score 41
- size: `0xEC` bytes
- screen constants: `480.0` @ `0x08A390F4`, `272.0` @ `0x08A39108`
- `swc1`: 12; `lwc1`: 0; COP1 instructions: 4
- direct calls: 2
  - `0x08A39094` -> `0x0885F528`
  - `0x08A390C0` -> `0x0885F17C`

## 4. `0x089B0740`–`0x089B0984` — score 39
- size: `0x244` bytes
- screen constants: `480.0` @ `0x089B07F0`
- `swc1`: 15; `lwc1`: 2; COP1 instructions: 15
- direct calls: 8
  - `0x089B0778` -> `0x08868904`
  - `0x089B07E8` -> `0x08ACE1E0`
  - `0x089B0824` -> `0x08ACE178`
  - `0x089B087C` -> `0x08ACE1E0`
  - `0x089B0890` -> `0x08ACE178`
  - `0x089B0904` -> `0x08868850`
  - `0x089B0928` -> `0x08868850`
  - `0x089B0950` -> `0x08868850`

## 5. `0x0882EED4`–`0x0882F03C` — score 31
- size: `0x168` bytes
- screen constants: `480.0` @ `0x0882EF7C`
- `swc1`: 19; `lwc1`: 0; COP1 instructions: 12
- direct calls: 0

## 6. `0x08993AD4`–`0x08993E50` — score 31
- size: `0x37C` bytes
- screen constants: `256.0` @ `0x08993D48`
- `swc1`: 15; `lwc1`: 4; COP1 instructions: 8
- direct calls: 11
  - `0x08993B4C` -> `0x0888ABF4`
  - `0x08993B58` -> `0x0885EDF4`
  - `0x08993BA4` -> `0x0885F3E0`
  - `0x08993BE4` -> `0x0899541C`
  - `0x08993BF0` -> `0x0899522C`
  - `0x08993C40` -> `0x0885F3E0`
  - `0x08993C84` -> `0x0885F3E0`
  - `0x08993CCC` -> `0x0885EDB4`
  - `0x08993CE4` -> `0x0885F3E0`
  - `0x08993DF0` -> `0x08B7A3BC`
  - `0x08993E40` -> `0x08ADB6A8`

## 7. `0x08840C6C`–`0x08840F58` — score 29
- size: `0x2EC` bytes
- screen constants: `256.0` @ `0x08840D74`
- `swc1`: 9; `lwc1`: 18; COP1 instructions: 43
- direct calls: 6
  - `0x08840CC4` -> `0x0885C3F4`
  - `0x08840CE0` -> `0x0885FA44`
  - `0x08840CF8` -> `0x0885C8A0`
  - `0x08840D00` -> `0x0885EDF4`
  - `0x08840DB8` -> `0x0885A1E8`
  - `0x08840F48` -> `0x0885EDB4`

## 8. `0x089AEF50`–`0x089AF398` — score 29
- size: `0x448` bytes
- screen constants: `480.0` @ `0x089AF044`
- `swc1`: 3; `lwc1`: 3; COP1 instructions: 46
- direct calls: 7
  - `0x089AF0EC` -> `0x088968DC`
  - `0x089AF11C` -> `0x088968DC`
  - `0x089AF17C` -> `0x0896DFF8`
  - `0x089AF18C` -> `0x0896DFF8`
  - `0x089AF198` -> `0x08970390`
  - `0x089AF1BC` -> `0x088968DC`
  - `0x089AF200` -> `0x088968DC`

## 9. `0x08946390`–`0x0894650C` — score 28
- size: `0x17C` bytes
- screen constants: `480.0` @ `0x089463C4`, `272.0` @ `0x089463CC`
- `swc1`: 0; `lwc1`: 0; COP1 instructions: 29
- direct calls: 6
  - `0x089463B8` -> `0x0895540C`
  - `0x089463E0` -> `0x08ACE178`
  - `0x0894642C` -> `0x08AC5BA8`
  - `0x08946448` -> `0x08946390`
  - `0x08946480` -> `0x08AC5BA8`
  - `0x089464B8` -> `0x08AC5BA8`
- PENALTY: broad viewport/surface state

## 10. `0x089933C8`–`0x08993510` — score 27
- size: `0x148` bytes
- screen constants: `256.0` @ `0x08993470`
- `swc1`: 14; `lwc1`: 3; COP1 instructions: 15
- direct calls: 2
  - `0x089933F8` -> `0x08B7A3BC`
  - `0x08993498` -> `0x08ADB6A8`

## 11. `0x089B3F44`–`0x089B4270` — score 27
- size: `0x32C` bytes
- screen constants: `272.0` @ `0x089B404C`
- `swc1`: 6; `lwc1`: 6; COP1 instructions: 31
- direct calls: 2
  - `0x089B401C` -> `0x088968DC`
  - `0x089B4158` -> `0x088968DC`

## 12. `0x08993E50`–`0x08993F9C` — score 26
- size: `0x14C` bytes
- screen constants: `256.0` @ `0x08993F48`
- `swc1`: 13; `lwc1`: 2; COP1 instructions: 16
- direct calls: 2
  - `0x08993EC8` -> `0x08B7A3BC`
  - `0x08993F70` -> `0x08ADB6A8`

## 13. `0x08841168`–`0x0884142C` — score 25
- size: `0x2C4` bytes
- screen constants: `256.0` @ `0x088412D8`
- `swc1`: 4; `lwc1`: 14; COP1 instructions: 47
- direct calls: 7
  - `0x088411C0` -> `0x0885A384`
  - `0x088411DC` -> `0x089E63F4`
  - `0x088411F0` -> `0x0884022C`
  - `0x088411F8` -> `0x0885C858`
  - `0x08841250` -> `0x0885A1E8`
  - `0x088413E0` -> `0x0885A158`
  - `0x08841400` -> `0x08A5C498`

## 14. `0x08840F58`–`0x08841168` — score 24
- size: `0x210` bytes
- screen constants: `256.0` @ `0x08840FD8`
- `swc1`: 9; `lwc1`: 18; COP1 instructions: 43
- direct calls: 1
  - `0x0884101C` -> `0x0885A1E8`

## 15. `0x088C0AAC`–`0x088C0DD8` — score 24
- size: `0x32C` bytes
- screen constants: `256.0` @ `0x088C0C0C`
- `swc1`: 4; `lwc1`: 8; COP1 instructions: 23
- direct calls: 7
  - `0x088C0ABC` -> `0x088C12D8`
  - `0x088C0B74` -> `0x08946ABC`
  - `0x088C0BE8` -> `0x08AC5130`
  - `0x088C0C28` -> `0x08AC43F8`
  - `0x088C0C78` -> `0x08AC43F8`
  - `0x088C0D18` -> `0x08AC43F8`
  - `0x088C0D58` -> `0x08825ECC`

## 16. `0x0883FCF8`–`0x0883FF70` — score 19
- size: `0x278` bytes
- screen constants: `256.0` @ `0x0883FE24`
- `swc1`: 0; `lwc1`: 9; COP1 instructions: 43
- direct calls: 5
  - `0x0883FD28` -> `0x0885A148`
  - `0x0883FD6C` -> `0x0885A3F8`
  - `0x0883FD88` -> `0x08841A90`
  - `0x0883FD90` -> `0x08842538`
  - `0x0883FD98` -> `0x0884245C`

## 17. `0x08806C64`–`0x08806E94` — score 18
- size: `0x230` bytes
- screen constants: `240.0` @ `0x08806E28`
- `swc1`: 4; `lwc1`: 1; COP1 instructions: 17
- direct calls: 1
  - `0x08806C74` -> `0x08B7B600`

## 18. `0x08AC3DD0`–`0x08AC4CB4` — score 18
- size: `0xEE4` bytes
- screen constants: `512.0` @ `0x08AC4340`
- `swc1`: 8; `lwc1`: 32; COP1 instructions: 86
- direct calls: 0

## 19. `0x088643A4`–`0x08864608` — score 16
- size: `0x264` bytes
- screen constants: `480.0` @ `0x08864494`, `272.0` @ `0x0886449C`
- `swc1`: 0; `lwc1`: 0; COP1 instructions: 7
- direct calls: 28
  - `0x088643D8` -> `0x08868CEC`
  - `0x088643F0` -> `0x08868748`
  - `0x08864400` -> `0x08AAB590`
  - `0x08864418` -> `0x08954B20`
  - `0x08864424` -> `0x089C97B0`
  - `0x08864430` -> `0x089C99A8`
  - `0x08864454` -> `0x0886BD28`
  - `0x0886446C` -> `0x08864104`
  - `0x0886447C` -> `0x089C97B0`
  - `0x08864488` -> `0x089CA6BC`
  - `0x088644B8` -> `0x08ACA990`
  - `0x088644D4` -> `0x08ACAB14`
- PENALTY: ortho Path C: user-visible no-op

## 20. `0x088E7810`–`0x088E7E20` — score 15
- size: `0x610` bytes
- screen constants: `512.0` @ `0x088E7B2C`
- `swc1`: 2; `lwc1`: 8; COP1 instructions: 49
- direct calls: 3
  - `0x088E784C` -> `0x0880468C`
  - `0x088E78E4` -> `0x0880468C`
  - `0x088E7CB4` -> `0x0880468C`

## Interpretation

- The Warriors fix succeeded because it found a HUD-specific scale operand separate from the 3D aspect operand. These Tekken candidates should be investigated for the same kind of live screen-space scale/aspect value.
- Do not patch every 480/272 occurrence. Trace data flow and caller ownership first.
- Full-screen overlays/fades may require exclusion or caller-aware handling even if they share a sprite submission family.
