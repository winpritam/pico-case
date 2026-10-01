# ============================================================
# PICOCASE - ESP32 Animation Engine
# MicroPython
#
# Main thread:
#   USB serial communication
#   Commands
#   File management
#   Upload
#
# Animation thread:
#   Animation file reading
#   OLED rendering
#
# OLED:
#   SSD1306 128x64
#   SDA = GPIO21
#   SCL = GPIO22
#
# Frame:
#   128 x 64 / 8 = 1024 bytes
#
# Animation files:
#   Every .bin file in anims/ is an animation.
#   EMO_<NAME>    -> anims/emo_<name>.bin    (looping emotion)
#   ALERT_<NAME>  -> anims/alert_<name>.bin  (plays once, then
#                                             returns to emotion)
#   Files are looked up by scanning anims/ (case-insensitive),
#   so new emo_*.bin / alert_*.bin files work without code changes.
# ============================================================

import sys
import time
import os
import _thread
import framebuf

try:
    import uselect
except ImportError:
    import select as uselect

from machine import Pin, I2C
import ssd1306


# ============================================================
# CONFIGURATION
# ============================================================

WIDTH = 128
HEIGHT = 64

FRAME_SIZE = (WIDTH * HEIGHT) // 8       # 1024 bytes
FRAME_DELAY_MS = 120                     # ~8.3 FPS

ANIM_DIR = "anims"

OLED_SDA = 21
OLED_SCL = 22
I2C_FREQ = 400000

SERIAL_BAUD = 115200

DEFAULT_ANIMATION = "anims/emo_happy.bin"

# True = echo every received command to the serial console.
# Keep False when the Android app is connected, so the app only
# sees real replies (READY / END / ERROR ...).
DEBUG = False


# ============================================================
# OLED
# ============================================================

i2c = I2C(
    0,
    scl=Pin(OLED_SCL),
    sda=Pin(OLED_SDA),
    freq=I2C_FREQ
)

print("I2C:", i2c.scan())

oled = ssd1306.SSD1306_I2C(
    WIDTH,
    HEIGHT,
    i2c
)


# ============================================================
# ANIMS DIRECTORY
# ============================================================

try:
    os.mkdir(ANIM_DIR)
except Exception:
    pass

# Remove leftovers of interrupted uploads
try:
    for _name in os.listdir(ANIM_DIR):
        if _name.lower().endswith(".tmp"):
            try:
                os.remove(ANIM_DIR + "/" + _name)
            except Exception:
                pass
except Exception:
    pass


# ============================================================
# SHARED STATE
#
# Every function that ASSIGNS one of these must declare it
# with "global", otherwise Python treats it as a local
# variable (that was the NameError in the old code).
# ============================================================

state_lock = _thread.allocate_lock()
io_lock = _thread.allocate_lock()

device_running = False

current_animation = DEFAULT_ANIMATION

animation_loop = True

# Incremented on every request, used to interrupt the
# animation that is currently playing
animation_generation = 0

# Emotion that is restored when an alert has finished
current_emotion = DEFAULT_ANIMATION

# True while the animation thread has released file + OLED
engine_idle = True

# Set on Ctrl+C so the animation thread exits
engine_quit = False


# ============================================================
# SERIAL
# ============================================================

serial_poll = uselect.poll()

try:
    serial_poll.register(sys.stdin, uselect.POLLIN)
except Exception as e:
    print("Serial poll error:", e)


def serial_send(text):
    """
    Send one ASCII line to Android / PC.
    """
    try:
        with io_lock:
            sys.stdout.write(str(text) + "\r\n")
    except Exception:
        pass


# ============================================================
# PATH HELPERS
# ============================================================

def normalize_path(path):

    path = path.strip()

    if path.startswith("/"):
        path = path[1:]

    if path.startswith("./"):
        path = path[2:]

    return path


def valid_animation_path(path):

    path = normalize_path(path)

    if not path.startswith(ANIM_DIR + "/"):
        return False

    if ".." in path:
        return False

    if not path.lower().endswith(".bin"):
        return False

    return True


def find_animation(path):
    """
    Look for the file in anims/ by scanning the directory
    (case-insensitive). Returns the real path or None.
    """
    path = normalize_path(path)
    prefix = ANIM_DIR + "/"

    if not path.startswith(prefix):
        return None

    wanted = path[len(prefix):].lower()

    try:
        for filename in os.listdir(ANIM_DIR):
            if filename.lower() == wanted:
                return prefix + filename
    except Exception:
        pass

    return None


def safe_close(handle):

    if handle is not None:
        try:
            handle.close()
        except Exception:
            pass

    return None


# ============================================================
# ANIMATION STATE
# ============================================================

def request_animation(path, loop=True, remember_emotion=False, quiet=False):

    global current_animation
    global animation_loop
    global animation_generation
    global current_emotion
    global device_running
    global engine_idle

    def fail(message):
        if not quiet:
            serial_send("ERROR " + message)
        return False

    path = normalize_path(path)

    if not valid_animation_path(path):
        return fail("INVALID_PATH")

    # Search anims/ for the file
    real_path = find_animation(path)

    if real_path is None:
        return fail("FILE_NOT_FOUND")

    try:
        size = os.stat(real_path)[6]
    except Exception:
        return fail("FILE_NOT_FOUND")

    if size == 0:
        return fail("EMPTY_FILE")

    if size % FRAME_SIZE != 0:
        return fail("INVALID_FRAME_SIZE")

    with state_lock:

        current_animation = real_path

        animation_loop = loop

        animation_generation += 1

        device_running = True

        engine_idle = False

        if remember_emotion:
            current_emotion = real_path

    return True


def stop_device():

    global device_running
    global animation_generation

    with state_lock:

        device_running = False

        animation_generation += 1

    serial_send("END")


def pause_playback():
    """
    Stop playback and wait until the animation thread has closed
    its file. Returns True if something was playing.
    """
    global device_running
    global animation_generation

    with state_lock:

        was_running = device_running

        device_running = False

        animation_generation += 1

    deadline = time.ticks_add(time.ticks_ms(), 1000)

    while time.ticks_diff(deadline, time.ticks_ms()) > 0:

        with state_lock:
            idle = engine_idle

        if idle:
            break

        time.sleep_ms(5)

    return was_running


def resume_playback():
    """
    Restart whatever was playing before pause_playback().
    """
    with state_lock:

        path = current_animation
        loop = animation_loop

    request_animation(path, loop, False, True)


def engine_shutdown():

    global engine_quit

    with state_lock:
        engine_quit = True


# ============================================================
# OLED SCREEN HELPERS
# ============================================================

def show_ready():

    oled.fill(0)

    oled.text("PICOCASE", 32, 20)
    oled.text("READY", 43, 40)

    oled.show()


# ============================================================
# ANIMATION THREAD
# ============================================================

def animation_core():

    # These are ASSIGNED below, so they MUST be declared global.
    global device_running
    global animation_generation
    global current_animation
    global animation_loop
    global engine_idle

    file_handle = None

    frame_buffer = bytearray(FRAME_SIZE)

    framebuffer = framebuf.FrameBuffer(
        frame_buffer,
        WIDTH,
        HEIGHT,
        framebuf.MONO_HLSB
    )

    local_generation = -1
    local_path = None
    local_loop = True
    frames_this_pass = 0
    screen_active = False

    while True:

        try:

            # ------------------------------------------------
            # Read shared state
            # ------------------------------------------------

            with state_lock:

                running = device_running
                requested_path = current_animation
                requested_loop = animation_loop
                generation = animation_generation
                quitting = engine_quit

            if quitting:

                file_handle = safe_close(file_handle)
                return

            # ------------------------------------------------
            # Device stopped
            # ------------------------------------------------

            if not running:

                file_handle = safe_close(file_handle)

                if screen_active:

                    oled.fill(0)
                    oled.show()

                    screen_active = False

                local_generation = -1

                with state_lock:

                    if not device_running:
                        engine_idle = True

                time.sleep_ms(20)
                continue

            # ------------------------------------------------
            # New animation requested
            # ------------------------------------------------

            if generation != local_generation:

                file_handle = safe_close(file_handle)

                local_generation = generation
                local_path = requested_path
                local_loop = requested_loop
                frames_this_pass = 0

                try:

                    file_handle = open(
                        local_path,
                        "rb"
                    )

                except Exception:

                    serial_send("ERROR FILE_OPEN")

                    with state_lock:

                        if animation_generation == generation:
                            device_running = False

                    continue

            # ------------------------------------------------
            # Read ONE frame
            # ------------------------------------------------

            try:
                bytes_read = file_handle.readinto(frame_buffer)
            except Exception:
                bytes_read = 0

            # ------------------------------------------------
            # End of animation
            # ------------------------------------------------

            if bytes_read != FRAME_SIZE:

                # Nothing playable in this file (avoid busy loop)
                if frames_this_pass == 0:

                    file_handle = safe_close(file_handle)

                    serial_send("ERROR EMPTY_FILE")

                    with state_lock:

                        if animation_generation == generation:
                            device_running = False

                    continue

                if local_loop:

                    # Emotion animation -> start again
                    try:
                        file_handle.seek(0)
                        frames_this_pass = 0
                    except Exception:
                        # force a clean re-open
                        local_generation = -1

                    continue

                # Alert animation finished
                file_handle = safe_close(file_handle)

                serial_send("END")

                # Return to current emotion
                with state_lock:

                    if (
                        device_running
                        and animation_generation == generation
                    ):

                        animation_generation += 1

                        current_animation = current_emotion

                        animation_loop = True

                local_generation = -1

                continue

            # ------------------------------------------------
            # RENDER FRAME
            # (blit overwrites all 8192 pixels, no fill needed)
            # ------------------------------------------------

            oled.blit(
                framebuffer,
                0,
                0
            )

            oled.show()

            screen_active = True
            frames_this_pass += 1

            # ------------------------------------------------
            # Wait for frame timing
            # ------------------------------------------------

            deadline = time.ticks_add(
                time.ticks_ms(),
                FRAME_DELAY_MS
            )

            while time.ticks_diff(deadline, time.ticks_ms()) > 0:

                time.sleep_ms(10)

                # Another animation requested / stopped?
                with state_lock:

                    interrupted = (
                        animation_generation != local_generation
                        or not device_running
                    )

                if interrupted:
                    break

        except Exception as e:

            print("ENGINE ERROR:", e)

            file_handle = safe_close(file_handle)

            local_generation = -1
            screen_active = False

            serial_send("ERROR ENGINE")

            with state_lock:
                device_running = False

            time.sleep_ms(100)


# ============================================================
# FILE LIST
# ============================================================

def list_files():

    try:

        files = os.listdir(ANIM_DIR)

        for filename in files:

            if not filename.lower().endswith(".bin"):
                continue

            path = ANIM_DIR + "/" + filename

            try:

                size = os.stat(path)[6]

                serial_send(
                    "{} {}".format(
                        filename,
                        size
                    )
                )

            except Exception:
                pass

        serial_send("END")

    except Exception:

        serial_send("ERROR LIST_FILES")


# ============================================================
# DELETE FILE
# ============================================================

def delete_file(path):

    path = normalize_path(path)

    if not valid_animation_path(path):

        serial_send("ERROR INVALID_PATH")
        return

    real_path = find_animation(path)

    if real_path is None:

        serial_send("ERROR FILE_NOT_FOUND")
        return

    with state_lock:

        active = device_running and current_animation == real_path

    if active:

        serial_send("ERROR FILE_IN_USE")
        return

    try:

        os.remove(real_path)

        serial_send("READY")

    except Exception:

        serial_send("ERROR DELETE")


# ============================================================
# RENAME FILE
# ============================================================

def rename_file(old_path, new_path):

    old_path = normalize_path(old_path)
    new_path = normalize_path(new_path)

    if not valid_animation_path(old_path):
        serial_send("ERROR INVALID_PATH")
        return

    if not valid_animation_path(new_path):
        serial_send("ERROR INVALID_PATH")
        return

    real_old = find_animation(old_path)

    if real_old is None:
        serial_send("ERROR FILE_NOT_FOUND")
        return

    try:

        os.rename(
            real_old,
            new_path
        )

        serial_send("READY")

    except Exception:

        serial_send("ERROR RENAME")


# ============================================================
# WIPE STORAGE
# ============================================================

def wipe_storage():

    upload_abort()
    upload_finish_resume(False)

    # Make sure the animation thread has closed its file
    pause_playback()

    try:

        files = os.listdir(ANIM_DIR)

        for filename in files:

            lower = filename.lower()

            if lower.endswith(".bin") or lower.endswith(".tmp"):

                try:

                    os.remove(
                        ANIM_DIR + "/" + filename
                    )

                except Exception:
                    pass

        serial_send("READY")

    except Exception:

        serial_send("ERROR WIPE")


# ============================================================
# FILE UPLOAD STATE
# ============================================================

upload_file = None
upload_path = None
upload_temp_path = None

upload_expected_size = 0
upload_received = 0

# True if playback was paused for the upload and should restart
upload_resume = False


def upload_reset():

    global upload_file
    global upload_path
    global upload_temp_path
    global upload_expected_size
    global upload_received

    upload_file = None
    upload_path = None
    upload_temp_path = None
    upload_expected_size = 0
    upload_received = 0


def upload_abort():
    """
    Close and delete the temporary file of a running upload.
    """
    if upload_file is not None:
        safe_close(upload_file)

    if upload_temp_path:

        try:
            os.remove(upload_temp_path)
        except Exception:
            pass

    upload_reset()


def upload_finish_resume(resume=True):

    global upload_resume

    was = upload_resume

    upload_resume = False

    if was and resume:
        resume_playback()


def upload_begin(path, size):

    global upload_file
    global upload_path
    global upload_temp_path
    global upload_expected_size
    global upload_received
    global upload_resume

    path = normalize_path(path)

    try:
        size = int(size)
    except Exception:
        serial_send("ERROR INVALID_SIZE")
        return

    if not valid_animation_path(path):

        serial_send("ERROR INVALID_PATH")
        return

    if size <= 0:

        serial_send("ERROR INVALID_SIZE")
        return

    if size % FRAME_SIZE != 0:

        serial_send("ERROR INVALID_FRAME_SIZE")
        return

    # Drop any half finished earlier upload
    upload_abort()

    # Pause the animation (keeps the serial line and the flash
    # free while data is coming in)
    if pause_playback():
        upload_resume = True

    try:

        upload_path = path

        upload_temp_path = path + ".tmp"

        upload_expected_size = size

        upload_received = 0

        upload_file = open(
            upload_temp_path,
            "wb"
        )

        serial_send("READY")

    except Exception:

        upload_abort()

        serial_send("ERROR UPLOAD_BEGIN")

        upload_finish_resume()


def upload_data(hex_string):

    global upload_received

    if upload_file is None:

        serial_send("ERROR NO_UPLOAD")
        return

    try:

        raw = bytes.fromhex(
            hex_string
        )

        if upload_received + len(raw) > upload_expected_size:
            raise ValueError("too much data")

        upload_file.write(raw)

        upload_received += len(raw)

        serial_send("READY")

    except Exception:

        upload_abort()

        serial_send("ERROR DATA")

        upload_finish_resume()


def upload_end():

    global upload_file

    if upload_file is None:

        serial_send("ERROR NO_UPLOAD")
        return

    try:

        upload_file.flush()
        upload_file.close()

        upload_file = None

        if upload_received != upload_expected_size:

            upload_abort()

            serial_send("ERROR SIZE_MISMATCH")

            upload_finish_resume()
            return

        # Replace old file (also if it differs only in upper/lower case)
        existing = find_animation(upload_path)

        if existing is not None:
            os.remove(existing)

        os.rename(
            upload_temp_path,
            upload_path
        )

        upload_reset()

        serial_send("READY")

    except Exception:

        upload_abort()

        serial_send("ERROR UPLOAD_END")

    upload_finish_resume()


# ============================================================
# COMMAND PROCESSOR
# ============================================================

def process_command(command):

    command = command.strip()

    if not command:
        return

    # --------------------------------------------------------
    # FILE DATA  (checked first, never echoed: very long line)
    # --------------------------------------------------------

    if command[:5].upper() == "DATA:":

        upload_data(
            command[5:].strip()
        )

        return

    if DEBUG:
        print("CMD:", command)

    parts = command.split(None, 1)

    head = parts[0].upper()

    arg = parts[1].strip() if len(parts) > 1 else ""

    # --------------------------------------------------------
    # PING
    # --------------------------------------------------------

    if head == "PING":

        serial_send("READY")
        return

    # --------------------------------------------------------
    # START  (resume / restart current animation)
    # --------------------------------------------------------

    if head == "START":

        with state_lock:

            path = current_animation
            loop = animation_loop

        if request_animation(path, loop, False):
            serial_send("READY")

        return

    # --------------------------------------------------------
    # STOP
    # --------------------------------------------------------

    if head == "STOP":

        stop_device()
        return

    # --------------------------------------------------------
    # ALERT_EVENT <path>   (used by the app for missed calls)
    # --------------------------------------------------------

    if head == "ALERT_EVENT":

        if not arg:

            serial_send("ERROR ALERT_FORMAT")
            return

        if request_animation(
            arg,
            False,
            False
        ):
            serial_send("READY")

        return

    # --------------------------------------------------------
    # EMOTIONS:  EMO_<NAME> -> anims/emo_<name>.bin  (loops)
    # --------------------------------------------------------

    if head.startswith("EMO_"):

        path = ANIM_DIR + "/" + head.lower() + ".bin"

        if request_animation(
            path,
            True,
            True
        ):
            serial_send("READY")

        return

    # --------------------------------------------------------
    # ALERTS:  ALERT_<NAME> -> anims/alert_<name>.bin  (once)
    # --------------------------------------------------------

    if head.startswith("ALERT_"):

        path = ANIM_DIR + "/" + head.lower() + ".bin"

        if request_animation(
            path,
            False,
            False
        ):
            serial_send("READY")

        return

    # --------------------------------------------------------
    # PLAY custom file
    # --------------------------------------------------------

    if head == "PLAY":

        if not arg:

            serial_send("ERROR PLAY_FORMAT")
            return

        if request_animation(
            arg,
            True,
            False
        ):
            serial_send("READY")

        return

    # --------------------------------------------------------
    # LIST FILES
    # --------------------------------------------------------

    if head == "LIST_FILES":

        list_files()
        return

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    if head == "DELETE":

        delete_file(arg)
        return

    # --------------------------------------------------------
    # RENAME
    # --------------------------------------------------------

    if head == "RENAME":

        names = command.split()

        if len(names) != 3:

            serial_send("ERROR RENAME_FORMAT")
            return

        rename_file(
            names[1],
            names[2]
        )

        return

    # --------------------------------------------------------
    # WIPE
    # --------------------------------------------------------

    if head == "WIPE_STORAGE":

        wipe_storage()
        return

    # --------------------------------------------------------
    # FILE UPLOAD BEGIN
    # --------------------------------------------------------

    if head == "FILE_UPLOAD_BEGIN":

        names = command.split()

        if len(names) != 3:

            serial_send(
                "ERROR UPLOAD_FORMAT"
            )

            return

        upload_begin(
            names[1],
            names[2]
        )

        return

    # --------------------------------------------------------
    # FILE UPLOAD END
    # --------------------------------------------------------

    if head == "FILE_UPLOAD_END":

        upload_end()
        return

    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    serial_send(
        "ERROR UNKNOWN_COMMAND"
    )


# ============================================================
# BOOT
# ============================================================

show_ready()

# A bigger stack for the animation thread (OLED + file I/O)
try:
    _thread.stack_size(8192)
except Exception:
    pass

_thread.start_new_thread(
    animation_core,
    ()
)

serial_send("READY")

print("--------------------------------")
print("PICOCASE ESP32")
print("Serial:", SERIAL_BAUD)
print("OLED:", WIDTH, "x", HEIGHT)
print("Frame:", FRAME_SIZE, "bytes")
print("Animation folder:", ANIM_DIR)
print("--------------------------------")


# ============================================================
# MAIN THREAD - SERIAL LOOP
# ============================================================

try:

    while True:

        try:

            events = serial_poll.poll(
                50
            )

            if events:

                line = sys.stdin.readline()

                if line:

                    process_command(
                        line
                    )

        except Exception as e:

            print(
                "SERIAL ERROR:",
                e
            )

            serial_send("ERROR INTERNAL")

            time.sleep_ms(100)

except KeyboardInterrupt:

    # Ctrl+C from the app / Thonny: stop the animation thread too
    engine_shutdown()
    raise
