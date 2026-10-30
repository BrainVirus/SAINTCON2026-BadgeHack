# Cracking the Orion Trail: How We Reverse-Engineered the SAINTCON 2026 Badge

*A talk-ready narrative of how we went from a USB serial prompt to all 3 flags and 100% achievement completion on the SAINTCON 2026 RP2350 badge.*

> [!NOTE]
> **AI Collaboration Notice:** This reverse-engineering journey, assembly decompilation, custom hash reversal, and narrative writeup were conducted in collaboration with AI (Google DeepMind's Antigravity).

---

## Act I: First Contact & The 85 Hz Speed Limit

Every good badge hack starts the same way: you plug a USB-C cable into the badge, run a quick device check on Linux, and wait to see what talks back.

Up popped a Raspberry Pi Pico 2—an ARM Cortex-M33 **RP2350** microcontroller—exposing a USB serial console at `/dev/ttyACM0`. When we opened a terminal and hit Enter, the badge greeted us with an ASCII starfield banner, a cryptic string at the top (`DV+HTSB+DJOGY`), and a simple command prompt:

```text
> HELP
Commands: HANDLE <new_handle>, UNLOCK <code>, IDENT
```

Right away, we noticed a quirk: if you pasted a batch of commands into the serial port all at once, the badge ignored almost all of them. Why? As we later confirmed in the firmware, the badge's main game loop only polls the USB serial buffer once per video frame tick—roughly **85 Hz (every 11.8 milliseconds)**. Once we paced our Python serial script to wait for the `> ` prompt between lines, we had a rock-solid command channel.

First order of business: claiming the badge.
```text
> HANDLE BrainVirus
Your new handle is "BrainVirus"
```

Next, we went hunting for low-hanging fruit:
1. **`SC_DUST_FLUX`** was sitting right in the `HELP` example text. Sending `UNLOCK SC_DUST_FLUX` gave us our first `UNLOCK: OK`—unlocking the achievement **"Service Port"**.
2. What about that gibberish string `DV+HTSB+DJOGY` in the starfield banner? Look at your keyboard: `D` is one key to the right of `S`. `V` is one key to the right of `C`. Every single character was shifted one key to the right on a standard QWERTY layout. Shifting them one key left decoded **`SC_GRAV_SHIFT`**—which unlocked the aptly named achievement **"Misaligned Home Row"**.
3. Probing undocumented commands revealed a `FLAG` command (`FLAG 1`, `FLAG 2`, `FLAG 3`).
   - `FLAG 1` immediately handed over the first flag: **`{At0m1c_Ut0p1a_1955}`**.
   - `FLAG 2` replied: `Flag: INVALID`.
   - `FLAG 3` replied: `Flag: ***********************`—23 asterisks staring right back at us.

The front door had given us all it was going to give. It was time to pull the firmware.

---

## Act II: Dumping the Brain

Because the badge runs on an RP2350, we added a quick Linux `udev` rule for the Raspberry Pi USB vendor ID (`2e8a`) and used `picotool` to dump the entire 1.5 MB XIP flash image straight to disk as `badge_backup.bin`.

Now we had the entire brain of the badge sitting in front of us.

---

## Act III: The Three Flags & The Troll in `FLAG 3`

Our first stop inside `badge_backup.bin` was the `FLAG` command handler at `0x10010016`.

### The `FLAG 3` Fake-Out
Why did `FLAG 3` print 23 asterisks? When we disassembled the `FLAG 3` branch at `0x100102fe`, we couldn't help but laugh. The firmware actually loads the real, plaintext flag from flash offset `0x28070` onto the stack, runs three rounds of a block cipher over it, and then—right before printing it—executes this:

```armasm
mov.w r3, #0x2a2a2a2a   ; '****'
str   r3, [sp, #0x30]
strd  r3, r3, [sp, #32]
strd  r3, r3, [sp, #40]
```

It literally overwrites the buffer with `0x2A` (`'*'`) every single time! There is no serial argument that unmasks it—the puzzle *was* dumping the firmware. Reading flash offset `0x28070` gave us **`FLAG 3`**:
> **`{Rusty_C0d3_1s_4w3s0m3}`**

### Reversing `FLAG 2` (Enter Professor Plum)
Next, we looked at the `FLAG 2` branch (`0x1001033a`). Before doing anything, it reads the first 4 bytes of the badge's onboard I2C EEPROM and compares them against the string **`"PLUM"`**. If that header isn't there, it prints `Flag: INVALID`.

But what if the `"PLUM"` header *is* there? The code loads a 21-byte scrambled byte array from flash offset `0x280bc` and runs a tight Thumb-2 decryption loop over each byte `b` at index `i`:

```python
x = ((b ^ i ^ 0xA5) + 3 * i) & 0xFF
char = ((x << 3) | (x >> 5)) & 0xFF  # 3-bit left rotate
```

Running those 21 bytes through a 5-line Python script decoded **`FLAG 2`** on the spot:
> **`{R4ygun_G0th13_Ph4s3}`**

All three CTF flags were now in the bag.

---

## Act IV: Where Are All the `UNLOCK` Codes?

Next, we wanted every single `UNLOCK` achievement on the badge. We knew the codes all started with `SC_`, so we ran a regex search for `SC_[A-Z0-9_]+` across the 1.5 MB firmware image.

Only **one** plaintext code came back:
- **`SC_THRUST_LOSS`** (at `0x28239`) — which unlocked **"Deep Storage"**. (Get it? Because it was buried in deep flash storage!)

Okay, what if the rest were XOR-encoded so they wouldn't show up in `strings`? We wrote a single-byte XOR crib scanner looking for the byte pattern of `"SC_"` across all 255 XOR keys. That caught two more codes hiding in the binary:
- **`SC_PHASE_DRIFT`** (XORed with `0x57` at `0x27bf0`) — used by the hardware dock UART handler, unlocking **"Dockmaster's Channel"**.
- **`SC_SIGNAL_GHOST`** (XORed with `0x55` at `0x27574`) — written into the I2C EEPROM during factory initialization, unlocking **"Long-Term Memory"**.

Along with two conference clues (**`SC_CORE_FLUX`** and **`SC_LAGRANGE_LOCK`**), we now had **7 codes**.

But when we checked the achievement pointer table in the `.data` section at `0x176220`, there were **32 achievements total**:
- Slots `0` and `1` (**"Thirty Lives"** via the 10-button Konami Code, and **"First Departure"** when launching your first voyage) were in-game only.
- Slots `2` through `31` were **30 code-backed achievements**.

We had 7. Where were the other 23? Why didn't they show up anywhere in the binary?

---

## Act V: `"PlumProf"` and the 64-Bit Hash Table

To find out, we disassembled the `UNLOCK` validator function at `0x1000e0d0`. And there was the plot twist:

**The remaining 23 codes aren't stored in the firmware at all.**

Instead, when you type `UNLOCK <code>`, the badge:
1. Measures the length of your string.
2. Loads a 64-bit seed from `0x1000e180`: `0x506c756d` and `0x50726f66`. In ASCII, that spells **`"PlumProf"`**—Professor Plum strikes again!
3. Passes your string and the `"PlumProf"` seed into a custom 64-bit xxHash-inspired mixing function at `0x10010a9c`.
4. Loops through a table of **30 64-bit hashes** in SRAM (`0x20001718`–`0x20001807`, initialized from flash offset `0x1762b4`). If the 64-bit hash matches entry `i`, achievement `i` unlocks!

To crack the remaining 23 codes, we had to translate the ARM Thumb-2 assembly of `0x10010a9c`—all 108 instructions of 64-bit multiplies, shifts, rotates, and XOR avalanches—into Python:

```python
def badge_hash64(data: bytes, seed: int = 0x50726f66506c756d) -> int:
    MASK64 = 0xFFFFFFFFFFFFFFFF
    h = (seed ^ 0x85ebca77c2b2ae63) & MASK64
    # ... 8-byte chunk mixing + tail bytes + 4-stage avalanche finalizer ...
```

The moment of truth: we fed our 7 known `SC_` codes into our reconstructed `badge_hash64` function and compared the outputs against the 30 64-bit numbers in the firmware's `.data` section.

**All 7 matched on the very first try.**

Now we had an exact offline oracle. Every code followed the pattern `SC_<WORD1>_<WORD2>` using space, orbital mechanics, and sci-fi vocabulary (`VECTOR`, `ORBIT`, `DRIFT`, `SHIFT`, `FLUX`, `ECHO`, `APOGEE`, `PERIGEE`).
- Our first pass in Python tested words scraped from the binary and basic space terms—instantly cracking **16 more codes** (`SC_VECTOR_BURN`, `SC_NOVA_TRACE`, `SC_PLASMA_ARC`, `SC_ORBIT_DECAY`, `SC_PULSE_FIELD`, `SC_APOGEE_DRIFT`, `SC_PERIGEE_SHIFT`, and more).
- That left just 7 hashes standing. We wrote a tiny C program compiled with `gcc -O3` to pair our orbital theme words against the entire 54,000-word Linux system dictionary (`cracklib-small`) plus physics terms (`WAKE`, `SHEAR`, `OFFSET`, `BIAS`, `PARALLAX`).
- In **less than one second**, the remaining 7 hashes fell like dominoes:
  - `SC_ION_WAKE` (*The Obsidian Monolith*)
  - `SC_SOLAR_SHEAR` (*Full Complement*)
  - `SC_STAR_OFFSET` (*Works Well With Others*)
  - `SC_QUANTUM_WAKE` (*Synthetic Minds*)
  - `SC_RADIAL_DRIFT` (*Fabric of Reality*)
  - `SC_COSMIC_BIAS` (*Blue Skies Ahead*)
  - And the final holdout, Slot 21 (*Attack Surface Survey*): **`SC_DEEP_PARALLAX`**.

All **30 out of 30** achievement hashes were cracked.

---

## Epilogue: Watching the Board Light Up

We wrote one final script to feed all 30 `UNLOCK` codes sequentially over `/dev/ttyACM0` into the live badge. One after another, `UNLOCK: OK` cascaded down the terminal as the badge flashed bright purple and wrote the completed bitmask to its I2C EEPROM.

And as the last achievement unlocked, we noticed the 9 addressable WS2812 RGB LEDs on the front of the badge were suddenly spinning at warp speed. When we checked the LED timer code at `0x10010624`, we found one last Easter egg left by the badge creators:

```c
int delay_ms = 170 - (5 * get_achievement_count());
```

Every time you unlock an achievement on the SAINTCON 2026 badge, it shaves 5 milliseconds off the LED animation timer—starting at a leisurely `170 ms` with zero achievements and accelerating all the way down to a blazing `10 ms` once the board is cleared.

**Final tally:**
- **Handle:** `"BrainVirus"`
- **Flags:** 3 / 3 (`{At0m1c_Ut0p1a_1955}`, `{R4ygun_G0th13_Ph4s3}`, `{Rusty_C0d3_1s_4w3s0m3}`)
- **Unlock Codes:** 30 / 30 cracked and verified on hardware.

