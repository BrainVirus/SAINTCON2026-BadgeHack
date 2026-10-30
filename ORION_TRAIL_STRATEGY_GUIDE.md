# SAINTCON 2026 Badge: *Orion Trail* Strategy & Mechanics Guide

Reverse-engineered game mechanics, formulas, and high-score strategy for the *SAINTCON Orion Trail Edition* space RPG on the **SAINTCON 2026 Conference Badge** (Raspberry Pi RP2350 / Pico 2).

> [!NOTE]
> **AI Collaboration Notice:** The game formulas, encounter event tables, and mathematical models in this guide were extracted and analyzed with the assistance of AI (Google DeepMind's Antigravity).

---

### *Fun Fact: The Internal Project Name is Actually Wayfarer!*
While the badge's circular LCD displays **"SAINTCON ORION TRAIL EDITION"**, the badge developer internally named the project **`Wayfarer`** in their Raspberry Pi Pico SDK `CMakeLists.txt`.

Inspecting the raw flash binary with `picotool info` reveals the embedded program metadata:
```text
Program Information
 name:          Wayfarer
 version:       0.1
 build date:    Aug 16 2026
 target chip:   RP2350
```

---

## 1. The Final Score Formula

When you return to the center **Space Station at `(0, 0)`** carrying at least `1` unit of Cargo (`[G + 0xc0] > 0`), the voyage concludes and calculates your final score (`0x100033ae`–`0x100033c8`):

$$\text{Final Score} = (300 \times \text{Cargo}) + \text{Reputation} + \text{XP} + (10 \times \text{Crew Count})$$

### Core Rules Derived from Assembly:
1. **Unspent Credits (`$`), Fuel, and Hull are worth 0 points:** Any remaining Credits in your wallet at mission end evaporate without adding to your score. Credits exist solely as working capital.
2. **Cargo Base Score:** Maximum hold capacity is **24 units** (`24 × 300 = 7,200 base points`). Never dock at `(0, 0)` with cargo until your hold is at `24/24` (unless facing imminent death).
3. **Uncapped Score Terms (XP & Reputation):** Because Cargo caps at `24` (7,200 pts) and Crew caps at `5` (50 pts), the only unbounded components of your final score are **XP** (`[G + 0xc8]`) and **Reputation** (`[G + 0xc4]`), earned from Random Space Encounters.
4. **No Turn Limit:** Moving between adjacent hexes costs **1 Fuel** (`0x100027b4`). As long as Hull, Fuel, and Crew remain above 0, the voyage can continue indefinitely.

---

## 2. All-Achievements Starting Advantage & Optimal Build

In `new_game_init` (`0x10001070`), starting funds scale directly with your unlocked achievement count:

$$\text{Starting Credits} = 1,000 + (150 \times \text{Unlocked Achievements})$$

With all **32 achievements unlocked**, every new run starts with **$5,800 Credits** (up from the base $1,000).

### Pre-Departure Upgrades (`0x10002fd0`–`0x10003030`)
Before selecting **START MISSION**, max out both ship systems:

| Upgrade | Base → Max | Cost per Level $L$ | Total Upgrade Cost | Advantage |
| :--- | :---: | :---: | :---: | :--- |
| **Fuel Tank** | `5 → 15` | $25 \times L$ | **$2,625** | Grants 15/15 fuel capacity. Each full outpost refuel covers 15 hexes. |
| **Hull Armor** | `3 → 8` | $30 \times L$ | **$900** | Grants 8/8 hull capacity. Withstands major event penalties (-3 Hull) and asteroid impacts (-2 Hull). |
| **Total** | **15 Fuel / 8 Hull** | — | **$3,525** | Leaves **$2,275 in cash** for trading and operations. |

---

## 3. The Zero-Cargo Station Refuel Exploit (`0x10003326`–`0x10003352`)

Landing on the center **Space Station `(0, 0)`** triggers specific branch conditions based on cargo and cash:
* **`Cargo > 0`:** Mission completes; final score is computed and written to EEPROM.
* **`Cargo == 0` and `Credits <= 400`:** Mission fails with *"No Credits"*.
* **`Cargo == 0` and `Credits > 400`:** The station displays *"You are back at the space station. Buy some cargo from outposts to complete your mission."* and executes `0x10003348`:
  * **Both Fuel (`15/15`) and Hull (`8/8`) are refilled to 100% capacity for FREE.**

### Phase 1 Infinite Farming Route:
1. Start the mission with **0 Cargo**. Do not purchase cargo and decline/dump cargo from events.
2. Fly in loops through empty space hexes near the center station to trigger encounters (each step on empty space has a **33.3% / 1-in-3 chance** to trigger an event at `0x100035d0`).
3. While holding 0 Cargo, events that penalize `Cargo -5` or `Cargo -10` have **zero effect**, as Cargo clamps at 0 (`0x10001c5e`).
4. Whenever Fuel or Hull runs low (provided Credits remain $> \$400$), return to `(0, 0)` for a complete refuel and repair, then continue farming XP and Reputation.

---

## 4. Crew Persistence & Recruitment Mechanics

In `new_game_init` (`0x100011f8`), the game checks if `crew_count != 0`:
* If crew members survived your previous run, **the game preserves them into the next run** until they perish in an encounter or the badge is power-cycled.
* Having specialists unlocked enables gold/cyan 4th event choices with **80%–85% success rates**.

### Recruitment Events:
1. **An Unexpected Passenger:** Select **Choice 3: `Let them stay`** (60% chance: `Crew +1`, 40% chance: `Hull -1`).
2. **Relics of the First Builders:** If you have a Medic (`Class E`), select **Choice 3: `Scan for lifeforms (Medic)`** (80% chance: `Crew +1`, 20% chance: `Hull -2`).

---

## 5. Outpost Trading & Market Math (`0x10002c24`–`0x10002cf8`)

Every sector generates **9 Outposts** across price brackets from **$100–$149** (`Surplus`/`Glut`) to **$500–$549** (`Crisis`):
* **Refueling:** Costs a flat **$25 per unit of Fuel** ($375 for a complete 15-unit fill) regardless of local price tiers.
* **Buying Cargo:** Costs the listed price $P$ and increases subsequent prices at that outpost:
  $$P_{\text{new}} = \lfloor 1.15 \times P + 1 \rfloor$$
* **Selling Cargo:** Sells at **75% of listed price** ($\lfloor 0.75 \times P \rfloor$) and depresses local prices:
  $$P_{\text{new}} = \lfloor 0.90 \times P \rfloor$$

### Trading Guidelines:
* Never buy and sell at the same outpost due to the 25% spread.
* To generate cash: Buy at `Surplus`/`Glut` outposts ($P \approx \$100\text{--}\$180$), then sell at `Desperate`/`Crisis` outposts ($P \approx \$450\text{--}\$550$, selling for $\approx \$340\text{--}\$410$).
* **Phase 2 Cash-Out:** Once satisfied with farmed XP and Reputation, visit low-tier outposts to load **24/24 Cargo** (7,200 pts), top off fuel, and fly into `(0, 0)` to finish.

---

## 6. Mini-Game Rewards & Hazards

| Hazard | Success | Failure | Behavior | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Nebula** (`0x10006168`) | **+$300 Credits** | **-2 Fuel** | Remains on map | Bypass unless seeking fast early credits; failure burns 2 fuel units ($50 value). |
| **Asteroid Field** (`0x10005068`) | **+$50 to +$200+ Credits** (per hit) | **-2 Hull** | **Permanently cleared** on victory (`0x100034c8`) | Clear when blocking straight corridors between `(0, 0)` and trading hubs. |

---

## 7. High-Value Event Choices

Always select the **Specialist (Choice 4)** when available, except where failure endangers crew lives and a safe fallback exists.

### Survival Rules (Avoid Crew Losses):
* **Giant Spider Infestation:** Choose **`Seal and abandon`** (`100% Reputation -50`) unless accompanied by a **Scientist** (`80% Credits +600, XP +20`). Avoid *Fight them off* (guaranteed 100% risk of losing 1–2 Crew).
* **Space Plague Strikes:** Choose **`Rest`** (`60% XP +50 / 40% XP -50`, 0% crew death) or **`Treat illness (Medic)`**. Avoid *Push on* (40% Crew -1).
* **Derelict Trap:** Choose **`Avoid it`** (`90% Reputation +10`, 0% crew death).
* **Medical Emergency Supply Cost:** Choose **`Use generic medicine`** (-$50 or -$300, 0% crew death) or **`Buy the expensive drugs`**.

### High-Yield Encounters:
* **Mutiny Brewing Below Decks:** **`Mediate`** yields **100% guaranteed +100 to +200 XP** (+200 to +400 XP with Medic).
* **Silence Across the Void:** **`Wait`** yields **100% guaranteed +50 to +100 XP** (80% Cargo +4 with Engineer).
* **The Dying Freighter:** **`Give them 3 Fuel`** yields a 70% chance of **`Cargo +10`** (+3,000 score pts) or 30% chance of **`XP +200`** for 3 fuel units ($75 value).
* **Fortune in the Deep:** **`Take some`** guarantees **`+2 to +5 Cargo`** without hull damage (**`Scan first (Scientist)`** yields **`+5 to +10 Cargo`** at 100%).
