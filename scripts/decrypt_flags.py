#!/usr/bin/env python3
"""
SAINTCON 2026 Badge — CTF Flag Decryptor & Honeypot Analysis
Extracts and decrypts all CTF flags from badge_backup.bin.

Credit: Huge thanks to r3tr0hck342 for discovering that {Rusty_C0d3_1s_4w3s0m3}
is an uncalled strings honeypot and identifying the GOST 28147-89 (Magma) cipher for Flag 3!
"""

import os
import sys
import struct

def main():
    bin_path = sys.argv[1] if len(sys.argv) > 1 else "badge_backup.bin"
    if not os.path.exists(bin_path):
        print(f"Error: Firmware backup '{bin_path}' not found.")
        print("Usage: python3 decrypt_flags.py [path/to/badge_backup.bin]")
        sys.exit(1)

    with open(bin_path, "rb") as f:
        data = f.read()

    print("=" * 65)
    print("SAINTCON 2026 RP2350 Badge — CTF Flag Extractor")
    print("Credit to r3tr0hck342 for pointing out the Flag 3 GOST cipher!")
    print("=" * 65)

    # 1. FLAG 1 (XOR 0xCC @ 0x10028088 / file offset 0x28088)
    f1_raw = data[0x28088 : 0x28088 + 22]
    flag1 = bytes([b ^ 0xCC for b in f1_raw]).split(b"\x00")[0].decode("ascii")
    print(f"\n[+] FLAG 1 (Printed via serial):")
    print(f"    Storage : XOR 0xCC @ flash offset 0x28088")
    print(f"    Value   : {flag1}")

    # 2. FLAG 2 (rol8((b ^ i ^ 0xA5) + 3i, 3) @ 0x100280bc / file offset 0x280bc)
    f2_raw = data[0x280bc : 0x280bc + 21]
    flag2 = "".join(
        chr(((((b ^ i ^ 0xA5) + 3 * i) & 0xFF) << 3 | (((b ^ i ^ 0xA5) + 3 * i) & 0xFF) >> 5) & 0xFF)
        for i, b in enumerate(f2_raw)
    )
    print(f"\n[+] FLAG 2 (EEPROM 'PLUM' gated):")
    print(f"    Storage : Custom bit-rotation cipher @ flash offset 0x280bc")
    print(f"    Value   : {flag2}")

    # 3. FLAG 3 (GOST 28147-89 / Magma @ 0x100280a0 / file offset 0x280a0)
    sbox = data[0x16ddc0 : 0x16ddc0 + 128]
    K = struct.unpack("<8I", data[0x1763ac : 0x1763ac + 32])
    idx = struct.unpack("<32I", data[0x16dd40 : 0x16dd40 + 128])
    ct = data[0x280a0 : 0x280a0 + 24]

    def f_step(x, k):
        s = (x + k) & 0xFFFFFFFF
        res = 0
        for i in range(8):
            res |= sbox[i * 16 + ((s >> (4 * i)) & 0xF)] << (4 * i)
        return ((res << 11) | (res >> 21)) & 0xFFFFFFFF

    pt = bytearray()
    for b in range(0, 24, 8):
        L, R = struct.unpack("<2I", ct[b : b + 8])
        for rnd in range(32):
            L, R = R ^ f_step(L, K[idx[rnd]]), L
        pt.extend(struct.pack("<2I", R, L))

    pad = pt[-1]
    flag3 = pt[:-pad].decode("ascii") if pad < 8 else pt.decode("ascii", errors="replace")
    print(f"\n[+] FLAG 3 (Device asterisks output, GOST/Magma encrypted):")
    print(f"    Storage : GOST 28147-89 (Magma) @ flash offset 0x280a0")
    print(f"    Value   : {flag3}")

    # 4. Decoy Bait
    decoy = data[0x28070 : 0x28070 + 23].decode("ascii")
    print(f"\n[!] DECOY HONEYPOT (Never outputted, strings trap):")
    print(f"    Storage : Plaintext @ flash offset 0x28070")
    print(f"    Value   : {decoy}")
    print("=" * 65)

if __name__ == "__main__":
    main()
