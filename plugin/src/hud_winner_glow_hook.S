.set noreorder

.text
.align 2
.globl tekken6_hud_winner_glow_hook
.ent tekken6_hud_winner_glow_hook
tekken6_hud_winner_glow_hook:
    addiu   $sp, $sp, -0x40
    sw      $ra, 0x3C($sp)

    /* Device-proven winner glow: four source vertices converted by
     * 0x08AE94A4 into 20-byte 0x80019E THROUGH vertices. */
    li      $t0, 4
    bne     $a3, $t0, 9f
    nop

    /* Exact 64x64 UV corners, source stride 0x30:
     * (0,0), (0,64), (64,0), (64,64). */
    lhu     $t0, 0x20($a2)
    bne     $t0, $zero, 9f
    nop
    lhu     $t0, 0x22($a2)
    bne     $t0, $zero, 9f
    nop
    lhu     $t0, 0x50($a2)
    bne     $t0, $zero, 9f
    nop
    lhu     $t0, 0x52($a2)
    li      $t1, 64
    bne     $t0, $t1, 9f
    nop
    lhu     $t0, 0x80($a2)
    bne     $t0, $t1, 9f
    nop
    lhu     $t0, 0x82($a2)
    bne     $t0, $zero, 9f
    nop
    lhu     $t0, 0xB0($a2)
    bne     $t0, $t1, 9f
    nop
    lhu     $t0, 0xB2($a2)
    bne     $t0, $t1, 9f
    nop

    /* x0+x3 selects only the two stock winner-glow centers observed in the
     * neutral captures: P1 center ~198 (sum ~396) or P2 center ~280.5
     * (sum ~561). Positive float bit patterns preserve unsigned ordering. */
    lwc1    $f0, 0x00($a2)
    lwc1    $f2, 0x90($a2)
    add.s   $f6, $f0, $f2
    mfc1    $t0, $f6

    li      $t1, 0x43C50000       /* 394.0f */
    sltu    $t2, $t0, $t1
    bne     $t2, $zero, 2f
    nop
    li      $t1, 0x43C70000       /* 398.0f */
    sltu    $t2, $t1, $t0
    beq     $t2, $zero, 3f
    nop

2:
    li      $t1, 0x440BC000       /* 559.0f */
    sltu    $t2, $t0, $t1
    bne     $t2, $zero, 9f
    nop
    li      $t1, 0x440CC000       /* 563.0f */
    sltu    $t2, $t1, $t0
    bne     $t2, $zero, 9f
    nop

3:
    /* y0+y3 ~= 70 selects the winner-orb row without flattening rotation. */
    lwc1    $f0, 0x04($a2)
    lwc1    $f2, 0x94($a2)
    add.s   $f6, $f0, $f2
    mfc1    $t0, $f6
    li      $t1, 0x42880000       /* 68.0f */
    sltu    $t2, $t0, $t1
    bne     $t2, $zero, 9f
    nop
    li      $t1, 0x42900000       /* 72.0f */
    sltu    $t2, $t1, $t0
    bne     $t2, $zero, 9f
    nop

    /* Temporarily CENTER-transform only the four source X coordinates.
     * Restore them immediately after the original converter consumes them. */
    lw      $t0, 0x00($a2)
    lw      $t1, 0x30($a2)
    lw      $t2, 0x60($a2)
    lw      $t3, 0x90($a2)
    sw      $t0, 0x00($sp)
    sw      $t1, 0x04($sp)
    sw      $t2, 0x08($sp)
    sw      $t3, 0x0C($sp)

    li      $t0, 0x3F4CCCCD       /* 0.8f */
    mtc1    $t0, $f4
    li      $t0, 0x42400000       /* 48.0f */
    mtc1    $t0, $f6

    lwc1    $f0, 0x00($a2)
    mul.s   $f0, $f0, $f4
    add.s   $f0, $f0, $f6
    swc1    $f0, 0x00($a2)
    lwc1    $f0, 0x30($a2)
    mul.s   $f0, $f0, $f4
    add.s   $f0, $f0, $f6
    swc1    $f0, 0x30($a2)
    lwc1    $f0, 0x60($a2)
    mul.s   $f0, $f0, $f4
    add.s   $f0, $f0, $f6
    swc1    $f0, 0x60($a2)
    lwc1    $f0, 0x90($a2)
    mul.s   $f0, $f0, $f4
    add.s   $f0, $f0, $f6
    swc1    $f0, 0x90($a2)

    jal     0x08AE94A4
    nop

    lw      $t0, 0x00($sp)
    lw      $t1, 0x04($sp)
    lw      $t2, 0x08($sp)
    lw      $t3, 0x0C($sp)
    sw      $t0, 0x00($a2)
    sw      $t1, 0x30($a2)
    sw      $t2, 0x60($a2)
    sw      $t3, 0x90($a2)
    b       10f
    nop

9:
    jal     0x08AE94A4
    nop

10:
    lw      $ra, 0x3C($sp)
    jr      $ra
    addiu   $sp, $sp, 0x40
.end tekken6_hud_winner_glow_hook
