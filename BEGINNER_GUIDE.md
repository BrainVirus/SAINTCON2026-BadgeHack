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

### 4. CTF Flags: Testing the Waters
Many conference badges have hidden commands. If you query `FLAG`:

- **Flag 1:**
  ```text
  > FLAG 1
  Flag: {At0m1c_Ut0p1a_1955}
  ```
  **Flag 1 captured!** Just like that, the first flag is returned directly in plaintext.

- **Flag 2:**
  ```text
  > FLAG 2
  Flag: INVALID
  ```
  The badge rejects the request. Does it require special credentials or external hardware?

- **Flag 3:**
  ```text
  > FLAG 3
  Flag: ***********************
  ```
  Twenty-three asterisks stare right back at you! The badge knows the flag exists, but it deliberately masks it out.

To capture **Flag 2** and **Flag 3**, we will need to dump the firmware and look under the hood in Phase 6.

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

## Phase 6: Reverse Engineering the Firmware: Flags 2 & 3 and Finding "PlumProf"

Now that we dumped `badge_backup.bin` in Phase 5, we have the complete, unencrypted flash filesystem. This is where hardware hacking turns into software reverse engineering and binary forensics.

### 1. Capturing Flag 3: The Decoy Bait & The Real GOST Cipher (`0x280a0`)

Recall that running `FLAG 3` in Phase 2 printed:
```text
> FLAG 3
Flag: ***********************
```

#### The Decoy Trap (`{Rusty_C0d3_1s_4w3s0m3}`)
If you run `strings badge_backup.bin | grep "{"`, the first string that immediately appears in the flash image is:
```text
{Rusty_C0d3_1s_4w3s0m3}
```
At first glance, it looks like an easy win—the string sits in plaintext at flash offset `0x28070` (`0x10028070`), and at address `0x10010026`, the firmware initially loads it into the output buffer.

> [!IMPORTANT]
> **Credit:** Massive thanks to **`r3tr0hck342`** for pointing out that `{Rusty_C0d3_1s_4w3s0m3}` is actually a decoy trap and discovering the real GOST/Magma cipher implementation!

**This string is an intentional decoy!** Every single command path (`FLAG 1`, `FLAG 2`, `FLAG 3`, or syntax error) immediately overwrites the buffer before printing. The decoy string is *never* printed under any condition. It exists solely to trap anyone relying on naive static string searches.

#### The Real Flag 3: GOST 28147-89 (Magma) Decryption
When `FLAG 3` is entered (`0x100102fe`):
1. The firmware loads **24 encrypted bytes** from flash address `0x100280a0` (file offset `0x280a0`).
2. It initializes the **GOST 28147-89 (Magma)** block cipher—a 64-bit Feistel cipher—using the 256-bit key from flash offset `0x1763ac` (mapped to `0x20001810` in SRAM) and S-boxes at `0x1016ddc0` (`0x16ddc0`).
3. It runs three 8-byte blocks through 32 rounds of Feistel decryption, recovering the real plaintext: **`{Fly1ng_C4r_Pr0m1s3}`** (padded with 4 bytes of PKCS#7 `\x04`).
4. *Only after* decrypting the real flag in RAM does the firmware execute this troll right before printing:
```armasm
10010326:  mov.w r3, #0x2a2a2a2a      ; 0x2A is ASCII for '*' ('****')!
1001032a:  str   r3, [sp, #48]
1001032c:  strd  r3, r3, [sp, #32]    ; deliberately overwrites the buffer with asterisks!
10010330:  strd  r3, r3, [sp, #40]
10010338:  b.n   0x1001008a           ; jumps to print "Flag: ***********************"
```

#### How to Decrypt the Real Flag 3:
Because the ciphertext, round keys, and S-boxes are all in `badge_backup.bin`, we can decrypt the true flag statically in Python:

```bash
python3 -c "
import struct
with open('badge_backup.bin', 'rb') as f:
    data = f.read()

sbox = data[0x16ddc0 : 0x16ddc0 + 128]
K = struct.unpack('<8I', data[0x1763ac : 0x1763ac + 32])
idx = struct.unpack('<32I', data[0x16dd40 : 0x16dd40 + 128])
ct = data[0x280a0 : 0x280a0 + 24]

def f_step(x, k):
    s = (x + k) & 0xFFFFFFFF
    res = 0
    for i in range(8):
        res |= (sbox[i * 16 + ((s >> (4 * i)) & 0xF)] << (4 * i))
    return ((res << 11) | (res >> 21)) & 0xFFFFFFFF

pt = bytearray()
for b in range(0, 24, 8):
    L, R = struct.unpack('<2I', ct[b:b+8])
    for rnd in range(32):
        L, R = R ^ f_step(L, K[idx[rnd]]), L
    pt.extend(struct.pack('<2I', R, L))

pad = pt[-1]
flag3 = pt[:-pad].decode('ascii')
print(f'Real Flag 3: {flag3}')
"
```

**Output:**
```text
Real Flag 3: {Fly1ng_C4r_Pr0m1s3}
```
**True Flag 3 captured!**

*(You can also run [`scripts/decrypt_flags.py`](./scripts/decrypt_flags.py) to automatically extract and decrypt all 3 flags and print the honeypot analysis).*

---

### 2. Capturing Flag 2: The "PLUM" EEPROM Bypass (`0x280bc`)

When we entered `FLAG 2` on the CLI in Phase 2, the badge replied:
```text
> FLAG 2
Flag: INVALID
```

Looking at the disassembly of the `FLAG 2` branch at `0x1001033a`:
1. The badge performs an I2C read of the first 8 bytes of an external memory chip (`0x1000e33c`).
2. At `0x10010348`, it compares the first 4 bytes against `0x4d554c50`—which is ASCII for **`"PLUM"`**!
3. If the chip does not return `"PLUM"`, it prints `Flag: INVALID`.
4. If `"PLUM"` is detected, it loads a 21-byte scrambled array from flash address `0x100280bc` (offset `0x280bc`) and decrypts it on the fly.

```armasm
10010344:  ldr   r3, [pc, #136]       ; loads 0x4d554c50 ("PLUM" in ASCII) from 0x100103d0
10010346:  ldr   r2, [sp, #0]         ; loads first 4 bytes returned from I2C EEPROM
10010348:  cmp   r2, r3               ; Does the external chip say "PLUM"?
1001034a:  beq.n 0x10010358           ; Match -> jump to decryption routine!
1001034e:  ldr   r1, [pc, #132]       ; No match -> loads pointer to string "INVALID"
...
1001035a:  ldr   r6, [pc, #124]       ; loads address 0x100280bc (flash offset 0x280bc)
```

We don't need any special hardware or an external chip—the scrambled 21 bytes and the decryption routine are already inside our firmware dump!

At offset `0x280bc`, the scrambled bytes are:
```python
[202, 227, 39, 128, 65, 63, 24, 116, 125, 71, 223, 66, 171, 151, 106, 119, 104, 231, 143, 155, 194]
```

The assembly routine decodes each byte `b` at index `i` (`0..20`) using an XOR with `0xA5`, an index offset (`+ 3 * i`), and a 3-bit left rotate:
```python
x = ((b ^ i ^ 0xA5) + 3 * i) & 0xFF
char = ((x << 3) | (x >> 5)) & 0xFF  # 3-bit left rotate
```

You can decode Flag 2 instantly from `badge_backup.bin` with this one-liner:

```bash
python3 -c "
data = open('badge_backup.bin', 'rb').read()[0x280bc:0x280bc+21]
flag = ''.join(chr(((((b ^ i ^ 0xA5) + 3 * i) & 0xFF) << 3 | (((b ^ i ^ 0xA5) + 3 * i) & 0xFF) >> 5) & 0xFF) for i, b in enumerate(data))
print(flag)
"
```

**Output:**
```text
{R4ygun_G0th13_Ph4s3}
```
**Flag 2 captured!** All 3 conference CTF flags are now solved.

---

### 3. Where & How We Found `"PlumProf"` (The Custom 64-Bit Hash)

With the CTF flags solved, our next target was the **30 locked conference achievements**.

When you run `strings` on `badge_backup.bin`, almost none of the secret codes appear. The badge doesn't store the secret unlock words in plaintext.

Instead, disassembling the `UNLOCK <code>` command handler at address `0x1000e0d0` reveals how verification works:

```armasm
1000e0d6:  mov   r4, r0             ; r4 = pointer to user's UNLOCK string
1000e0d8:  bl    0x10013e98         ; calls strlen(input)
1000e0dc:  add   r3, pc, #160       ; r3 = 0x1000e180 (the literal pool)
1000e0de:  ldrd  r2, r3, [r3]       ; loads 64-bit constant from 0x1000e180 into r2 and r3!
1000e0e2:  mov   r1, r0             ; r1 = string length
1000e0e4:  mov   r0, r4             ; r0 = string pointer
1000e0e6:  bl    0x10010a9c         ; calls badge_hash64(str, len, seed)!
1000e0ea:  movs  r4, #2             ; loop counter: start at achievement Slot 2
1000e0ec:  ldr   r3, [pc, #152]     ; loads address of target hashes in RAM (0x20001710)
```

#### Where Did `"PlumProf"` Come From?
Look closely at instruction `0x1000e0de`:
```armasm
ldrd r2, r3, [r3]    ; loads 8 bytes from address 0x1000e180
```
This instruction loads an 8-byte (64-bit) constant from the literal pool at address `0x1000e180` (file offset `0xe180` in `badge_backup.bin`).

If we inspect those 8 bytes at file offset `0xe180`:
```text
Offset 0x0000E180:  6d 75 6c 50  66 6f 72 50
```
Because ARM is little-endian, reading these as two 32-bit words gives:
- Word 1 (`r2`): `0x506c756d` $\rightarrow$ ASCII bytes `'P'`, `'l'`, `'u'`, `'m'` (**`"Plum"`**)
- Word 2 (`r3`): `0x50726f66` $\rightarrow$ ASCII bytes `'P'`, `'r'`, `'o'`, `'f'` (**`"Prof"`**)

Combined into a single 64-bit integer, the seed is:
$$\mathbf{0x50726f66506c756d} \Longleftrightarrow \mathbf{\text{"PlumProf"}}$$

The badge author (who already hid the `"PLUM"` check in Flag 2) used the alias of the classic *Clue* character **Professor Plum** (`"PlumProf"`) as the secret seed for the badge's custom hash function!

---

### 4. Cracking All 30 Hashes with a Space Dictionary

The function at `0x10010a9c` is a custom 64-bit mixing algorithm (similar to xxHash). It takes your input word and hashes it using the `"PlumProf"` seed.

The loop in `0x1000e0f0`–`0x1000e102` then compares your calculated 64-bit hash against a table of **thirty 64-bit target hashes** stored in SRAM (`0x20001718`–`0x20001807`, loaded from flash `0x1762b4`):
- If the hash matches entry `i`, achievement `i` is unlocked and written to the badge's EEPROM.

Because we now had both the **algorithm** (`0x10010a9c`) and the **seed** (`"PlumProf"` / `0x50726f66506c756d`), we reconstructed the hash in Python. All unlock codes followed the pattern:
$$\mathbf{SC\_<WORD1>\_<WORD2>}$$

We fed standard sci-fi and space navigation terms (`VECTOR`, `ORBIT`, `DRIFT`, `NOVA`, `PULSE`, `FLUX`, `SIGNAL`, etc.) into a Python dictionary generator. Within seconds, all 30 64-bit target hashes collided, giving us the full list of secret codes:

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
   - **Flag 1:** `{At0m1c_Ut0p1a_1955}` *(XOR 0xCC @ `0x10028088`, printed via CLI)*
   - **Flag 2:** `{R4ygun_G0th13_Ph4s3}` *(Deobfuscated from firmware byte table @ `0x100280bc`, EEPROM gated)*
   - **Flag 3:** `{Fly1ng_C4r_Pr0m1s3}` *(Decrypted via GOST 28147-89 / Magma @ `0x100280a0`; special credit to `r3tr0hck342`)*
   - **Decoy:** `{Rusty_C0d3_1s_4w3s0m3}` *(Unused plaintext strings bait @ `0x10028070`)*
2. **Achievements Unlocked:** 32 / 32 (30 via serial script + Konami Code + First Departure).
3. **In-Game Reward:** Starting *Wayfarer* with **₡5,800 credits** and all **5 specialist crew members**!
