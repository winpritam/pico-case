# 💗 Picocase

### A tiny digital companion living inside a handmade phone case.

**Picocase** is a DIY smart phone-case project that combines **handmade craft, pixel art, OLED animation, an ESP32 microcontroller, and an Android companion app**.

Instead of being just a phone case, Picocase turns the back of the phone into a tiny animated character that can react to what is happening on the phone — messages, calls, charging, music, battery status, and more.

> **A physical gift with a little digital personality.**

---

## ✨ What is Picocase?

Picocase is designed around a simple idea:

**Your phone case should feel alive.**

A small **128×64 monochrome OLED** acts as the character's face. An **ESP32** stores and plays animation files locally while an Android app acts as the bridge between the phone and the case.

The case itself is handmade using materials such as:

- 🧶 Wool / yarn
- 🧵 Plastic canvas
- 🪡 Cross-stitch artwork
- 🧩 Layered / pop-out decorations
- 🖥️ 128×64 SSD1306 OLED
- ⚡ ESP32
- 📱 Android phone

The result is a physical + digital character that can react to the owner's phone.

---

## 🎀 Project Concept

```text
                 📱 ANDROID PHONE
                       │
                       │ USB / OTG
                       ▼
                ┌───────────────┐
                │   Picocase    │
                │ Android App   │
                └───────┬───────┘
                        │
                  Serial Commands
                        │
                        ▼
                ┌───────────────┐
                │     ESP32     │
                │               │
                │ Core 0        │
                │ Serial / App  │
                │ Communication │
                │               │
                │ Core 1        │
                │ Animation     │
                │ Rendering     │
                └───────┬───────┘
                        │
                        ▼
                 ┌─────────────┐
                 │ SSD1306     │
                 │ 128 × 64    │
                 │ OLED        │
                 └─────────────┘
                        │
                        ▼
                  💗 Character
```

---

# 🌸 Features

## 🖥️ Animated OLED Character

Picocase uses a 128×64 monochrome SSD1306 OLED.

Animations are stored as `.bin` files and played directly from the ESP32 filesystem.

### Current animation categories

| Type | Purpose |
|---|---|
| 😊 HAPPY | Default idle personality |
| 😴 SLEEPY | Sleep / inactive state |
| 🤩 EXCITED | High-energy personality |
| 💬 ALERT_MSG | Incoming message |
| 📞 ALERT_CALL | Incoming call |
| 🔌 ALERT_CHARGE | Charger connected |
| 🔋 ALERT_BATTERY | Low battery |
| ⭐ ALERT_SPECIAL | Special contact / event |
| 📵 ALERT_MISSED | Missed call |

Animations can contain:

- Eye movement
- Blinking
- Facial expressions
- Smiles
- Surprise reactions
- Winks
- Small shakes
- Symbols
- Personality animations
- Custom pixel-art effects

---

# 🧠 Dual-Core ESP32 Architecture

Picocase is designed to use both ESP32 cores.

### Core 0 — Communication

Handles:

- Serial communication
- Commands
- App synchronization
- File management
- Animation upload
- Delete / rename
- Storage management

### Core 1 — Rendering

Handles:

- Reading `.bin` animation files
- Loading frames
- OLED rendering
- Animation timing
- Alert completion

This means the OLED animation does **not block serial communication**.

For example:

```text
Animation playing
       │
       ├── OLED → rendering frames
       │
       └── Serial → still accepts commands
```

There is intentionally **no `BUSY` state during normal animation playback**.

---

# 📐 Hardware

## Required

### ESP32

Recommended:

- ESP32 DevKit
- ESP32-WROOM based development board

Other supported/planned boards:

- Raspberry Pi Pico
- ESP32-S2
- ESP32-S3
- Custom boards

> Some boards may require changes to the USB/serial implementation and GPIO configuration.

---

## OLED

**SSD1306 128×64 I2C**

Default wiring:

| OLED | ESP32 |
|---|---|
| VCC | 3.3V |
| GND | GND |
| SDA | GPIO 21 |
| SCL | GPIO 22 |

Configuration:

```text
I2C Bus:      0
Frequency:    400 kHz
Resolution:   128 × 64
Format:       MONO_HLSB
Frame size:   1024 bytes
```

---

# 🧩 Frame Format

Each frame is a monochrome bitmap:

```text
128 × 64 pixels
     ↓
128 × 64 / 8
     ↓
1024 bytes
```

Therefore:

```text
1 frame = 1024 bytes
```

Animation files contain frames sequentially:

```text
[FRAME 0]
1024 bytes

[FRAME 1]
1024 bytes

[FRAME 2]
1024 bytes

[FRAME 3]
1024 bytes

...
```

Example:

```text
emo_happy.bin
    ↓
1024 × number_of_frames
```

A 30-frame animation:

```text
30 × 1024 = 30,720 bytes
```

The ESP32 reads frames from flash instead of loading the complete animation into RAM.

---

# 📁 Project Structure

Recommended repository structure:

```text
pico-case/
│
├── firmware/
│   └── main.py
│
├── anims/
│   ├── emo_happy.bin
│   ├── emo_sleepy.bin
│   ├── emo_excited.bin
│   ├── alert_msg.bin
│   ├── alert_call.bin
│   ├── alert_charge.bin
│   ├── alert_battery.bin
│   ├── alert_special.bin
│   └── alert_missed.bin
│
├── android/
│   └── Picocase/
│
├── tools/
│   └── animation utilities
│
├── artwork/
│   └── character / case designs
│
└── README.md
```

---

# ⚙️ ESP32 Firmware Setup

## 1. Install MicroPython

Flash a compatible MicroPython firmware to the ESP32.

The firmware must support:

- `machine`
- `framebuf`
- `_thread`
- filesystem access
- serial input/output

---

## 2. Install the OLED driver

The firmware expects:

```python
import ssd1306
```

Make sure `ssd1306.py` exists on the ESP32 filesystem.

---

## 3. Upload `main.py`

Copy:

```text
main.py
```

to the ESP32 root filesystem.

The device should contain:

```text
/
├── main.py
├── ssd1306.py
└── anims/
```

---

## 4. Upload animations

Create:

```text
anims/
```

Then upload your `.bin` files:

```text
anims/emo_happy.bin
anims/emo_sleepy.bin
anims/emo_excited.bin
...
```

---

# 🚀 First Boot

After reboot, the serial terminal should show something similar to:

```text
I2C: [60]
--------------------------------
PICOCASE ESP32
Serial: 115200
OLED: 128 x 64
Frame: 1024 bytes
Animation folder: anims
--------------------------------
Animation Core: STARTED
Serial Core: STARTED
```

The OLED displays:

```text
PICOCASE

READY
```

The device is now waiting for commands.

---

# 📡 Serial Communication

Default configuration:

```text
Baud Rate: 115200
Data:      8-bit
Parity:    None
Stop bits: 1
DTR:       OFF
RTS:       OFF
```

### Basic commands

| Command | Response / Action |
|---|---|
| `PING` | `READY` |
| `START` | Start current emotion |
| `STOP` | Stop animation |
| `PLAY <path>` | Play specified animation |

---

# 😊 Emotion Commands

```text
EMO_HAPPY
EMO_SLEEPY
EMO_EXCITED
```

Example:

```text
EMO_HAPPY
```

The ESP32 looks for:

```text
anims/emo_happy.bin
```

If found, it immediately starts playing the animation.

Response:

```text
READY
```

---

# 🚨 Alert Commands

### Incoming message

```text
ALERT_MSG
```

→

```text
anims/alert_msg.bin
```

---

### Incoming call

```text
ALERT_CALL
```

→

```text
anims/alert_call.bin
```

---

### Charger connected

```text
ALERT_CHARGE
```

→

```text
anims/alert_charge.bin
```

---

### Low battery

```text
ALERT_BATTERY
```

→

```text
anims/alert_battery.bin
```

---

### Special contact

```text
ALERT_SPECIAL
```

→

```text
anims/alert_special.bin
```

---

### Missed call

```text
ALERT_MISSED
```

→

```text
anims/alert_missed.bin
```

---

# 🔄 Alert Behaviour

Emotion animations normally loop:

```text
HAPPY
 ↓
HAPPY
 ↓
HAPPY
 ↓
...
```

An alert is different:

```text
HAPPY
  │
  │ incoming call
  ▼
ALERT_CALL
  │
  │ animation finished
  ▼
END
  │
  ▼
HAPPY
```

The alert does not need to be manually stopped.

---

# 📂 File Management Commands

## List animations

```text
LIST_FILES
```

Example response:

```text
emo_happy.bin 30720
emo_sleepy.bin 20480
alert_call.bin 15360
alert_msg.bin 18432
END
```

---

## Delete

```text
DELETE emo_happy.bin
```

or:

```text
DELETE anims/emo_happy.bin
```

Response:

```text
READY
```

---

## Rename

```text
RENAME old.bin new.bin
```

Example:

```text
RENAME emo_happy.bin emo_idle.bin
```

---

## Wipe animation storage

```text
WIPE_STORAGE
```

This removes `.bin` animation files from:

```text
anims/
```

---

# 📤 Animation Upload Protocol

Upload begins with:

```text
FILE_UPLOAD_BEGIN <path> <size>
```

Example:

```text
FILE_UPLOAD_BEGIN anims/emo_happy.bin 30720
```

ESP32 responds:

```text
READY
```

Then send hexadecimal data:

```text
DATA:<hex bytes>
```

Example:

```text
DATA:00FF00FF...
```

The ESP32 responds:

```text
READY <received_bytes>
```

Example:

```text
READY 512
READY 1024
READY 1536
```

Finish with:

```text
FILE_UPLOAD_END
```

Response:

```text
READY
```

The file is first written to a temporary file and then moved into place.

---

# 📱 Picocase Android App

The Android app is the **bridge between the phone and the physical Picocase**.

Its job is to:

1. Connect to the ESP32
2. Detect phone events
3. Convert events into Picocase commands
4. Send commands over USB/OTG
5. Manage animation files
6. Configure the device
7. Provide debugging tools

---

# 🏠 App Dashboard

The main dashboard can provide:

```text
┌──────────────────────────────┐
│          PIC0CASE            │
│        ● Connected           │
├──────────────────────────────┤
│                              │
│       Current Emotion        │
│          😊 HAPPY            │
│                              │
├──────────────────────────────┤
│ Notifications       ON       │
│ Mini Messages       OFF      │
│ Wake on Shake        ON      │
│ Sleep Mode           ON      │
│ Random Animation     ON      │
│ Always On            ON      │
├──────────────────────────────┤
│     ▶ Test Animation         │
│     📂 Animation Library     │
│     ⚡ Events                │
│     🖥 Terminal              │
│     ⚙ Settings              │
└──────────────────────────────┘
```

---

# 📱 App Pages

## 🔌 Connect

Shows:

- USB device
- Connection status
- Connect / disconnect
- Serial configuration
- Device information

---

## 🏠 Dashboard

Controls:

- Current emotion
- Notifications
- Mini messages
- Wake on shake
- Sleep mode
- Random animations
- Always-on mode

---

## 🎞 Animation Library

Manage animations directly from the phone.

Possible operations:

```text
Upload
Download
Delete
Rename
Play
Preview
Refresh
```

The app communicates with the ESP32 using the file protocol.

---

# ⚡ Events

The app can map Android events to Picocase reactions.

| Phone Event | Picocase Command |
|---|---|
| Incoming call | `ALERT_CALL` |
| Special contact | `ALERT_SPECIAL` |
| Incoming SMS | `ALERT_MSG` |
| Charger connected | `ALERT_CHARGE` |
| Battery <15% | `ALERT_BATTERY` |
| Missed call | `ALERT_MISSED` |
| Music playing | `EMO_HAPPY` |
| Music paused | `EMO_SLEEPY` |

This allows the character to react automatically without manually opening the app.

---

# 🖥 Terminal

The app terminal can provide direct access to the Picocase command protocol.

Example:

```text
> PING

< READY

> EMO_HAPPY

< READY

> ALERT_CALL

< READY

< END
```

This is useful for:

- Debugging
- Testing animations
- Checking communication
- Testing commands
- Diagnosing connection problems

---

# ⚙️ Default App Settings

| Setting | Default |
|---|---|
| Baud Rate | 115200 |
| DTR | OFF |
| RTS | OFF |
| Board Profile | ESP32 DevKit |
| OLED SDA | GPIO 21 |
| OLED SCL | GPIO 22 |
| I2C Bus | 0 |
| I2C Frequency | 400 kHz |
| Display | 128×64 |
| Pixel Format | MONO_HLSB |
| Frame Size | 1024 bytes |
| Frame Delay | 120 ms |
| Animation Folder | `anims/` |
| Auto Connect OTG | ON |

---

# 🔌 USB / OTG

Picocase is designed to communicate with the Android phone over USB OTG.

Typical connection:

```text
Android Phone
      │
      │ USB-C OTG
      │
      ▼
ESP32 USB interface
      │
      ▼
MicroPython
      │
      ▼
Picocase firmware
```

The exact USB implementation depends on the ESP32 board.

For ESP32 development boards using a USB-to-UART bridge, the Android app needs a compatible USB serial implementation.

For boards with native USB, the implementation may use USB CDC.

---

# 🧵 The Physical Case

The electronics are only one part of Picocase.

The physical case is intended to be handmade and personalized.

A typical design can include:

```text
┌───────────────────────────────┐
│        ✨ Decorative          │
│                               │
│     ┌─────────────────┐       │
│     │     OLED        │       │
│     │   ◉       ◉     │       │
│     │       ◡         │       │
│     └─────────────────┘       │
│                               │
│       🧶 Cross Stitch         │
│       🧵 Wool Artwork         │
│                               │
│    ESP32 hidden underneath    │
│                               │
└───────────────────────────────┘
```

The OLED becomes the character's face while the surrounding handmade artwork creates the physical personality.

---

# 🎨 Character Design

The original Picocase character concept is a human-girl-like digital companion.

Design elements include:

- Oval face
- Large round glasses
- Long hair
- Cute facial expressions
- Simple monochrome pixel art
- Small personality animations

The character should feel like a tiny companion rather than a robotic interface.

---

# 🛠 Animation Creation

Animations should be created at:

```text
128 × 64 pixels
```

Monochrome:

```text
1 = pixel ON
0 = pixel OFF
```

Recommended animation speed:

```text
120 ms/frame
```

Approximately:

```text
8.3 FPS
```

For smoother animations, frame timing can be changed in firmware.

---

# 🧪 Testing

## Test communication

Send:

```text
PING
```

Expected:

```text
READY
```

---

## Test HAPPY

```text
EMO_HAPPY
```

Expected:

```text
READY
```

OLED should begin playing:

```text
anims/emo_happy.bin
```

---

## Test alert

```text
ALERT_CALL
```

Expected:

```text
READY
```

After the animation finishes:

```text
END
```

The previous emotion resumes automatically.

---

## Test file list

```text
LIST_FILES
```

Expected:

```text
<filename> <bytes>
<filename> <bytes>
...
END
```

---

# 🧯 Troubleshooting

## OLED shows nothing

Check:

```text
SDA → GPIO21
SCL → GPIO22
VCC → 3.3V
GND → GND
```

Then check the I2C scan.

Expected output may look like:

```text
I2C: [60]
```

`60` decimal is:

```text
0x3C
```

which is a common SSD1306 address.

---

## `FILE_NOT_FOUND`

Example:

```text
ERROR FILE_NOT_FOUND
```

Check:

```text
anims/
```

and make sure the requested file exists.

For:

```text
EMO_HAPPY
```

the required file is:

```text
anims/emo_happy.bin
```

---

## `INVALID_SIZE`

The animation file must contain complete frames.

Correct:

```text
1024
2048
3072
4096
...
```

Incorrect:

```text
1000
1500
2500
```

---

## Animation doesn't play

Check:

1. File exists
2. File size is divisible by 1024
3. OLED is detected
4. `ssd1306.py` is installed
5. ESP32 has enough free storage
6. Serial command is correct

---

## Serial connection doesn't work

Check:

```text
115200 baud
8N1
DTR OFF
RTS OFF
```

Also make sure another serial terminal such as Thonny is not already holding the USB serial port.

---

# 🔐 Safety Notes

Picocase is designed around USB/OTG-powered electronics.

If powering the project directly from a phone:

- Do not connect 5V to an ESP32 3.3V pin.
- Use the correct 5V/VIN input for the development board.
- Verify the board's regulator before wiring power.
- Use proper USB-C CC configuration for custom USB-C hardware.
- Avoid exposed conductive connections behind the phone.
- Insulate solder joints.
- Secure the electronics so they cannot scratch or short against the phone.

---

# 🗺️ Roadmap

## ✅ Current

- [x] ESP32 animation playback
- [x] SSD1306 128×64
- [x] `.bin` animation format
- [x] Flash-based frame streaming
- [x] Dual-core architecture
- [x] Serial command protocol
- [x] Emotion commands
- [x] Alert commands
- [x] File management
- [x] Animation upload protocol
- [x] One-shot alert → emotion return

## 🚧 In Progress

- [ ] Android Picocase app
- [ ] USB OTG auto-connect
- [ ] Background event monitoring
- [ ] Animation library UI
- [ ] Event mapping UI
- [ ] Terminal UI
- [ ] Animation preview
- [ ] Touch / swipe controls
- [ ] Random personality system

## 💡 Future Ideas

- [ ] More emotional states
- [ ] Custom animation editor
- [ ] Phone notification preview
- [ ] Music-reactive animation
- [ ] Shake detection
- [ ] Charging animation
- [ ] Sleep/wake system
- [ ] OTA firmware update
- [ ] Wi-Fi configuration
- [ ] Multiple character themes
- [ ] Custom user-created animation packs

---

# 🧰 Development Tools

Picocase can be developed using:

- **MicroPython**
- **Thonny**
- **Android Studio**
- **Kotlin**
- **XML / Material Design**
- **Python**
- **ESP32**
- **SSD1306**
- **Git / GitHub**

---

# 📜 Command Reference

```text
PING

START
STOP
PLAY <path>

EMO_HAPPY
EMO_SLEEPY
EMO_EXCITED

ALERT_MSG
ALERT_CALL
ALERT_CHARGE
ALERT_BATTERY
ALERT_SPECIAL
ALERT_MISSED

LIST_FILES

FILE_UPLOAD_BEGIN <path> <size>
DATA:<hex_bytes>
FILE_UPLOAD_END

DELETE <path>
RENAME <old> <new>
WIPE_STORAGE
```

---

# 💗 Why Picocase?

Most phone cases are designed to protect a phone.

Picocase is designed to **mean something**.

It combines:

```text
Craft
  +
Electronics
  +
Software
  +
Animation
  +
Personalization
  =
Picocase 💗
```

The goal isn't to build another generic IoT gadget.

It's to build a small physical object that feels personal — something that can sit on the back of a phone and react, move, and express itself.

---

# 👨‍💻 Project

**Project:** Picocase  
**Repository:** `winpritam/pico-case`

Built with:

```text
ESP32
MicroPython
SSD1306 OLED
Android
USB OTG
Pixel Art
Handmade Craft
```

---

## ⭐ Support the Project

If you like the idea of Picocase:

- ⭐ Star the repository
- 🍴 Fork it
- 🛠 Build your own version
- 🎨 Create your own animations
- 💡 Share improvements
- 🐛 Report bugs
- ❤️ Make something personal

---

## 📄 License

Choose and add a license appropriate for your project.

For example:

```text
MIT License
```

See the repository `LICENSE` file for the complete license text.

---

<p align="center">

### 💗 Picocase

**A tiny companion. A handmade case. A little bit of personality.**

`Made with code + craft + curiosity.`

</p>
