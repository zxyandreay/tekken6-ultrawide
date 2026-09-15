.set noreorder

.text
.align 2
.globl tekken6_hud_slot_builder_wrapper
.ent tekken6_hud_slot_builder_wrapper
tekken6_hud_slot_builder_wrapper:
    addiu   $sp, $sp, -0x40
    sw      $ra, 0x3C($sp)
    sw      $a0, 0x00($sp)
    sw      $a1, 0x04($sp)
    sw      $a2, 0x08($sp)
    sw      $a3, 0x0C($sp)
    sw      $t0, 0x10($sp)
    sw      $t1, 0x14($sp)
    sw      $t2, 0x18($sp)
    sw      $t3, 0x1C($sp)
    swc1    $f12, 0x20($sp)

    li      $t4, 0xEF
    bne     $a1, $t4, 1f
    nop
    lui     $t4, %hi(tekken6_hud_shell_depth)
    addiu   $t4, $t4, %lo(tekken6_hud_shell_depth)
    lw      $t5, 0($t4)
    addiu   $t5, $t5, 1
    sw      $t5, 0($t4)

1:
    lw      $a0, 0x00($sp)
    lw      $a1, 0x04($sp)
    lw      $a2, 0x08($sp)
    lw      $a3, 0x0C($sp)
    lw      $t0, 0x10($sp)
    lw      $t1, 0x14($sp)
    lw      $t2, 0x18($sp)
    lw      $t3, 0x1C($sp)
    lwc1    $f12, 0x20($sp)
    jal     0x0892D9F8
    nop

    lw      $t4, 0x04($sp)
    li      $t5, 0xEF
    bne     $t4, $t5, 2f
    nop
    lui     $t4, %hi(tekken6_hud_shell_depth)
    addiu   $t4, $t4, %lo(tekken6_hud_shell_depth)
    lw      $t5, 0($t4)
    addiu   $t5, $t5, -1
    sw      $t5, 0($t4)

2:
    lw      $ra, 0x3C($sp)
    jr      $ra
    addiu   $sp, $sp, 0x40
.end tekken6_hud_slot_builder_wrapper

.align 2
.globl tekken6_hud_rect_hook
.ent tekken6_hud_rect_hook
tekken6_hud_rect_hook:
    lui     $t4, %hi(tekken6_hud_shell_depth)
    addiu   $t4, $t4, %lo(tekken6_hud_shell_depth)
    lw      $t4, 0($t4)
    move    $t6, $t4
    nop

    /* Exact long HP shell shape, including a later same-shape overlay that is
     * submitted after the slot-0xEF depth scope has closed. */
    li      $t4, 5
    bne     $a3, $t4, 3f
    nop
    li      $t4, 256
    bne     $t0, $t4, 3f
    nop
    li      $t4, 32
    bne     $t1, $t4, 3f
    nop
    li      $t4, 256
    bne     $t2, $t4, 3f
    nop
    li      $t4, 32
    bne     $t3, $t4, 3f
    nop

    li      $t4, -21
    beq     $a2, $t4, 4f
    nop
    li      $t4, 501
    beq     $a2, $t4, 5f
    nop

3:
    bne     $t6, $zero, 8f
    nop

    /* The newly earned round orb sprite is submitted again after the
     * slot-0xEF scope closes.  Match only the 16x16 y=27 orb slots on either
     * side so it follows the same CENTER transform as the rail and persistent
     * lit orbs.  The separate rotated winner-orb glow is not handled here. */
    li      $t4, 27
    bne     $a3, $t4, 1f
    nop
    li      $t4, 16
    bne     $t0, $t4, 1f
    nop
    bne     $t1, $t4, 1f
    nop
    bne     $t2, $t4, 1f
    nop
    bne     $t3, $t4, 1f
    nop

    slti    $t4, $a2, 150
    bne     $t4, $zero, 1f
    nop
    slti    $t4, $a2, 207
    bne     $t4, $zero, 8f
    nop
    /* Neutral round-win capture proved P2's first late orb starts at x=273.
     * Include it; the previous lower bound of 274 skipped exactly that slot. */
    slti    $t4, $a2, 273
    bne     $t4, $zero, 1f
    nop
    slti    $t4, $a2, 311
    beq     $t4, $zero, 1f
    nop

8:

    /* Preserve authored side ownership for the y=10 player/rank panels.
     * Round markers at y=27 remain tied to the protected center/HP endpoints. */

    move    $t5, $a2
    li      $t4, 4
    mult    $a2, $t4
    mflo    $a2
    li      $t4, 5
    div     $a2, $t4
    mflo    $a2

    li      $t4, 10
    beq     $a3, $t4, 6f
    nop
    /* +49 balances the integer-truncated center family around x=240. */
    addiu   $a2, $a2, 49
    b       7f
    nop

6:
    slti    $t4, $t5, 240
    bne     $t4, $zero, 7f
    nop
    addiu   $a2, $a2, 96

7:

    li      $t4, 4
    mult    $t0, $t4
    mflo    $t0
    li      $t4, 5
    div     $t0, $t4
    mflo    $t0

    b       1f
    nop

4:
    li      $a2, -17
    li      $t0, 253
    b       1f
    nop

5:
    li      $a2, 497
    li      $t0, 253

1:
    j       0x08AB9380
    nop
.end tekken6_hud_rect_hook

.align 2
.globl tekken6_hud_gauge_draw_hook
.ent tekken6_hud_gauge_draw_hook
tekken6_hud_gauge_draw_hook:
    /* Both proven layer sites pass gauge + 0x84 in t1. */
    lw      $t4, -0x28($t1)
    sltiu   $t5, $t4, 2
    beq     $t5, $zero, 1f
    nop

    lui     $t5, %hi(tekken6_hud_fill_coords)
    addiu   $t5, $t5, %lo(tekken6_hud_fill_coords)
    sll     $t4, $t4, 3
    addu    $t5, $t5, $t4

    lwc1    $f0, 0x00($t1)
    lwc1    $f1, 0x04($t1)
    /* Align the fixed-width fill with the uniformly remapped shell interior. */
    li      $t4, 0x3FA71E44       /* 1.3056111f */
    mtc1    $t4, $f2
    lw      $t4, -0x28($t1)
    beq     $t4, $zero, 2f
    nop
    neg.s   $f2, $f2
2:
    add.s   $f0, $f0, $f2
    swc1    $f0, 0x00($t5)
    swc1    $f1, 0x04($t5)
    move    $t1, $t5

    li      $t4, 0x3F8650F4       /* 1.0493455f */
    mtc1    $t4, $f0
    mul.s   $f12, $f12, $f0

1:
    /* Preserve jal and tail-j return semantics at both patched owner sites. */
    j       0x08928FF4
    nop
.end tekken6_hud_gauge_draw_hook

.align 2
.globl tekken6_hud_side_strip_hook
.ent tekken6_hud_side_strip_hook
tekken6_hud_side_strip_hook:
    /* Mirrored y=22 256x32 packets own the translucent under-bar strips;
     * mirrored y=56 64x32 packets own the player rank badges. */
    lw      $t4, 0x04($a0)
    li      $t5, 0x41B00000       /* 22.0f */
    beq     $t4, $t5, 4f
    nop
    li      $t5, 0x42600000       /* 56.0f */
    bne     $t4, $t5, 1f
    nop
    lw      $t4, 0x18($a0)
    li      $t5, 0x42800000       /* 64.0f */
    bne     $t4, $t5, 1f
    nop
    li      $t6, 1
    b       5f
    nop

4:
    lw      $t4, 0x18($a0)
    li      $t5, 0x43800000       /* 256.0f */
    bne     $t4, $t5, 1f
    nop
    move    $t6, $zero
5:
    lw      $t4, 0x1C($a0)
    li      $t5, 0x42000000       /* 32.0f */
    bne     $t4, $t5, 1f
    nop
    lw      $t4, 0x20($a0)
    li      $t5, 0x3F800000       /* +1.0f: P1 */
    beq     $t4, $t5, 8f
    nop
    li      $t5, 0xBF800000       /* -1.0f: P2 */
    bne     $t4, $t5, 1f
    nop
8:
    beq     $t6, $zero, 2f
    nop

    /* Rank badges use the same positive sprite orientation on both sides,
     * so the flip sign cannot identify P2.  Their authored X remains the
     * semantic side discriminator (P1 is < 240, P2 is > 240).  Encode the
     * result as the same sign convention consumed below. */
6:
    lw      $t4, 0x00($a0)
    li      $t5, 0x43700000       /* 240.0f */
    sltu    $t5, $t5, $t4
    beq     $t5, $zero, 7f
    nop
    li      $t4, -1
    b       2f
    nop
7:
    move    $t4, $zero

2:
    li      $t5, 0x3F4CCCCD       /* 0.8f */
    mtc1    $t5, $f1
    lwc1    $f0, 0x00($a0)
    mul.s   $f0, $f0, $f1
    bgez    $t4, 3f
    nop
    li      $t5, 0x42C00000       /* RIGHT anchor offset: 96.0f */
    mtc1    $t5, $f2
    add.s   $f0, $f0, $f2
3:
    swc1    $f0, 0x00($a0)
    lwc1    $f0, 0x20($a0)
    mul.s   $f0, $f0, $f1
    swc1    $f0, 0x20($a0)

1:
    j       0x08825EAC
    nop
.end tekken6_hud_side_strip_hook

.bss
.align 2
.globl tekken6_hud_fill_coords
tekken6_hud_fill_coords:
    .space 16
