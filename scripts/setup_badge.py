#!/usr/bin/env python3
"""
SAINTCON 2026 Badge Setup Script
Prompts for a handle, unlocks all 30 achievements, and sets the handle on the badge.
"""

import os
import sys
import time
import select
import tty

CODES = [
    ("Slot 02: Frequent Flyer", "SC_VECTOR_BURN"),
    ("Slot 03: Relics of the First Builders", "SC_NOVA_TRACE"),
    ("Slot 04: The Obsidian Monolith", "SC_ION_WAKE"),
    ("Slot 05: Full Complement", "SC_SOLAR_SHEAR"),
    ("Slot 06: A Crew of Specialists", "SC_PLASMA_ARC"),
    ("Slot 07: Signed On", "SC_VOID_VECTOR"),
    ("Slot 08: Works Well With Others", "SC_STAR_OFFSET"),
    ("Slot 09: Civic Duty", "SC_ORBIT_DECAY"),
    ("Slot 10: Deep Storage", "SC_THRUST_LOSS"),
    ("Slot 11: Long-Term Memory", "SC_SIGNAL_GHOST"),
    ("Slot 12: Manual Override", "SC_ECHO_ORBIT"),
    ("Slot 13: Service Port", "SC_DUST_FLUX"),
    ("Slot 14: Dockmaster's Channel", "SC_PHASE_DRIFT"),
    ("Slot 15: Misaligned Home Row", "SC_GRAV_SHIFT"),
    ("Slot 16: Diagnostics Complete", "SC_CORE_FLUX"),
    ("Slot 17: Circles Within Circles", "SC_LAGRANGE_LOCK"),
    ("Slot 18: Connect the Dots", "SC_PULSE_FIELD"),
    ("Slot 19: Know a Guy", "SC_FIELD_ECHO"),
    ("Slot 20: Synthetic Minds", "SC_QUANTUM_WAKE"),
    ("Slot 21: Attack Surface Survey", "SC_DEEP_PARALLAX"),
    ("Slot 22: Fabric of Reality", "SC_RADIAL_DRIFT"),
    ("Slot 23: Blue Skies Ahead", "SC_COSMIC_BIAS"),
    ("Slot 24: Bare Metal", "SC_FLUX_VECTOR"),
    ("Slot 25: Sick Bay", "SC_ORBIT_TRACE"),
    ("Slot 26: Domestic Infrastructure", "SC_ASTRA_SHIFT"),
    ("Slot 27: Identity Crisis", "SC_ZENITH_DRIFT"),
    ("Slot 28: Open Access", "SC_ECHO_VECTOR"),
    ("Slot 29: Off the Record", "SC_DRIFT_LOCK"),
    ("Slot 30: Seal Broken", "SC_APOGEE_DRIFT"),
    ("Slot 31: The Watchtower", "SC_PERIGEE_SHIFT"),
]

def send_cmd(fd, cmd_str, timeout=1.0):
    os.write(fd, f"{cmd_str}\r\n".encode("ascii"))
    buf = b""
    deadline = time.time() + timeout
    while time.time() < deadline:
        r, _, _ = select.select([fd], [], [], 0.05)
        if r:
            buf += os.read(fd, 512)
            if b">" in buf or b"\n" in buf:
                time.sleep(0.02)
                r2, _, _ = select.select([fd], [], [], 0.02)
                if r2:
                    buf += os.read(fd, 512)
                break
    return buf.decode("ascii", errors="replace").strip()

def main():
    device = "/dev/ttyACM0"
    if len(sys.argv) > 1:
        handle = sys.argv[1].strip()
    else:
        try:
            handle = input("Enter badge handle / username: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)

    if not handle:
        print("Error: Handle cannot be empty.")
        sys.exit(1)

    print(f"\nWaiting for badge at {device}...")
    while not os.path.exists(device):
        time.sleep(0.5)

    print(f"Connected to {device}!")
    fd = os.open(device, os.O_RDWR | os.O_NOCTTY)
    try:
        tty.setraw(fd)
        # Drain any existing bytes
        while True:
            r, _, _ = select.select([fd], [], [], 0.1)
            if not r:
                break
            os.read(fd, 1024)

        # 1. Unlock achievements
        print(f"\nUnlocking all 30 achievements...")
        success = 0
        for i, (name, code) in enumerate(CODES, 1):
            resp = send_cmd(fd, f"UNLOCK {code}")
            if "UNLOCK: OK" in resp or "ALREADY UNLOCKED" in resp:
                success += 1
                status = "✓ OK"
            else:
                status = f"✗ {resp}"
            print(f"  [{i:02d}/30] {name:<35} -> {status}")
            time.sleep(0.04)

        print(f"\nAchievements unlocked: {success}/30")

        # 2. Set handle
        print(f"\nSetting handle to \"{handle}\"...")
        resp = send_cmd(fd, f"HANDLE {handle}")
        print(f"  {resp}")

        # 3. Verify handle
        ident = send_cmd(fd, "IDENT")
        print(f"  Badge identity: {ident}")

        print("\n" + "=" * 50)
        print(f"✓ All done! Badge handle set to \"{handle}\".")
        print("=" * 50)
    finally:
        os.close(fd)

if __name__ == "__main__":
    main()
