# Baseline

Last updated: 2026-09-03

## Target

- Game: Tekken 6
- Region: USA
- Game ID: ULUS10466
- Target emulator: PPSSPP
- Primary target device: POCO F5
- Primary display resolution: 2400x1080
- Primary display aspect ratio: 20:9, approximately 2.222222
- Expected PPSSPP display layout for user testing: Stretch

## Local Reference Files

These files are present in the local working folder.

| File | Size | SHA-256 | Repository status |
| --- | ---: | --- | --- |
| `Tekken 6 (USA) (En,Ja,Fr,De,Es,It,Ko,Ru).iso` | 855638016 bytes | `45E9EAA105AFDA7C44204909E7FA22321236C89158BD7D26B52ABA2F2E0794C8` | Must remain ignored; never commit |
| `ULUS10466_EBOOT.BIN` | 4158480 bytes | `E0ED418952C51032796EBC54584592A9F6075495229F6D12D5065F3186BCB55F` | Trackable reference executable |
| `ULUS10466.ini` | 719 bytes | `C82619333B621B22ACD86A23F595FC344CC181879F4D963E381D45C10E1C4D77` | Trackable known-good cheat config |

## EBOOT Verification

VERIFIED:

- `ULUS10466_EBOOT.BIN` begins with an ELF magic header, not an encrypted `~PSP` header.
- ELF class: 32-bit.
- Data encoding: little-endian.
- ELF type: `0x0002` (`ET_EXEC`).
- Machine: `0x0008` (MIPS).
- Entry point: `0x08804124`.
- Program header offset: `0x00000034`.
- Section header offset: `0x00000000`.
- ELF flags: `0x10A23001`.
- Program header count: 1.
- Section header count: 0.
- Static MIPS analysis should be possible, but the binary appears stripped because no section headers are present.

VERIFIED load segment:

| Field | Value |
| --- | --- |
| Type | `0x00000001` (`PT_LOAD`) |
| File offset | `0x00001018` |
| Virtual address | `0x08804018` |
| Physical address | `0x00386740` |
| File size | `0x003F62A8` |
| Memory size | `0x0045F02C` |
| Flags | `0x00000007` |
| Alignment | `0x00001000` |

## Known Working Cheat Baseline

`ULUS10466.ini` currently contains one known-good 20:9 3D aspect patch, four camera options, and a restore code.

Known 20:9 3D patch:

```ini
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

VERIFIED from the cheat data:

- Each pair writes `lui at, 0x400E` followed by `ori at, at, 0x38E4`.
- Together the pair constructs `0x400E38E4`.
- Interpreted as a 32-bit float, `0x400E38E4` is approximately `2.2222223`, matching 20:9.

Known restore/original 3D constant:

```ini
_L 0x20145F10 0x3C013FE3
_L 0x20145F14 0x34218E39
_L 0x20146794 0x3C013FE3
_L 0x20146798 0x34218E39
_L 0x20146BC8 0x3C013FE3
_L 0x20146BCC 0x34218E39
_L 0x20147D90 0x3C013FE3
_L 0x20147D94 0x34218E39
```

VERIFIED from the cheat data:

- The restore pairs construct `0x3FE38E39`.
- Interpreted as a 32-bit float, `0x3FE38E39` is approximately `1.7777778`, matching 16:9.

Known optional camera address, not part of the initial plugin scope:

| CWCheat address | Value | Label |
| --- | --- | --- |
| `0x1015350C` | `0x00003F80` | Original |
| `0x1015350C` | `0x00003F81` | Slightly Wider |
| `0x1015350C` | `0x00003F82` | Wider |
| `0x1015350C` | `0x00003F83` | Widest |

## Current Assumptions

HYPOTHESIS:

- The four 3D patch sites are related to aspect/projection setup.
- They may represent different rendering modes or callers, but this is not yet mapped.
- HUD correction probably requires a higher-level screen-space transform rather than individual sprite patching.

REJECTED for initial work:

- Modifying the ISO.
- Committing extracted game assets.
- Integrating the camera patch before 3D and HUD behavior are understood.
- Patching broad/global HUD constants without tracing usage.
