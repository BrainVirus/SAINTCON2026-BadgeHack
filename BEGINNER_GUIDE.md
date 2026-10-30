# Beginner's Guide to Hacking the SAINTCON 2026 Badge
### A Step-by-Step Walkthrough for IT and InfoSec Professionals

> [!NOTE]
> **AI Collaboration Notice:** This beginner's guide, firmware analysis, and automation tooling were researched and developed with the assistance of AI (Google DeepMind's Antigravity).

If you are an IT administrator, sysadmin, SOC analyst, or security engineer, you already know Linux, networking, scripting, and authentication concepts. But when you are handed a physical circuit board at a conference, it can feel like a completely foreign world of oscilloscopes, soldering irons, and obscure protocols.

Here is the secret: **Conference hardware hacking is just systems administration and input testing over a wire.**

You do not need a soldering iron, a hardware probe, or special chip clips. Everything in this guide is done with a standard USB-C cable and your regular Linux terminal.

---

## Architecture at a Glance (The Hardware Stack)

Before typing commands, here is how the physical badge maps to concepts you already know:

| Hardware Component | What It Is | Equivalent IT Concept |
| :--- | :--- | :--- |
| **RP2350 (Raspberry Pi Pico 2)** | ARM Cortex-M33 32-bit Microcontroller | The CPU / Server |
| **2 MB QSPI Flash Memory** | Non-volatile flash storage mapped at `0x10000000` | The Hard Drive / Root Filesystem (holds the OS & game binary) |
| **520 KB SRAM** | Volatile system memory starting at `0x20000000` | System RAM (holds active game state, crew roster, framebuffer) |
| **1 KB I2C EEPROM (`0x50`)** | Small non-volatile memory chip | `/etc/passwd` / Configuration NVRAM (stores your handle, save game, and unlocked achievement bitmask) |
| **USB CDC Port (`/dev/ttyACM0`)** | Virtual serial interface exposed over USB-C | An unauthenticated SSH shell or Cisco serial console cable |
| **360×360 Round LCD & 9 LEDs** | SPI display & WS2812 addressable RGB LEDs | Monitor & Server Status LEDs |

---

## Phase 1: First Contact (Plugging in the Badge)

### 1. Identify the USB Device
Connect the badge to your Linux laptop using a USB-C data cable. Check `dmesg`:

```bash
dmesg | tail -n 20
```

You will see the Raspberry Pi Pico CDC serial device appear and bind to a virtual COM port:
```text
cdc_acm 1-2:1.0: ttyACM0: USB ACM device
```

In Linux, serial devices live in `/dev/ttyACM*` or `/dev/ttyUSB*`. Check permissions:
```bash
ls -l /dev/ttyACM0
```
*(If your user cannot read/write `/dev/ttyACM0`, add yourself to the serial group: `sudo usermod -aG dialout $USER` or `uucp` depending on your Linux distro, then log back in).*

### 2. Connect to the Badge Terminal
You don't need proprietary software to talk to microcontrollers. Use any standard terminal emulator at 115,200 baud (or 9600):

```bash
# Option A: using picocom (lightweight, Ctrl+A then Ctrl+X to exit)
picocom -b 115200 /dev/ttyACM0

# Option B: using screen (Ctrl+A then \ to exit)
screen /dev/ttyACM0 115200
```

Press **Enter**. The badge will respond with its interactive shell prompt:
```text
> 
```

---

## Phase 2: Shell Reconnaissance & Built-In Commands

Just like exploring an unknown shell, test basic reconnaissance commands:

```text
> HELP
Commands:
  HELP               - Display this help message
  IDENT              - Identify badge
  HANDLE <name>      - Set player handle
  UNLOCK <code>      - Unlock achievement (e.g. SC_DUST_FLUX)
  CLEAR              - Clear screen
> 
```

### 1. Discovering Your Current Identity
```text
> IDENT
IDENT "Usher Zenith"
```
Every badge starts with a randomly generated sci-fi callsign.

### 2. Renaming Your Handle
You can change your handle at any time. The name is permanently stored into the badge's EEPROM:
```text
> HANDLE BrainVirus
Your new handle is "BrainVirus"
```

### 3. Testing Your First Unlock Code
Notice that `HELP` leaked a sample unlock code: `SC_DUST_FLUX`. Let's enter it:
```text
> UNLOCK SC_DUST_FLUX
UNLOCK: OK
```
The badge flashes its LEDs and buzzes—achievement unlocked! If you enter it again:
```text
> UNLOCK SC_DUST_FLUX
UNLOCK: ALREADY UNLOCKED
```

### 4. CTF Flag 1
Many conference badges have hidden commands. Try querying flags:
```text
> FLAG 1
Flag: {At0m1c_Ut0p1a_1955}
```
**Flag 1 captured!**

---

## Phase 3: The Starfield Cipher (`SC_GRAV_SHIFT`)

Type `CLEAR` in the terminal:
```text
> CLEAR
============================== terminal connected ==============================

                +                           D                       Y           

     D                   T                          J                           

                             S                               G                  

           V                            +                                       

                    H             B                     O                       

================================================================================
> 
```

This looks like random ASCII art, but in security CTFs, nothing is an accident.

### How to Decrypt It:
1. **Column Coordinates:** Notice that every letter sits at a unique horizontal character column across the 80-column terminal. Reading left-to-right by column position gives:
   ```text
   D  V  +  H  T  S  B  +  D  J  O  G  Y
   ```
2. **QWERTY Keyboard Cipher:** Look at a standard QWERTY keyboard. Shift each letter **one key to the left**:
   - `D` $\rightarrow$ `S`
   - `V` $\rightarrow$ `C`
   - `+` $\rightarrow$ `_`
   - `H` $\rightarrow$ `G`
   - `T` $\rightarrow$ `R`
   - `S` $\rightarrow$ `A`
   - `B` $\rightarrow$ `V`
   - `+` $\rightarrow$ `_`
   - `D` $\rightarrow$ `S`
   - `J` $\rightarrow$ `H`
   - `O` $\rightarrow$ `I`
   - `G` $\rightarrow$ `F`
   - `Y` $\rightarrow$ `T`
3. Result: **`SC_GRAV_SHIFT`** *(Gravity Shift)*!
4. Send it to the badge:
   ```text
   > UNLOCK SC_GRAV_SHIFT
   UNLOCK: OK
   ```

---

## Phase 4: The Hardware Button Easter Egg (Konami Code)

Not all achievements are unlocked through the keyboard. The badge firmware listens for physical button inputs.

Take the physical badge in your hands. On the directional pad and action buttons, enter the classic **Konami Code**:
$$\mathbf{Up \rightarrow Up \rightarrow Down \rightarrow Down \rightarrow Left \rightarrow Right \rightarrow Left \rightarrow Right \rightarrow B \rightarrow A}$$

The badge screen will display a victory chime and unlock **Slot 0 ("Thirty Lives")**.

---

## Phase 5: Dumping the Firmware (Extracting the Binary)

To discover all remaining secrets, security analysts extract the raw code running on the device.

### What is BOOTSEL Mode?
The Raspberry Pi RP2350 microcontroller has a read-only bootloader burned into silicon at the factory. If you tell it to reboot into BOOTSEL mode, it stops running user code and presents itself as a raw storage interface (`picoboot`).

### How to Dump Flash over USB:
1. You can install the official Raspberry Pi tool:
   ```bash
   sudo apt install picotool  # or build from source
   ```
2. Alternatively, triggering a 1200-baud connection on the serial port commands the Pico SDK to reboot into bootloader mode.
3. Run `picotool` to dump the entire 2 MB flash memory directly to a local binary file:
   ```bash
   sudo picotool save -a badge_backup.bin
   ```
Now you have `badge_backup.bin` on your hard drive!

---

## Phase 6: Cracking the 30 Achievement Hashes

In Linux security, password hashes are stored in `/etc/shadow`. The badge uses the exact same design:
- It maintains an array of **thirty 64-bit target hashes** in firmware memory.
- When you type `UNLOCK <word>`, the badge runs your word through a custom hashing function (`badge_hash64`, seeded with `"PlumProf"` / `0x50726f66506c756d`) and checks if the hash matches any entry in its table.

Because all codes follow the format `SC_<WORD1>_<WORD2>` using common space navigation terms (e.g., `ORBIT`, `VECTOR`, `DRIFT`, `NOVA`, `PULSE`), we ran a dictionary generator in Python that tested space-themed word combinations.

Within seconds, all 30 target hashes collided and yielded the full dictionary of codes:

| Slot | Achievement Title | Secret Code |
| :---: | :--- | :--- |
| **02** | Frequent Flyer | `SC_VECTOR_BURN` |
| **03** | Relics of the First Builders | `SC_NOVA_TRACE` |
| **04** | The Obsidian Monolith | `SC_ION_WAKE` |
| **05** | Full Complement | `SC_SOLAR_SHEAR` |
| **06** | A Crew of Specialists | `SC_PLASMA_ARC` |
| **07** | Signed On | `SC_VOID_VECTOR` |
| **08** | Works Well With Others | `SC_STAR_OFFSET` |
| **09** | Civic Duty | `SC_ORBIT_DECAY` |
| **10** | Deep Storage | `SC_THRUST_LOSS` |
| **11** | Long-Term Memory | `SC_SIGNAL_GHOST` |
| **12** | Manual Override | `SC_ECHO_ORBIT` |
| **13** | Service Port | `SC_DUST_FLUX` |
| **14** | Dockmaster's Channel | `SC_PHASE_DRIFT` |
| **15** | Misaligned Home Row | `SC_GRAV_SHIFT` |
| **16** | Diagnostics Complete | `SC_CORE_FLUX` |
| **17** | Circles Within Circles | `SC_LAGRANGE_LOCK` |
| **18** | Connect the Dots | `SC_PULSE_FIELD` |
| **19** | Know a Guy | `SC_FIELD_ECHO` |
| **20** | Synthetic Minds | `SC_QUANTUM_WAKE` |
| **21** | Attack Surface Survey | `SC_DEEP_PARALLAX` |
| **22** | Fabric of Reality | `SC_RADIAL_DRIFT` |
| **23** | Blue Skies Ahead | `SC_COSMIC_BIAS` |
| **24** | Bare Metal | `SC_FLUX_VECTOR` |
| **25** | Sick Bay | `SC_ORBIT_TRACE` |
| **26** | Domestic Infrastructure | `SC_ASTRA_SHIFT` |
| **27** | Identity Crisis | `SC_ZENITH_DRIFT` |
| **28** | Open Access | `SC_ECHO_VECTOR` |
| **29** | Off the Record | `SC_DRIFT_LOCK` |
| **30** | Seal Broken | `SC_APOGEE_DRIFT` |
| **31** | The Watchtower | `SC_PERIGEE_SHIFT` |

---

## Phase 7: Automated 1-Click Setup Script (`setup_badge.py` / `.sh`)

Instead of manually typing 30 codes and setting your handle by hand into the terminal, we can automate the entire setup over the USB serial interface.

We included [`scripts/setup_badge.py`](./scripts/setup_badge.py) (and wrapper [`scripts/setup_badge.sh`](./scripts/setup_badge.sh)). Run it directly from your terminal with whatever username or hacker alias **you** want on your badge:

```bash
# Option A: Pass your chosen handle directly (replace <YOUR_HANDLE> with whatever name you want):
python3 scripts/setup_badge.py <YOUR_HANDLE>
# or:
./scripts/setup_badge.sh <YOUR_HANDLE>

# Example:
python3 scripts/setup_badge.py Maverick

# Option B: Run it interactively (it will prompt you to type the handle you want):
python3 scripts/setup_badge.py
# or:
./scripts/setup_badge.sh
```

> [!IMPORTANT]
> You do **not** need to type `BrainVirus`! Replace `<YOUR_HANDLE>` with your own preferred handle or hacker alias. The script will write whatever name you choose into your badge's EEPROM.

### Output Example:
```text
Connected to /dev/ttyACM0!

Unlocking all 30 achievements...
  [01/30] Slot 02: Frequent Flyer             -> ✓ OK
  [02/30] Slot 03: Relics of the First Builders -> ✓ OK
  [03/30] Slot 04: The Obsidian Monolith      -> ✓ OK
  ...
  [30/30] Slot 31: The Watchtower             -> ✓ OK

Achievements unlocked: 30/30

Setting handle to "<YOUR_HANDLE>"...
  Your new handle is "<YOUR_HANDLE>"

  Badge identity: IDENT "<YOUR_HANDLE>"

==================================================
✓ All done! Badge handle set to "<YOUR_HANDLE>".
==================================================
```

Your physical badge now has every single conference achievement unlocked and your handle set!

---

## Summary of Achievements & Flags

1. **CTF Flags Captured:**
   - **Flag 1:** `{At0m1c_Ut0p1a_1955}` *(CLI)*
   - **Flag 2:** `{R4ygun_G0th13_Ph4s3}` *(Deobfuscated from firmware byte table)*
   - **Flag 3:** `{Rusty_C0d3_1s_4w3s0m3}` *(Extracted from adjacent flash memory)*
2. **Achievements Unlocked:** 32 / 32 (30 via serial script + Konami Code + First Departure).
3. **In-Game Reward:** Starting *Wayfarer* with **₡5,800 credits** and all **5 specialist crew members**!
