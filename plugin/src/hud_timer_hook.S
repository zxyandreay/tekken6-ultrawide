.set noreorder

.text
.align 2
.globl tekken6_hud_timer_digit_wrapper
.ent tekken6_hud_timer_digit_wrapper
tekken6_hud_timer_digit_wrapper:
    addiu   $sp, $sp, -0x20
    sw      $ra, 0x1C($sp)

    /* The original timer callsites pass a fifth argument in the caller's
     * stack slot at 0($sp).  Preserve that ABI through this wrapper: after
     * allocating 0x20 bytes, the caller's 0($sp) is now at 0x20($sp). */
    lw      $t4, 0x20($sp)
    sw      $t4, 0x00($sp)

    /* The large round countdown bypasses the slot-builder routes used by the
     * surrounding round rails/orbs, but its digit renderer eventually reaches
     * the same rectangle builder. Reuse the proven centered rectangle scope
     * only while each timer digit is being submitted. */
    lui     $t4, %hi(tekken6_hud_shell_depth)
    addiu   $t4, $t4, %lo(tekken6_hud_shell_depth)
    lw      $t5, 0($t4)
    addiu   $t5, $t5, 1
    sw      $t5, 0($t4)

    jal     0x0892D72C
    nop

    lui     $t4, %hi(tekken6_hud_shell_depth)
    addiu   $t4, $t4, %lo(tekken6_hud_shell_depth)
    lw      $t5, 0($t4)
    addiu   $t5, $t5, -1
    sw      $t5, 0($t4)

    lw      $ra, 0x1C($sp)
    jr      $ra
    addiu   $sp, $sp, 0x20
.end tekken6_hud_timer_digit_wrapper
