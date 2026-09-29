# ============================================================
# Picocase - ESP32 Serial Command Test
# ============================================================
# This is a TEST version.
#
# It does NOT:
#   - Initialize OLED
#   - Read animation files
#   - Play animation
#
# Instead:
#   - Waits for commands through Serial/USB
#   - Prints a reply back to the serial terminal
#   - Prints the action that would happen for EMO_HAPPY
#
# Example:
#
# PC/Phone sends:
# EMO_HAPPY
#
# ESP32 replies:
# [COMMAND] EMO_HAPPY
# [ACTION] Happy animation requested
# [ACTION] Would open: anims/emo_happy.bin
# [ACTION] Would play animation on OLED
# ============================================================

import sys
import time

# ============================================================
# CONFIGURATION
# ============================================================

DEVICE_NAME = "PICOCASE"

# ============================================================
# STARTUP
# ============================================================

print()
print("================================")
print(DEVICE_NAME)
print("Serial Command Test")
print("================================")

print("Device ready")
print("Waiting for commands...")
print()

# ============================================================
# COMMAND HANDLER
# ============================================================

def handle_command(command):

    command = command.strip()

    if not command:
        return

    print("--------------------------------")
    print("Received:", command)

    # --------------------------------------------------------
    # EMO_HAPPY
    # --------------------------------------------------------

    if command == "EMO_HAPPY":

        print("[COMMAND] EMO_HAPPY")
        print("[ACTION] Happy animation requested")
        print("[ACTION] Would open: anims/emo_happy.bin")
        print("[ACTION] Would read animation frames")
        print("[ACTION] Would display frames on OLED")

        # Reply to sender
        print("REPLY: EMO_HAPPY_OK")

    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    elif command == "START":

        print("[COMMAND] START")
        print("[ACTION] Animation system would start")

        print("REPLY: START_OK")

    # --------------------------------------------------------
    # END
    # --------------------------------------------------------

    elif command == "END":

        print("[COMMAND] END")
        print("[ACTION] Animation system would stop")

        print("REPLY: END_OK")

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    elif command == "STATUS":

        print("[COMMAND] STATUS")
        print("[ACTION] Device is ready")

        print("REPLY: READY")

    # --------------------------------------------------------
    # HELP
    # --------------------------------------------------------

    elif command == "HELP":

        print("[COMMAND] HELP")
        print()
        print("Available commands:")
        print("  EMO_HAPPY")
        print("  START")
        print("  END")
        print("  STATUS")
        print("  HELP")

        print()
        print("REPLY: HELP_OK")

    # --------------------------------------------------------
    # UNKNOWN COMMAND
    # --------------------------------------------------------

    else:

        print("[ERROR] Unknown command")
        print("REPLY: UNKNOWN_COMMAND")

    print("--------------------------------")


# ============================================================
# SERIAL LOOP
# ============================================================

while True:

    try:

        # ----------------------------------------------------
        # Wait for input from USB serial terminal
        # ----------------------------------------------------

        line = sys.stdin.readline()

        if line:

            handle_command(line)

        else:

            time.sleep_ms(10)

    except KeyboardInterrupt:

        print()
        print("Serial test stopped")
        break

    except Exception as e:

        print("[ERROR]")
        print(e)
        time.sleep_ms(100)