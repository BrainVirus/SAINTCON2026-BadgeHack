#!/usr/bin/env python3
"""
SAINTCON 2026 Badge Firmware Patch (MAX SCORE EDITION - NO DELAY):
15 Max-Score (99,999 pts) Saves Generated at Boot.

Features:
- Extends the binary cleanly by 512 bytes past the end of the firmware image,
  moving Picobin Metadata Block 2 from 0x10176aa0 to 0x10176ca0 and updating
  the Pico binary info and Picobin Block 1 forward link.
- Leaves 100% of game code, sprites, strings, variables, and player data untouched.
- Places the 120-byte `hook_boot_generator` function in dedicated flash at 0x10176aa0.
- Hooks the boot sequence at 0x1000053a (replacing `bl ws2812_init` with `bl hook_boot_generator`).
- Hook controls:
  1. Hold Button A on boot:
     - Sets ship cargo hold to 24/24 ([0x20002438 + 0xc0] = 24).
     - Loops 15 times generating max-score saves (99,999 pts each).
     - Uses natural I2C EEPROM write timing (~20 ms per save, ~300 ms total).
     - Computes authentic cryptographic HMAC signatures for each save.
     - Flashes all 9 RGB LEDs Bright Green for 3 pulses to confirm.
  2. Hold Joystick UP on boot:
     - Wipes all 15 EEPROM game slot headers to 0x00 (empty).
     - Flashes all 9 RGB LEDs Bright Red for 3 pulses to confirm.
  3. Normal boot (neither held):
     - Generator hook exits cleanly in ~5 microseconds, continuing normal boot.
"""

import os
import sys
import struct
import hashlib

SRC_BIN = "badge_backup.bin"
DST_BIN = "badge_patched_max.bin"

XIP_BASE = 0x10000000
HOOK_ADDR = 0x10176aa0
HOOK_OFFSET = HOOK_ADDR - XIP_BASE
EXTRA_SIZE = 0x200  # 512 bytes
TARGET_SCORE = 99999

def encode_bl(pc, target):
    """Encode an ARM Thumb-2 32-bit branch with link (BL) instruction."""
    offset = target - (pc + 4)
    assert -0x1000000 <= offset < 0x1000000, f"Branch out of range: {hex(offset)}"
    assert (offset & 1) == 0, f"Target not 2-byte aligned: {hex(target)}"

    s = (offset >> 24) & 1
    i1 = (offset >> 23) & 1
    i2 = (offset >> 22) & 1
    imm10 = (offset >> 12) & 0x3FF
    imm11 = (offset >> 1) & 0x7FF

    j1 = (~i1 ^ s) & 1
    j2 = (~i2 ^ s) & 1

    hw1 = 0xF000 | (s << 10) | imm10
    hw2 = 0xD000 | (j1 << 13) | (j2 << 11) | imm11
    return struct.pack("<HH", hw1, hw2)

def build_hook(base_addr):
    """Assemble the hook_boot_generator binary payload with max score and no sleep_ms."""
    b = bytearray()
    # 0x00: push {r3-r7, lr} (24 bytes, maintains 8-byte stack alignment)
    b.extend(b"\xf8\xb5")
    # 0x02: bl ws2812_init (0x10010500)
    b.extend(encode_bl(base_addr + 0x02, 0x10010500))
    # 0x06: cmp r4, #0
    b.extend(b"\x00\x2c")
    # 0x08: beq .Ldone (+0x64 bytes -> 0x6e -> 0x10176b0e)
    b.extend(b"\x31\xd0")
    # 0x0a: bl read_live_buttons (0x1000dcc8)
    b.extend(encode_bl(base_addr + 0x0a, 0x1000dcc8))
    # 0x0e: mov r7, r0 (save button mask in r7)
    b.extend(b"\x07\x46")
    # 0x10: tst.w r7, #0x41 (Button A: 0x40 | Joystick UP: 0x01)
    b.extend(b"\x17\xf0\x41\x0f")
    # 0x14: beq .Ldone (+0x58 bytes -> 0x6e -> 0x10176b0e)
    b.extend(b"\x2b\xd0")
    # 0x16: sub sp, #16
    b.extend(b"\x84\xb0")
    # 0x18: movs r0, #0
    b.extend(b"\x00\x20")
    # 0x1a: strb.w r0, [sp, #0]
    b.extend(b"\x8d\xf8\x00\x00")
    # 0x1e: ldr r3, =0x20044a7b (pc + 80 -> 0x70 -> 0x10176b10)
    b.extend(b"\x14\x4b")
    # 0x20: strb r0, [r3, #0] (ensure offline_mode = 0)
    b.extend(b"\x18\x70")
    # 0x22: movs r6, #0x40
    b.extend(b"\x40\x26")
    # .Lwipe_loop (0x24):
    # 0x24: mov r0, r6
    b.extend(b"\x30\x46")
    # 0x26: mov r1, sp
    b.extend(b"\x69\x46")
    # 0x28: movs r2, #1
    b.extend(b"\x01\x22")
    # 0x2a: bl eeprom_write (0x1000e3b4)
    b.extend(encode_bl(base_addr + 0x2a, 0x1000e3b4))
    # 0x2e: adds r6, #0x40
    b.extend(b"\x40\x36")
    # 0x30: cmp.w r6, #0x400
    b.extend(b"\xb6\xf5\x80\x6f")
    # 0x34: bne .Lwipe_loop (-20 bytes -> 0x24)
    b.extend(b"\xf6\xd1")
    # 0x36: tst.w r7, #1 (Check if Joystick UP was pressed)
    b.extend(b"\x17\xf0\x01\x0f")
    # 0x3a: bne .Lwipe_only (+0x24 bytes -> 0x60)
    b.extend(b"\x11\xd1")
    # 0x3c: ldr r3, =0x20002438 (pc + 52 -> 0x74 -> 0x10176b14)
    b.extend(b"\x0d\x4b")
    # 0x3e: movs r2, #24
    b.extend(b"\x18\x22")
    # 0x40: str.w r2, [r3, #0xc0] (cargo hold = 24/24)
    b.extend(b"\xc3\xf8\xc0\x20")
    # 0x44: movs r5, #15
    b.extend(b"\x0f\x25")
    # .Lgen_loop (0x46):
    # Load 99,999 (0x0001869f) into r0
    b.extend(b"\x48\xf2\x9f\x60")                            # movw r0, #34463 (0x869f)
    b.extend(b"\xc0\xf2\x01\x00")                            # movt r0, #1
    # 0x4e: bl save_game_to_eeprom (0x10000754)
    b.extend(encode_bl(base_addr + 0x4e, 0x10000754))
    # 0x52: subs r5, #1
    b.extend(b"\x01\x3d")
    # 0x54: bne .Lgen_loop (-18 bytes -> 0x46)
    b.extend(b"\xf7\xd1")
    # 0x56: mov.w r0, #0x2000 (Bright Green GRB)
    b.extend(b"\x4f\xf4\x00\x50")
    # 0x5a: bl led_trigger_flash (0x100108b4)
    b.extend(encode_bl(base_addr + 0x5a, 0x100108b4))
    # 0x5e: b.n .Lcleanup (+8 bytes -> 0x68)
    b.extend(b"\x03\xe0")
    # .Lwipe_only (0x60):
    # 0x60: mov.w r0, #0x00200000 (Bright Red GRB)
    b.extend(b"\x4f\xf4\x00\x10")
    # 0x64: bl led_trigger_flash (0x100108b4)
    b.extend(encode_bl(base_addr + 0x64, 0x100108b4))
    # .Lcleanup (0x68):
    # 0x68: bl clear_latched_buttons (0x1000dca4)
    b.extend(encode_bl(base_addr + 0x68, 0x1000dca4))
    # 0x6c: add sp, #16
    b.extend(b"\x04\xb0")
    # .Ldone (0x6e):
    # 0x6e: pop {r3-r7, pc}
    b.extend(b"\xf8\xbd")
    # Literal pool (aligned at 0x70):
    # 0x70: 0x20044a7b (offline_mode flag address)
    # 0x74: 0x20002438 (game_state struct base address)
    b.extend(struct.pack("<II", 0x20044a7b, 0x20002438))

    assert len(b) == 0x78, f"Unexpected hook length: {hex(len(b))}"
    return bytes(b)

def patch_firmware(src_path, dst_path):
    print(f"Reading source firmware: {src_path}")
    with open(src_path, "rb") as f:
        data = bytearray(f.read())

    orig_len = len(data)
    print(f"Original size: {orig_len} bytes ({hex(orig_len)})")
    assert orig_len == 1534644, f"Unexpected source file size: {orig_len}"

    # Verify original hook point instruction
    orig_hook_instr = data[0x53a:0x53e]
    expected_hook_instr = bytes.fromhex("0ff0e1ff")
    assert orig_hook_instr == expected_hook_instr, (
        f"Mismatch at 0x1000053a: found {orig_hook_instr.hex()}, expected {expected_hook_instr.hex()}"
    )

    # Verify Picobin Block 1 at 0x10000138
    b1_magic = struct.unpack_from("<I", data, 0x138)[0]
    assert b1_magic == 0xFFFFDED3, f"Block 1 magic mismatch: {hex(b1_magic)}"
    orig_b1_link = struct.unpack_from("<I", data, 0x144)[0]
    assert orig_b1_link == 0x00176968, f"Block 1 link mismatch: {hex(orig_b1_link)}"

    # Verify Picobin Block 2 at 0x10176aa0
    b2_magic = struct.unpack_from("<I", data, 0x176aa0)[0]
    assert b2_magic == 0xFFFFDED3, f"Block 2 magic mismatch: {hex(b2_magic)}"

    # Verify binary_info end pointer at 0x1016d000
    orig_bin_end = struct.unpack_from("<I", data, 0x16d000)[0]
    assert orig_bin_end == 0x10176ab4, f"Binary end pointer mismatch: {hex(orig_bin_end)}"

    print("Source firmware integrity verified 100%. Applying patch...")

    # 1. Update boot instruction at 0x1000053a to call HOOK_ADDR
    new_hook_call = encode_bl(0x1000053a, HOOK_ADDR)
    data[0x53a:0x53e] = new_hook_call
    print(f"  [+] Patched 0x1000053a: 'bl 0x10010500' -> 'bl {hex(HOOK_ADDR)}' ({new_hook_call.hex()})")

    # 2. Update Picobin Block 1 forward link
    new_b1_link = orig_b1_link + EXTRA_SIZE
    struct.pack_into("<I", data, 0x144, new_b1_link)
    print(f"  [+] Updated Picobin Block 1 forward link: {hex(orig_b1_link)} -> {hex(new_b1_link)}")

    # 3. Update binary_info binary end pointer
    new_bin_end = orig_bin_end + EXTRA_SIZE
    struct.pack_into("<I", data, 0x16d000, new_bin_end)
    print(f"  [+] Updated binary_info binary end: {hex(orig_bin_end)} -> {hex(new_bin_end)}")

    # 4. Save and move Picobin Block 2
    orig_b2_bytes = bytes(data[0x176aa0:0x176ab4])
    data[0x176aa0:0x176ab4] = b"\x00" * 20
    data.extend(b"\x00" * (EXTRA_SIZE - 20))

    new_b2_bytes = bytearray(orig_b2_bytes)
    struct.pack_into("<i", new_b2_bytes, 12, -new_b1_link)
    data.extend(new_b2_bytes)
    print(f"  [+] Moved Picobin Block 2 to {hex(0x10176aa0 + EXTRA_SIZE)} with updated reverse link")

    # 5. Insert assembled hook at 0x10176aa0 (offset 0x176aa0)
    hook_payload = build_hook(HOOK_ADDR)
    data[0x176aa0:0x176aa0 + len(hook_payload)] = hook_payload
    print(f"  [+] Installed hook_boot_generator ({len(hook_payload)} bytes) at {hex(HOOK_ADDR)}")
    print(f"      - Fixed Score Target: {TARGET_SCORE:,} points")
    print(f"      - No sleep_ms delay: natural EEPROM write timing (~20 ms/save)")

    # Write output binary
    with open(dst_path, "wb") as f:
        f.write(data)

    print(f"Successfully generated: {dst_path}")
    print(f"  New file size: {len(data)} bytes ({hex(len(data))})")
    print(f"  SHA-256: {hashlib.sha256(data).hexdigest()}")

if __name__ == "__main__":
    patch_firmware(SRC_BIN, DST_BIN)
