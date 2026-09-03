.set noreorder
.set nomacro

.text
.align 2
.globl t6_native_2d_safe_viewport
.ent t6_native_2d_safe_viewport

/*
 * Entry contract is Tekken's existing viewport-call contract at 0x08864B88:
 *   f12 = x
 *   f13 = y
 *   f14 = width
 *   f15 = height
 *   f16 = near
 *   f17 = far
 *
 * Preserve every authored 2D coordinate. Only map the complete flat viewport
 * into a centered native-PSP aspect safe area:
 *   safeWidth = width * g_safeAreaScale
 *   x += (width - safeWidth) * 0.5
 *   width = safeWidth
 * height/y/depth are unchanged.
 */
t6_native_2d_safe_viewport:
    addiu   $sp, $sp, -16
    sw      $ra, 12($sp)

    lui     $t0, %hi(g_safeAreaScale)
    lwc1    $f0, %lo(g_safeAreaScale)($t0)
    mul.s   $f1, $f14, $f0
    sub.s   $f2, $f14, $f1

    lui     $at, 0x3F00
    mtc1    $at, $f3
    mul.s   $f2, $f2, $f3
    add.s   $f12, $f12, $f2
    mov.s   $f14, $f1

    jal     0x08AC5BA8
    nop

    lw      $ra, 12($sp)
    addiu   $sp, $sp, 16
    jr      $ra
    nop

.end t6_native_2d_safe_viewport
