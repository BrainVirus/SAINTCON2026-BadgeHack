# SAINTCON 2026 Badge — Complete CTF, Achievement & Hardware Reference

> [!NOTE]
> **AI Collaboration Notice:** The reverse-engineered algorithms, memory maps, hash implementations, and technical documentation in this guide were produced with the assistance of AI (Google DeepMind's Antigravity).

## 1. Hardware & Serial CLI Overview

- **MCU:** Raspberry Pi Pico 2 (RP2350, ARM Cortex-M33 Thumb-2), USB ID `2e8a:0009`
- **Serial Interface:** `/dev/ttyACM0` (`/dev/serial/by-id/usb-Raspberry_Pi_Pico_*-if00`)
- **Firmware Backup:** `badge_backup.bin` (`1,534,644` bytes, mapped at `0x10000000` in XIP flash, dumped via `picotool`)
- **Supported USB Serial CLI Commands (`0x10010180`):**
  - `HELP` — Displays command summary and sample unlock code (`SC_DUST_FLUX`).
  - `IDENT` — Prints current badge handle (`IDENT "BrainVirus"`).
  - `HANDLE <new_handle>` — Updates persistent badge handle (stored in SRAM at `0x200021a8` and I2C EEPROM at `0x0010`).
  - `UNLOCK <code>` — Validates `<code>` (case-insensitive) against 30 64-bit achievement hashes (`0x1000e0d0`).
  - `CLEAR` — Clears the terminal screen and reprints the starfield ASCII banner.
  - `FLAG <1|2|3>` — Queries badge CTF flags 1, 2, or 3.
- **Supported Hardware Dock / UART Commands (`0x1000fe80`):**
  - `$UNLOCK <code>` — Unlocks an achievement over the physical dock UART.
  - `$STATION ...`, `$ID ...`, `$GAME ...`, `$VOTE ...`, `$EOL ...` — Orion Trail station/crew/voting protocol messages.

---

## 2. All 3 Hidden CTF Flags (`FLAG 1`, `FLAG 2`, `FLAG 3`)

| Flag         | Value                     | How It Was Found                                                                                                                                                                                                                                                                                                                                 |                   |
| :----------- | :------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| **`FLAG 1`** | `{At0m1c_Ut0p1a_1955}`    | Returned directly via the `FLAG 1` serial command (`0x10010300`).                                                                                                                                                                                                                                                                                |                   |
| **`FLAG 2`** | `{R4ygun_G0th13_Ph4s3}`   | On the CLI, `FLAG 2` checks for an external hardware EEPROM containing the 4-byte magic header `"PLUM"` (`0x10027db0`). Inspecting the firmware around that check revealed a 21-byte obfuscated array at flash offset `0x280bc`. Each byte `b` at index `i` (`0..20`) decodes via:<br>`x = ((b ^ i ^ 0xA5) + 3 * i) & 0xFF`<br>`char = ((x << 3) | (x >> 5)) & 0xFF` |
| **`FLAG 3`** | `{Rusty_C0d3_1s_4w3s0m3}` | Sending `FLAG 3` on the CLI outputs masked asterisks (`Flag: ***********************`). Inspecting the flash strings adjacent to the `FLAG` handler in `badge_backup.bin` revealed the plaintext flag stored at offset `0x28070` (`0x10028070`).                                 |                   |

---

## 3. All 32 Achievements & 30 `UNLOCK` Codes

The badge tracks **32 achievements** (`Slots 0–31`):
- **Slots `0` and `1`** have target hash `0x0000000000000000` and are unlocked exclusively through in-game actions.
- **Slots `2` through `31`** (all 30 conference achievements) are backed by 64-bit hashes in SRAM at `0x20001718`–`0x20001807` (initialized from flash offset `0x1762b4`–`0x1763a3`). Slots `2`–`8` and `12` can *also* be unlocked via in-game triggers (`0x1000e198`).

| Slot | Achievement Name | `UNLOCK` Code | Target 64-Bit Hash | How Found / In-Game Trigger |
| ---: | :--- | :--- | :--- | :--- |
| **0** | **Thirty Lives** | *(In-game only)* | `0x0000000000000000` | Enter the 10-step Konami Code (**Up, Up, Down, Down, Left, Right, Left, Right, B, A**) on the badge buttons (`0x1000dd3e`) |
| **1** | **First Departure** | *(In-game only)* | `0x0000000000000000` | Launch your first Orion Trail voyage (`0x100033e4`) |
| **2** | **Frequent Flyer** | `SC_VECTOR_BURN` | `0xa60d149ba625229f` | Hash reversal *(or in-game distance `>= 9000` at `0x10003cf4`)* |
| **3** | **Relics of the First Builders** | `SC_NOVA_TRACE` | `0x2e0bf85ad010dbb2` | Hash reversal *(or in-game landmark event 0 at `0x10001c52`)* |
| **4** | **The Obsidian Monolith** | `SC_ION_WAKE` | `0x4750921fb1958f66` | Hash reversal *(or in-game landmark event 1 at `0x10001c52`)* |
| **5** | **Full Complement** | `SC_SOLAR_SHEAR` | `0x666d527fb94e3da0` | Hash reversal *(or recruit a full crew of 5 at `0x100039d2`)* |
| **6** | **A Crew of Specialists** | `SC_PLASMA_ARC` | `0x80a5aedb8684c3b4` | Hash reversal *(or 5 crew with all 5 distinct roles: Pilot, Engineer, Scientist, Soldier, Medic at `0x10003a3c`)* |
| **7** | **Signed On** | `SC_VOID_VECTOR` | `0x54cd46567937ecbd` | Hash reversal *(or badge-to-badge crew sign-on at `0x10003ce2`)* |
| **8** | **Works Well With Others** | `SC_STAR_OFFSET` | `0xc327e386d9189b63` | Hash reversal *(or badge-to-badge crew recruitment at `0x10003d00`)* |
| **9** | **Civic Duty** | `SC_ORBIT_DECAY` | `0xd1ff3ce39c469e68` | Hash reversal |
| **10** | **Deep Storage** | `SC_THRUST_LOSS` | `0x3c317b15e7c1e29d` | Found in plaintext in flash at `0x28239` |
| **11** | **Long-Term Memory** | `SC_SIGNAL_GHOST` | `0xa1d4a114f76211b7` | Found XOR-encoded with `0x55` in flash at `0x27574` |
| **12** | **Manual Override** | `SC_ECHO_ORBIT` | `0x95c911db5174adae` | Hash reversal *(or enable Offline Mode at `0x10000576`)* |
| **13** | **Service Port** | `SC_DUST_FLUX` | `0x236c4a02f5b53468` | Listed in serial `HELP` output |
| **14** | **Dockmaster's Channel** | `SC_PHASE_DRIFT` | `0xca5d48f6551e91a6` | Found XOR-encoded with `0x57` in flash at `0x27bf0` |
| **15** | **Misaligned Home Row** | `SC_GRAV_SHIFT` | `0x3b21dd157c302499` | Starfield banner `DV+HTSB+DJOGY` shifted 1 key left on QWERTY |
| **16** | **Diagnostics Complete** | `SC_CORE_FLUX` | `0x2b649143bd4140b1` | Conference clue + verified against hash |
| **17** | **Circles Within Circles** | `SC_LAGRANGE_LOCK` | `0x73d4fbc7ac29b3ff` | Conference clue + verified against hash |
| **18** | **Connect the Dots** | `SC_PULSE_FIELD` | `0x187b1fcf223c7378` | Hash reversal |
| **19** | **Know a Guy** | `SC_FIELD_ECHO` | `0x1d3ba22e7f078e03` | Hash reversal |
| **20** | **Synthetic Minds** | `SC_QUANTUM_WAKE` | `0x5d0f1b55a201937e` | Hash reversal |
| **21** | **Attack Surface Survey** | `SC_DEEP_PARALLAX` | `0x3260bcce868c358c` | Hash reversal |
| **22** | **Fabric of Reality** | `SC_RADIAL_DRIFT` | `0xa3ffa1442b62a8b9` | Hash reversal |
| **23** | **Blue Skies Ahead** | `SC_COSMIC_BIAS` | `0xfd4dcde6773030f5` | Hash reversal |
| **24** | **Bare Metal** | `SC_FLUX_VECTOR` | `0x72b59e0887bae55c` | Hash reversal |
| **25** | **Sick Bay** | `SC_ORBIT_TRACE` | `0xbd21f31f1860e478` | Hash reversal |
| **26** | **Domestic Infrastructure** | `SC_ASTRA_SHIFT` | `0x5bb3c9f2243bcbdd` | Hash reversal |
| **27** | **Identity Crisis** | `SC_ZENITH_DRIFT` | `0x36ee9016f26b3c8d` | Hash reversal |
| **28** | **Open Access** | `SC_ECHO_VECTOR` | `0x70dd514041fafbf3` | Hash reversal |
| **29** | **Off the Record** | `SC_DRIFT_LOCK` | `0xb377e54b5a08a833` | Hash reversal |
| **30** | **Seal Broken** | `SC_APOGEE_DRIFT` | `0x6c01b05f902d9e09` | Hash reversal |
| **31** | **The Watchtower** | `SC_PERIGEE_SHIFT` | `0xfccc75461d4f2fe2` | Hash reversal |

---

## 4. Custom 64-Bit Hash Algorithm (`0x10010a9c`) & EEPROM State Layout

### A. `badge_hash64` Implementation (`0x10010a9c`)
Used both for validating `UNLOCK` codes (`0x1000e0d0`) and computing the 8-byte integrity checksum of the 32-byte EEPROM state structure (`0x200021a8`). It uses the 64-bit seed `0x50726f66506c756d` (`"PlumProf"` in little-endian ASCII):

```python
def badge_hash64(data: bytes, seed: int = 0x50726f66506c756d) -> int:
    MASK64 = 0xFFFFFFFFFFFFFFFF
    C_INIT = 0x85ebca77c2b2ae63
    M1     = 0x27d4eb2f165667c5
    A1     = 0x9e3779b97f4a7c15
    M2     = 0xc2b2ae3d27d4eb4f
    A2     = 0x165667b19e3779f9

    h = (seed ^ C_INIT) & MASK64
    length = len(data)
    idx = 0

    while idx + 8 <= length:
        k = int.from_bytes(data[idx:idx+8], "little")
        h ^= k
        h = (h * M1 + A1) & MASK64
        idx += 8

    rem = length - idx
    if rem > 0:
        tail = int.from_bytes(data[idx:], "little")
        h ^= tail
    h = (h * M1 + A1) & MASK64

    h ^= length
    h = (h * M2 + A2) & MASK64
    h ^= (h >> 33)
    h = (h * M1 + A1) & MASK64
    h ^= (h >> 29)
    h = (h * M2 + A2) & MASK64
    h ^= (h >> 32)
    return h & MASK64
```

### B. Persistent State Structure (`0x200021a8` in SRAM / `0x0010` in EEPROM)

| Offset | Size | Field | Description |
| :--- | :--- | :--- | :--- |
| `0x00`–`0x0E` | 15 bytes | `handle[15]` | Null-terminated ASCII handle (`"BrainVirus"`) |
| `0x0F` | 1 byte | `player_class` | `'A'`=Pilot, `'B'`=Engineer, `'C'`=Scientist, `'D'`=Soldier, `'E'`=Medic |
| `0x10`–`0x13` | 4 bytes | `achievement_bitmask` | `uint32_t` bitmask (`1 << slot` for `slot` in `0..31`) |
| `0x14`–`0x17` | 4 bytes | `counters` | Game state counters (e.g., byte `0x16` = voyage count) |
| `0x18`–`0x1F` | 8 bytes | `checksum` | `badge_hash64(bytes[0..23], seed=0x50726f66506c756d)` |

---

## 5. Addressable RGB LED Architecture & Manual Control

### A. Hardware Details
- **LED Type & Count:** **9 × WS2812 (NeoPixel) RGB LEDs** (`27` bytes framebuffer at SRAM `0x20002210`).
- **Controller & Pin:** Driven by **`PIO0` (`0x50200000`) State Machine 0** on **GPIO 24** (`0x18`), initialized by `ws2812_init` at `0x10010500` using the 4-instruction `ws2812.pio` program at flash offset `0x16dd38` (`0x6321, 0x1223, 0x1200, 0xa242`).
- **Pixel Format:** Standard 24-bit GRB (`(G << 24) | (R << 16) | (B << 8)`) written to `PIO0->txf[0]` inside `led_update` (`0x10010670`).

### B. How the Firmware Drives the LEDs
1. **Base Color (`0x20001830`, 3 bytes `[R, G, B]`):**
   Set on boot (`0x1000054c`–`0x100005dc`) via `led_set_base_color(uint32_t rgb)` (`0x10010624`) according to your `player_class` byte (`[0x200021a8 + 0x0f]`):
   - `'A'` (**Pilot**): `(R=0x00, G=0x00, B=0x10)` — **Blue**
   - `'B'` (**Engineer**): `(R=0x10, G=0x06, B=0x00)` — **Orange / Gold**
   - `'C'` (**Scientist**): `(R=0x10, G=0x10, B=0x10)` — **White**
   - `'D'` (**Soldier**): `(R=0x00, G=0x10, B=0x00)` — **Green**
   - `'E'` (**Medic**): `(R=0x10, G=0x06, B=0x06)` — **Red / Pink**
   - Default (Unassigned): `(R=0x10, G=0x00, B=0x10)` — **Purple / Magenta**
2. **Animation Frames (`0x1016dd24`):**
   A repeating timer callback (`0x100108a8` → `0x10010670`) steps `frame_idx` (`0..4` at `0x20044a79`) through the 9-bit LED bitmask table at flash offset `0x16dd24`:
   - Frame 0: `0x080` (LED 7)
   - Frame 1: `0x140` (LEDs 6, 8)
   - Frame 2: `0x021` (LEDs 0, 5)
   - Frame 3: `0x012` (LEDs 1, 4)
   - Frame 4: `0x00c` (LEDs 2, 3)
3. **Animation Speed (`170 - 5 * unlocked_achievements` ms):**
   Both `0x10010624` and `0x100108b4` call `get_achievement_count()` (`0x1000e070`) and set the repeating timer period to `170 - 5 * count` ms (`170 ms` with 0 achievements down to `10 ms` with all 32 achievements unlocked).
4. **Event Flash Override (`0x100108b4`):**
   Calling `0x100108b4(uint32_t rgb)` sets `blink_counter = 3` (`0x20002c78`) and `override_rgb = rgb` (`0x20002c7c`), flashing all 9 LEDs with `override_rgb` for 3 cycles:
   - New achievement unlocked (`0x1000e154`): `0x00200020` (**Bright Purple**)
   - Invalid unlock code (`0x1000e16c`): `0x00000020` (**Bright Red**)
   - Dock/voyage sync (`0x1000e2ba`): `0x00002000` (**Bright Green**)

### C. How to Manually Control the LEDs
1. **Trigger LED Flashes Over USB Serial (`/dev/ttyACM0`):**
   - Sending `UNLOCK <any_invalid_string>` over `/dev/ttyACM0` calls `0x100108b4(0x00000020)`, immediately flashing all 9 LEDs **Red** for 3 cycles.
2. **Change the Persistent Base Color:**
   - Selecting or changing your player class (`Pilot`, `Engineer`, `Scientist`, `Soldier`, `Medic`) updates `[0x200021a8 + 0x0f]`, changing the base color of the LED animation between Blue, Orange, White, Green, and Red/Pink.
3. **Custom RGB Colors / Patterns via Firmware Patch (`picotool`):**
   - **Animation Bitmasks:** The five 16-bit halfwords at file offset `0x16dd24` (`[0x0080, 0x0140, 0x0021, 0x0012, 0x000c]`) control which of the 9 LEDs (`bits 0..8`) light up on each step. Setting all 5 halfwords to `0x01ff` keeps all 9 LEDs solidly lit.
   - **Adding a Custom `LED` Serial Command:** Because the CLI parser at `0x10010180` has direct access to `0x10010624` (`led_set_base_color`) and `0x100108b4` (`led_trigger_flash`), a tiny patch to `badge_backup.bin` (flashed via `picotool load`) can repurpose or extend the serial CLI to accept arbitrary `(R, G, B)` values over `/dev/ttyACM0`.
