# SAINTCON 2026 Badge — Reverse Engineering & CTF Writeup
Repo: `https://github.com/BrainVirus/SAINTCON2026-BadgeHack`

Complete writeup, achievement unlock codes, CTF flags, beginner's walkthrough, and setup scripts for the **SAINTCON 2026 RP2350 Conference Badge**.

> [!NOTE]
> **AI Collaboration Disclosure:** This reverse engineering research, CTF flag recovery, firmware analysis, setup tooling, and documentation were performed with the collaborative assistance of AI (Google DeepMind's Antigravity).

## Repository Contents

- **[BEGINNER_GUIDE.md](./BEGINNER_GUIDE.md)** — **Start here!** A dead-simple, step-by-step walkthrough written specifically for IT and InfoSec professionals who are new to hardware hacking. Covers plugging in the badge, serial shell recon, solving the starfield cipher, the Konami code, dumping the firmware without soldering, capturing all 3 CTF flags, and cracking the 30 achievement hashes.
- **[SAINTCON2026_BADGE_STORY.md](./SAINTCON2026_BADGE_STORY.md)** — Talk-ready narrative walking through how we reverse-engineered the badge from initial USB serial access to dumping the flash, cracking the `"PlumProf"` 64-bit hash table, and unlocking all 30 achievements.
- **[SAINTCON2026_BADGE_GUIDE.md](./SAINTCON2026_BADGE_GUIDE.md)** — Complete technical reference containing:
  - All 3 CTF flags (`FLAG 1`, `FLAG 2`, `FLAG 3`), the decoy honeypot, and GOST/Magma decryption methods (credit to `r3tr0hck342`)
  - All 32 achievements (`Slots 0–31`) and all 30 `UNLOCK` codes (`Slots 2–31`)
  - Python implementation of the custom 64-bit `"PlumProf"` hash algorithm (`0x10010a9c`)
  - Onboard 1 KB I2C EEPROM (`0x50`) and SRAM (`0x200021a8`) state structure layout
  - Addressable WS2812 RGB LED (`PIO0` / GPIO 24) hardware and firmware architecture
- **[ORION_TRAIL_STRATEGY_GUIDE.md](./ORION_TRAIL_STRATEGY_GUIDE.md)** — Reverse-engineered formulas, trading math, event tables, and optimal high-score strategy for the *Orion Trail* RPG (internally named *Wayfarer* in firmware).
- **[scripts/decrypt_flags.py](./scripts/decrypt_flags.py)** — Standalone offline tool to extract and decrypt all 3 CTF flags (including GOST 28147-89 Magma) and analyze the honeypot directly from `badge_backup.bin`.
- **[scripts/setup_badge.py](./scripts/setup_badge.py)** (or **[scripts/setup_badge.sh](./scripts/setup_badge.sh)**) — All-in-one setup script that connects to `/dev/ttyACM0`, unlocks all 30 conference achievements, and sets your custom handle.
- **[LICENSE](./LICENSE)** — MIT License.

## Automated Badge Setup Script (`scripts/setup_badge.py` / `.sh`)

To unlock all 30 conference achievements and set your handle on the physical badge:

```bash
# Using Python directly (replace <YOUR_HANDLE> with whatever username you want):
python3 scripts/setup_badge.py <YOUR_HANDLE>

# Or using the shell wrapper:
./scripts/setup_badge.sh <YOUR_HANDLE>

# Or run interactively (it will prompt you to type the name you want):
python3 scripts/setup_badge.py
```

> [!TIP]
> You do **not** need to use `BrainVirus`! Replace `<YOUR_HANDLE>` with your own hacker alias or preferred conference name.


