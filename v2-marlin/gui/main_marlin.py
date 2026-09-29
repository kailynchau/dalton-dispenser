from tkinter import *
import serial
import threading
from time import sleep

# Connect to serial port
ser = serial.Serial('COM3', 115200, timeout=0.1)

# =====================================================
# SERIAL COMMUNICATION
# Non-blocking send to prevent GUI freezing
# =====================================================

serial_lock = threading.Lock()
abort_requested = False
last_position = {"x": None, "y": None, "z": None}

# Manual Z jog feedrate (mm/min). XY jog buttons run at F3000.
JOG_FEED_Z = 1200



# =====================================================
# COORDINATE CONVENTION FIX (software-only, no firmware change)
# The X motor is physically inverted relative to standard convention.
# Commanding "your" X (negative=left) must be flipped before sending
# to Marlin, since G1 X-1 currently moves RIGHT instead of LEFT.
# Wrap any X value going into a G-code move with fx().
# =====================================================
def fx(x):
    return -x

def fy(y):
    return -y

def send_gcode(cmd, force=False):
    """Send a G-code command to Marlin over serial.
       If STOP was pressed, non-forced commands are dropped so the
       coating routine cannot queue any more motion."""
    if abort_requested and not force:
        return
    try:
        with serial_lock:
            ser.write((cmd + "\n").encode())
        print(f">> {cmd}")
    except Exception as e:
        print(f"Serial error: {e}")


def serial_reader():
    """Background thread to read serial responses from Marlin."""
    while True:
        try:
            with serial_lock:
                if ser.in_waiting:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        print(f"<< {line}")
                        # Parse M114 position reports: "X:1.00 Y:2.00 Z:3.00 E:0.00 Count X:40 ..."
                        # Only parse BEFORE "Count" - after it are raw step counts, not mm
                        if line.startswith("X:") and "Y:" in line and "Z:" in line:
                            try:
                                mm_part = line.split("Count")[0]
                                parts = mm_part.split()
                                for p in parts:
                                    if p.startswith("X:"): last_position["x"] = float(p[2:])
                                    elif p.startswith("Y:"): last_position["y"] = float(p[2:])
                                    elif p.startswith("Z:"): last_position["z"] = float(p[2:])
                            except:
                                pass
        except:
            pass
        sleep(0.01)

# Start background serial reader thread
reader_thread = threading.Thread(target=serial_reader, daemon=True)
reader_thread.start()

# =====================================================
# UNIT CONVERSION HELPERS
# =====================================================

def to_mm(value_str, unit, axis="xy"):
    try:
        value = float(value_str)
    except ValueError:
        return 0.0
    if unit == "mm":
        return value
    elif unit == "um":
        return value / 1000.0
    elif unit == "step":
        # Convert steps to mm using calibrated steps/mm
        # X/Y = 40 steps/mm, Z = 200 steps/mm
        steps_per_mm = 200.0 if axis == "z" else 40.0
        return value / steps_per_mm
    return value

# =====================================================
# MOVEMENT FUNCTIONS
# =====================================================

def send_command(outgoing):
    unit_xyz = xyz_unt.get()

    x_val = to_mm(x_res.get(), unit_xyz, "xy")
    y_val = to_mm(y_res.get(), unit_xyz, "xy")
    z_val = to_mm(z_res.get(), unit_xyz, "z")

    send_gcode("G91")

    if outgoing == "a":
        send_gcode(f"G1 X{x_val:.4f} F3000")
    elif outgoing == "b":
        send_gcode(f"G1 X-{x_val:.4f} F3000")
    elif outgoing == "c":
        send_gcode(f"G1 Y{y_val:.4f} F3000")
    elif outgoing == "d":
        send_gcode(f"G1 Y-{y_val:.4f} F3000")
    elif outgoing == "e":
        send_gcode(f"G1 Z{z_val:.4f} F{JOG_FEED_Z}")
    elif outgoing == "f":
        send_gcode(f"G1 Z-{z_val:.4f} F{JOG_FEED_Z}")
    elif outgoing == "i":
        solenoidOn()

    send_gcode("G90")

# =====================================================
# SOLENOID CONTROL
# =====================================================

def solenoidOn():
    send_gcode("M104 S50")

def solenoidOff():
    send_gcode("M104 S0")

def solenoidPulse():
    try:
        ms = int(pulse_duration.get())
    except ValueError:
        ms = 100
    send_gcode(f"M800 P{ms}")

def solenoidMultiPulse():
    try:
        ms = int(pulse_duration.get())
        count = int(pulse_count.get())
    except ValueError:
        return
    def multi():
        for _ in range(count):
            send_gcode(f"M800 P{ms}")  # firmware-timed pulse
            sleep(0.5)                 # gap between pulses (timing not critical)
    threading.Thread(target=multi, daemon=True).start()

# =====================================================
# PRESET DISPENSE ROUTINES
# =====================================================

def dispenseSU8():
    send_gcode("G91")
    # TODO: add SU8 locus moves here
    send_gcode("G90")

# =====================================================
# AUTOMATED ARRAY COATING
# Workflow: home -> align tip over first needle at
# dispensing height -> Zero Axes -> Dry Run -> Start
# All coordinates relative to the zeroed origin.
# =====================================================

# Recorded needle positions (taught by jogging + Record Point)
needle_points = [
    (0.000, 0.000),
    (0.000, 0.400),
    (0.000, 0.800),
    (0.000, 1.200),
    (0.000, 1.600),
    (0.000, 2.000),
    (0.000, 2.400),
    (0.400, 2.400),
    (0.400, 2.000),
    (0.400, 1.600),
    (0.400, 1.200),
    (0.400, 0.800),
    (0.400, 0.400),
    (0.400, 0.000),
    (0.800, 0.000),
    (0.800, 0.400),
    (0.800, 0.800),
    (0.800, 1.200),
    (0.800, 1.600),
    (0.800, 2.000),
    (0.800, 2.400),
    (1.200, 2.400),
    (1.600, 2.400),
    (2.000, 2.400),
    (2.400, 2.400),
    (2.800, 2.400),
    (3.200, 2.400),
    (3.200, 2.000),
    (2.800, 2.000),
    (2.400, 2.000),
    (2.000, 2.000),
    (1.600, 2.000),
    (1.200, 2.000),
    (2.000, 0.800),
    (2.000, 0.400),
    (2.000, 0.000),
    (2.400, 0.000),
    (2.400, 0.400),
    (2.400, 0.800),
    (2.800, 0.800),
    (2.800, 0.400),
    (2.800, 0.000),
]


# Process parameters
COATING_PARAMS = {
    "z_travel": 1.0,     # safe height above needles (mm)
    "z_dispense": 0.0,  # contact height (mm above Z0) - SAFETY GAP so tip
                         #   doesn't crash/bend. Lower toward 0.0 if it's not
                         #   touching; raise if it still bends at some points.
    "pulse_ms": 100,     # solenoid pulse (unused in dip mode)
    "feed_xy": 800,      # XY feedrate mm/min
    "feed_z": 600,       # Z feedrate mm/min
}

# Dip-transfer parameters (acupuncture needle method)
# Reservoir is mechanically fixed - hardcoded relative to needle #1 zero
reservoir_pos = {"x": -37.10, "y": -19.80}
DIP_PARAMS = {
    "dip_z": -65,          # measured dip depth (per user); lowered 40mm from -69.0
    "dip_dwell": 500,         # ms to hold in the reservoir
    "contact_dwell": 500,     # ms to hold in contact with pad
    "pads_per_dip": 1,        # re-dip after this many pads (1 = every pad)
    "z_reservoir_travel": -29.0,  # hover height above SU-8 surface
    "z_fixture_clear": 10.0,  # MUST clear the workpiece fixture on reservoir trips
}

# =====================================================
# DEVELOPER / IPA DIP-RINSE (two-station sequence)
# Taught hover positions over each dish: (x, y, z_hover)
# z_hover = safe height directly above that dish, NOT the dip depth.
# =====================================================
DIP_STATIONS = {
    "developer": (37.8, 105.0, 18.75),  # Z = needle tips AT liquid surface
                                        # derived: chuck-on-floor 15.9 + 1.5 PCB
                                        # + 0.35 needle + 1.0 fill
    "ipa":       (102.0, 104.0, 9.0),
}

RINSE_PARAMS = {
    "safe_z":     36,     # MUST clear BOTH dish rims during transit - teach this high
    "dev_depth":  0.0,    # mm below hover Z. 0.0 = dry run (no plunge). Set after microscope.
    "ipa_depth":  0.0,    # mm below hover Z. 0.0 = dry run (no plunge). Set after microscope.
    "dev_dwell":  500,    # ms held in developer
    "ipa_dwell":  2000,   # ms held in IPA
    "f_travel":   1600,   # XY travel feedrate mm/min
    "f_plunge":   600,    # going into the dish
    "f_withdraw": 2200,    # coming out - sets meniscus drag-out, tune later
    "f_transit":  2200,   # developer -> IPA; this IS part of development time
    "z_down_is_negative": True,   # VERIFY: home, M114, jog down, M114. Flip if Z increases.
}

# =====================================================
# SEM TEST BRACKET - dev_depth values to run, one array each.
# NOTE: -0.050 touched liquid, so true contact is SHALLOWER than 0.0.
# Negative half = contact sweep. Positive half = dip bracket (only meaningful
# once real contact C is known - then dip = value - C).
# Station Z 18.75. 90 mm glass dish: 6.36 mL per mm; 1 mm fill = 6.36 mL.
# =====================================================
TEST_DEPTHS = [-0.300, -0.250, -0.200, -0.150, -0.100, -0.050,
               0.0, 0.025, 0.050, 0.075, 0.100, 0.150]
CALC_CONTACT = -0.300

# =====================================================
# CONTACT TEST - find the dev_depth at which needle tips first touch liquid.
# Run with WATER and a bare PCB. Plunge, immediate withdraw, no dwell.
# Inspect tips after each run; first wet result = contact depth C.
# =====================================================
CONTACT_TEST = {
    "depth":     1.150,   # current test depth (mm below station Z)
    "step":      0.050,   # increment per button press
    "f_plunge":  400,     # mm/min going down
    "f_up":      500,     # mm/min coming back up
    "retract_z": 60.0,    # lift to THIS Z after the dip, for easy PCB removal.
                          # Must be below Z_MAX_POS - check with M114 after G28.
}

def setReservoir():
    """Record current XY as the SU-8 reservoir location."""
    def record():
        send_gcode("M114")
        sleep(0.5)
        if last_position["x"] is not None:
            reservoir_pos["x"] = last_position["x"]
            reservoir_pos["y"] = last_position["y"]
            print(f"=== Reservoir set: X{reservoir_pos['x']:.3f} Y{reservoir_pos['y']:.3f} ===")
            reservoir_label.config(text="Reservoir: SET")
        else:
            print("=== Could not read position ===")
    threading.Thread(target=record, daemon=True).start()

def runDipCoating(dry_run=False):
    if len(needle_points) == 0:
        print("=== No points recorded ===")
        return
    if reservoir_pos["x"] is None:
        print("=== Reservoir not set! Jog to SU-8 and click Set Reservoir ===")
        return
    def sequence():
        global coating_active, abort_requested
        abort_requested = False
        coating_active = True
        p = COATING_PARAMS
        d = DIP_PARAMS
        mode = "DRY RUN" if dry_run else "DIP COATING"
        print(f"=== {mode}: {len(needle_points)} pads, re-dip every {d['pads_per_dip']} ===")
        send_gcode("G90")
        send_gcode(f"G1 Z{p['z_travel']:.3f} F{p['feed_z']}")

        since_dip = d["pads_per_dip"]  # force a dip before the first pad

        for i, (x, y) in enumerate(needle_points):
            if not coating_active:
                print("=== Stopped ===")
                send_gcode(f"G1 Z{p['z_travel']:.3f} F{p['feed_z']}")
                return

            # Re-dip if needed
            if since_dip >= d["pads_per_dip"]:
                # RAISE ABOVE FIXTURE FIRST, then travel - prevents dragging
                send_gcode(f"G1 Z{d['z_fixture_clear']:.3f} F{p['feed_z']}")
                send_gcode(f"G1 X{reservoir_pos['x']:.3f} Y{reservoir_pos['y']:.3f} F{p['feed_xy']}")
                send_gcode(f"G1 Z{d['z_reservoir_travel']:.3f} F{p['feed_z']}")
                if not dry_run:
                    send_gcode(f"G1 Z{d['dip_z']:.3f} F{p['feed_z']}")  # dip down
                    send_gcode(f"G4 P{d['dip_dwell']}")                  # dwell in SU-8
                    send_gcode(f"G1 Z{d['z_reservoir_travel']:.3f} F{p['feed_z']}")  # lift
                else:
                    print("   (dry run: skipping actual dip)")
                # RAISE ABOVE FIXTURE before heading back to the array
                send_gcode(f"G1 Z{d['z_fixture_clear']:.3f} F{p['feed_z']}")
                since_dip = 0
                print(f"=== Dipped ===")

            # Go to pad and contact
            send_gcode(f"G1 X{x:.3f} Y{y:.3f} F{p['feed_xy']}")
            send_gcode(f"G1 Z{p['z_travel']:.3f} F{p['feed_z']}")
            send_gcode(f"G1 Z{p['z_dispense']:.3f} F{p['feed_z']}")  # contact
            send_gcode("M400")
            if not dry_run:
                send_gcode(f"G4 P{d['contact_dwell']}")  # dwell in contact
            send_gcode(f"G1 Z{p['z_travel']:.3f} F{p['feed_z']}")  # lift
            send_gcode("M400")  # wait for machine to catch up - keeps queue
                                # shallow so STOP responds quickly
            since_dip += 1
            print(f"=== Pad {i+1}/{len(needle_points)} ===")
            sleep(0.3)

        print(f"=== {mode} complete ===")
        coating_active = False

    threading.Thread(target=sequence, daemon=True).start()



def recordPoint():
    """Query current position and add it to the needle list."""
    def record():
        send_gcode("M114")
        sleep(0.5)  # wait for response to be parsed
        if last_position["x"] is not None:
            pt = (last_position["x"], last_position["y"])
            needle_points.append(pt)
            print(f"=== Recorded point {len(needle_points)}: X{pt[0]:.3f} Y{pt[1]:.3f} ===")
            points_label.config(text=f"Points recorded: {len(needle_points)}")
        else:
            print("=== Could not read position - try again ===")
    threading.Thread(target=record, daemon=True).start()

def clearPoints():
    needle_points.clear()
    points_label.config(text="Points recorded: 0")
    print("=== Points cleared ===")

def undoLastPoint():
    """Remove the most recently recorded point."""
    if len(needle_points) == 0:
        print("=== No points to undo ===")
        return
    pt = needle_points.pop()
    print(f"=== Removed point {len(needle_points)+1}: X{pt[0]:.3f} Y{pt[1]:.3f} ===")
    points_label.config(text=f"Points recorded: {len(needle_points)}")

def goToFirstPoint():
    """Raise to travel height, then move to the first recorded point."""
    if len(needle_points) == 0:
        print("=== No points recorded ===")
        return
    x, y = needle_points[0]
    p = COATING_PARAMS
    send_gcode("G90")
    send_gcode(f"G1 Z{p['z_travel']:.3f} F{p['feed_z']}")
    send_gcode(f"G1 X{x:.3f} Y{y:.3f} F{p['feed_xy']}")

def exportPoints():
    """Print all recorded points as copy-pasteable Python code."""
    if len(needle_points) == 0:
        print("=== No points to export ===")
        return
    print("=== COPY BELOW INTO CODE TO HARDCODE ===")
    print("needle_points = [")
    for x, y in needle_points:
        print(f"    ({x:.3f}, {y:.3f}),")
    print("]")
    print("=== END ===")


def recordStation(name):
    """Record current X/Y/Z as a named dip station (developer or ipa)."""
    def record():
        send_gcode("M114")
        sleep(0.5)
        if last_position["x"] is not None:
            pt = (last_position["x"], last_position["y"], last_position["z"])
            DIP_STATIONS[name] = pt
            print(f"=== {name} station: X{pt[0]:.3f} Y{pt[1]:.3f} Z{pt[2]:.3f} ===")
            station_label.config(
                text=f"dev: {'set' if None not in DIP_STATIONS['developer'] else 'not set'}   "
                     f"ipa: {'set' if None not in DIP_STATIONS['ipa'] else 'not set'}")
        else:
            print("=== Could not read position - try again ===")
    threading.Thread(target=record, daemon=True).start()


def recordSafeZ():
    """Record current Z as the transit height that clears both dish rims."""
    def record():
        send_gcode("M114")
        sleep(0.5)
        if last_position["z"] is not None:
            RINSE_PARAMS["safe_z"] = last_position["z"]
            print(f"=== safe_z set to Z{last_position['z']:.3f} ===")
            safez_label.config(text=f"safe_z: {last_position['z']:.3f}")
        else:
            print("=== Could not read position - try again ===")
    threading.Thread(target=record, daemon=True).start()


def exportStations():
    """Print taught stations as copy-pasteable Python code."""
    print("=== COPY BELOW INTO CODE TO HARDCODE ===")
    print("DIP_STATIONS = {")
    for k, v in DIP_STATIONS.items():
        print(f"    {k!r}: {v},")
    print("}")
    print(f"# RINSE_PARAMS['safe_z'] = {RINSE_PARAMS['safe_z']}")
    print("=== END ===")


def runDipRinse():
    """Developer dip -> timed transit -> IPA dip.
       With dev_depth/ipa_depth at 0.0 this runs the full motion without plunging."""
    global coating_active
    if coating_active:
        print("=== A routine is already running - ignoring this press ===")
        return

    p = RINSE_PARAMS
    dev = DIP_STATIONS["developer"]
    ipa = DIP_STATIONS["ipa"]

    if None in dev or None in ipa:
        print("=== Stations not taught - record developer and ipa first ===")
        return
    if p["safe_z"] is None:
        print("=== safe_z not set - jog to a height clearing both rims, then Set Safe Z ===")
        return

    sign = -1.0 if p["z_down_is_negative"] else 1.0
    coating_active = True   # claim NOW, not inside the thread, or a fast
                            # second click slips through before the thread starts

    def run():
        global coating_active, abort_requested
        abort_requested = False
        print(f"=== Dip/rinse started (dev_depth={p['dev_depth']}, ipa_depth={p['ipa_depth']}) ===")
        send_gcode("G90")

        # --- developer station ---
        send_gcode(f"G1 Z{p['safe_z']:.3f} F{p['f_travel']}")
        send_gcode(f"G1 X{dev[0]:.3f} Y{dev[1]:.3f} F{p['f_travel']}")
        send_gcode(f"G1 Z{dev[2] + sign * p['dev_depth']:.3f} F{p['f_plunge']}")
        send_gcode(f"G4 P{p['dev_dwell']}")
        send_gcode(f"G1 Z{p['safe_z']:.3f} F{p['f_withdraw']}")

        # --- transit: fixed feedrate, this is part of development time ---
        send_gcode(f"G1 X{ipa[0]:.3f} Y{ipa[1]:.3f} F{p['f_transit']}")

        # --- ipa station ---
        send_gcode(f"G1 Z{ipa[2] + sign * p['ipa_depth']:.3f} F{p['f_plunge']}")
        send_gcode(f"G4 P{p['ipa_dwell']}")
        send_gcode(f"G1 Z{p['safe_z']:.3f} F{p['f_withdraw']}")

        print("=== Dip/rinse done ===")
        coating_active = False

    threading.Thread(target=run, daemon=True).start()


def _updateDepthLabel():
    d = RINSE_PARAMS["dev_depth"]
    dip = (d - CALC_CONTACT) * 1000.0
    try:
        idx = TEST_DEPTHS.index(round(d, 4))
        pos = f"[{idx + 1}/{len(TEST_DEPTHS)}]"
    except ValueError:
        pos = "[custom]"
    depth_label.config(text=f"dev_depth: {d:.3f} mm   dip: {dip:+.0f} um   {pos}")


def _setDepth(value):
    RINSE_PARAMS["dev_depth"] = round(value, 4)
    dip = (value - CALC_CONTACT) * 1000.0
    print(f"=== dev_depth -> {value:.3f}  (nominal dip {dip:+.0f} um) ===")
    _updateDepthLabel()


def nextTestDepth():
    """Step to the next deeper value in the TEST_DEPTHS bracket."""
    d = round(RINSE_PARAMS["dev_depth"], 4)
    deeper = [v for v in TEST_DEPTHS if v > d]
    if deeper:
        _setDepth(min(deeper))
    else:
        print(f"=== already at deepest bracket value ({max(TEST_DEPTHS):.3f}) ===")


def prevTestDepth():
    """Step to the next shallower value in the TEST_DEPTHS bracket."""
    d = round(RINSE_PARAMS["dev_depth"], 4)
    shallower = [v for v in TEST_DEPTHS if v < d]
    if shallower:
        _setDepth(max(shallower))
    else:
        print(f"=== already at shallowest bracket value ({min(TEST_DEPTHS):.3f}) ===")


def devDepthDeeper():
    _setDepth(RINSE_PARAMS["dev_depth"] + 0.020)


def devDepthShallower():
    _setDepth(RINSE_PARAMS["dev_depth"] - 0.020)


def _updateContactLabel():
    d = CONTACT_TEST["depth"]
    contact_label.config(text=f"depth: {d:.3f} mm   (step {CONTACT_TEST['step']:.3f})")


def contactStepDown():
    CONTACT_TEST["depth"] += CONTACT_TEST["step"]
    print(f"=== contact test depth -> {CONTACT_TEST['depth']:.3f} ===")
    _updateContactLabel()


def contactStepUp():
    CONTACT_TEST["depth"] -= CONTACT_TEST["step"]
    print(f"=== contact test depth -> {CONTACT_TEST['depth']:.3f} ===")
    _updateContactLabel()


def runContactTest():
    """Go to developer station, plunge to CONTACT_TEST depth, come straight back up.
       No dwell - just touch and retract so the tips can be inspected.
       Run with WATER and a bare PCB."""
    global coating_active
    if coating_active:
        print("=== A routine is already running - ignoring this press ===")
        return

    c = CONTACT_TEST
    p = RINSE_PARAMS
    dev = DIP_STATIONS["developer"]

    if None in dev:
        print("=== developer station not set ===")
        return
    if p["safe_z"] is None:
        print("=== safe_z not set ===")
        return

    sign = -1.0 if p["z_down_is_negative"] else 1.0
    target_z = dev[2] + sign * c["depth"]
    coating_active = True   # claim NOW, not inside the thread

    def run():
        global coating_active, abort_requested
        abort_requested = False
        print(f"=== CONTACT TEST: depth {c['depth']:.3f} -> Z{target_z:.3f} ===")
        send_gcode("G90")
        send_gcode(f"G1 Z{p['safe_z']:.3f} F{p['f_travel']}")
        send_gcode(f"G1 X{dev[0]:.3f} Y{dev[1]:.3f} F{p['f_travel']}")
        send_gcode(f"G1 Z{target_z:.3f} F{c['f_plunge']}")
        send_gcode(f"G1 Z{c['retract_z']:.3f} F{c['f_up']}")
        print(f"=== done - inspect tips (depth {c['depth']:.3f}) ===")
        coating_active = False

    threading.Thread(target=run, daemon=True).start()


coating_active = False

def runCoating(dry_run=False):
    if len(needle_points) == 0:
        print("=== No points recorded! Jog to each needle and click Record Point first ===")
        return
    def sequence():
        global coating_active, abort_requested
        abort_requested = False
        coating_active = True
        p = COATING_PARAMS
        mode = "DRY RUN" if dry_run else "COATING"
        print(f"=== {mode} started: {len(needle_points)} needles ===")

        send_gcode("G90")  # absolute positioning
        send_gcode(f"G1 Z{p['z_travel']:.3f} F{p['feed_z']}")

        for i, (x, y) in enumerate(needle_points):
            if not coating_active:
                print("=== Stopped by user ===")
                send_gcode(f"G1 Z{p['z_travel']:.3f} F{p['feed_z']}")
                return
            send_gcode(f"G1 X{x:.3f} Y{y:.3f} F{p['feed_xy']}")
            send_gcode(f"G1 Z{p['z_dispense']:.3f} F{p['feed_z']}")
            send_gcode("M400")
            if not dry_run:
                send_gcode(f"M800 P{p['pulse_ms']}")
            else:
                send_gcode("G4 P500")  # dwell 0.5s at Z0 so touchdown is visible
            send_gcode(f"G1 Z{p['z_travel']:.3f} F{p['feed_z']}")
            send_gcode("M400")  # keeps queue shallow so STOP responds quickly
            print(f"=== Needle {i+1}/{len(needle_points)} ===")
            sleep(0.4)

        print(f"=== {mode} complete ===")
        coating_active = False

    threading.Thread(target=sequence, daemon=True).start()


# =====================================================
# SMEAR COATING (drag tool along lines of pads)
# Each "run" is a straight line of pads. The tool lowers
# at the start of a run, drags along it in contact, then
# lifts before moving to the next run - so SU-8 is only
# smeared along pad lines, not across bare substrate.
# =====================================================

# Crosshatch sweeps: 200um offset either side of every pad row/column,
# so the tool passes BETWEEN pads rather than over them. Pads sit on a
# clean 400um grid, so sweeps land exactly halfway between them.
# 10 vertical + 8 horizontal = 18 strokes covering the whole array.
SMEAR_RUNS = [
    # --- vertical sweeps (constant X, drag along Y) ---
    (-0.200, -0.200, -0.200, 2.600),
    ( 0.200, -0.200,  0.200, 2.600),
    ( 0.600, -0.200,  0.600, 2.600),
    ( 1.000, -0.200,  1.000, 2.600),
    ( 1.400, -0.200,  1.400, 2.600),
    ( 1.800, -0.200,  1.800, 2.600),
    ( 2.200, -0.200,  2.200, 2.600),
    ( 2.600, -0.200,  2.600, 2.600),
    ( 3.000, -0.200,  3.000, 2.600),
    ( 3.400, -0.200,  3.400, 2.600),
    # --- horizontal sweeps (constant Y, drag along X) ---
    (-0.200, -0.200,  3.400, -0.200),
    (-0.200,  0.200,  3.400,  0.200),
    (-0.200,  0.600,  3.400,  0.600),
    (-0.200,  1.000,  3.400,  1.000),
    (-0.200,  1.400,  3.400,  1.400),
    (-0.200,  1.800,  3.400,  1.800),
    (-0.200,  2.200,  3.400,  2.200),
    (-0.200,  2.600,  3.400,  2.600),
]

SMEAR_PARAMS = {
    "z_smear": 0.0,      # contact height for dragging (Z0 = your zeroed height)
    "z_lift": 1.0,       # height to lift between runs
    "feed_smear": 65,    # drag speed mm/min (1/3 of previous 200)
    "feed_travel": 800,  # XY travel speed between runs
    "feed_z": 600,       # Z speed for lower/lift (matches jog speed)
    "dwell_ms": 300,     # pause after touchdown before dragging
    "dip_each_run": True,# re-dip in the SU-8 reservoir before every stroke
}

def runSmear(dry_run=False, height_offset=0.0):
    """Drag the tool along each run of pads.
       height_offset: mm ABOVE z_smear to run at. Use e.g. 0.5 to rehearse
       the whole path safely in the air before committing to contact."""
    def sequence():
        global coating_active, abort_requested
        abort_requested = False
        coating_active = True
        s = SMEAR_PARAMS
        z_contact = s["z_smear"] + height_offset
        mode = "DRY RUN" if dry_run else "SMEAR"
        print(f"=== {mode}: {len(SMEAR_RUNS)} runs at Z{z_contact:.3f} ===")
        if height_offset > 0:
            print(f"    (running {height_offset}mm ABOVE contact - rehearsal)")

        send_gcode("G90")
        send_gcode(f"G1 Z{s['z_lift']:.3f} F{s['feed_z']}")

        for i, (x1, y1, x2, y2) in enumerate(SMEAR_RUNS):
            if not coating_active:
                print("=== Stopped by user ===")
                send_gcode(f"G1 Z{s['z_lift']:.3f} F{s['feed_z']}", force=True)
                return

            # re-dip in the SU-8 reservoir before this stroke
            if s["dip_each_run"]:
                d = DIP_PARAMS
                # raise above the fixture BEFORE any XY travel
                send_gcode(f"G1 Z{d['z_fixture_clear']:.3f} F{s['feed_z']}")
                send_gcode(f"G1 X{reservoir_pos['x']:.3f} Y{reservoir_pos['y']:.3f} F{s['feed_travel']}")
                send_gcode(f"G1 Z{d['z_reservoir_travel']:.3f} F{s['feed_z']}")
                if not dry_run:
                    send_gcode(f"G1 Z{d['dip_z']:.3f} F{s['feed_z']}")   # dip in
                    send_gcode(f"G4 P{d['dip_dwell']}")                   # dwell
                    send_gcode(f"G1 Z{d['z_reservoir_travel']:.3f} F{s['feed_z']}")  # lift out
                else:
                    print("   (dry run: skipping actual dip)")
                # raise above the fixture again before heading to the array
                send_gcode(f"G1 Z{d['z_fixture_clear']:.3f} F{s['feed_z']}")
                send_gcode("M400")
                print(f"   dipped")

            # travel to start of run at lift height
            send_gcode(f"G1 X{x1:.3f} Y{y1:.3f} F{s['feed_travel']}")
            send_gcode(f"G1 Z{s['z_lift']:.3f} F{s['feed_z']}")
            # lower into contact
            send_gcode(f"G1 Z{z_contact:.3f} F{s['feed_z']}")
            send_gcode("M400")
            if not dry_run:
                send_gcode(f"G4 P{s['dwell_ms']}")
            # THE DRAG - slow move while in contact
            send_gcode(f"G1 X{x2:.3f} Y{y2:.3f} F{s['feed_smear']}")
            send_gcode("M400")
            # lift before moving on
            send_gcode(f"G1 Z{s['z_lift']:.3f} F{s['feed_z']}")
            send_gcode("M400")
            print(f"=== Run {i+1}/{len(SMEAR_RUNS)}: ({x1},{y1}) -> ({x2},{y2}) ===")
            sleep(0.3)

        print(f"=== {mode} complete ===")
        coating_active = False

    threading.Thread(target=sequence, daemon=True).start()


# =====================================================
# TEACH & REPEAT SEQUENCER
# Record a custom sequence of actions by jogging the tool
# and clicking buttons. Replay runs it identically.
#
# Action types stored in taught_sequence:
#   ("dip",)                    -> go to reservoir, dip, return
#   ("deposit", x, y)           -> move to (x,y), lower, dwell, lift
#   ("drag", x1, y1, x2, y2)    -> move to start, lower, drag to end, lift
#   ("move", x, y)              -> travel to (x,y) at safe height
# =====================================================

taught_sequence = []
_drag_start = {"x": None, "y": None}

TEACH_PARAMS = {
    "z_contact": 0.0,     # contact height (Z0)
    "z_lift": 1.0,        # travel/lift height
    "deposit_dwell": 400, # ms held down when depositing a drop
    "feed_drag": 65,      # drag speed mm/min
    "feed_travel": 800,   # travel speed mm/min
    "feed_z": 600,        # Z speed mm/min
}

def _read_xy(callback):
    """Query M114 and pass current (x,y) to callback."""
    def worker():
        send_gcode("M114")
        sleep(0.5)
        if last_position["x"] is not None:
            callback(last_position["x"], last_position["y"])
        else:
            print("=== Could not read position, try again ===")
    threading.Thread(target=worker, daemon=True).start()

def teachDip():
    taught_sequence.append(("dip",))
    print(f"=== Step {len(taught_sequence)}: DIP ===")
    teach_label.config(text=f"Steps: {len(taught_sequence)}")

def teachDeposit():
    def add(x, y):
        taught_sequence.append(("deposit", x, y))
        print(f"=== Step {len(taught_sequence)}: DEPOSIT at X{x:.3f} Y{y:.3f} ===")
        teach_label.config(text=f"Steps: {len(taught_sequence)}")
    _read_xy(add)

def teachDragStart():
    def mark(x, y):
        _drag_start["x"], _drag_start["y"] = x, y
        print(f"=== Drag START marked at X{x:.3f} Y{y:.3f} - now jog to end and click Drag End ===")
    _read_xy(mark)

def teachDragEnd():
    if _drag_start["x"] is None:
        print("=== Mark a Drag Start first ===")
        return
    def add(x, y):
        taught_sequence.append(("drag", _drag_start["x"], _drag_start["y"], x, y))
        print(f"=== Step {len(taught_sequence)}: DRAG ({_drag_start['x']:.3f},{_drag_start['y']:.3f}) -> ({x:.3f},{y:.3f}) ===")
        teach_label.config(text=f"Steps: {len(taught_sequence)}")
        _drag_start["x"] = None
    _read_xy(add)

def teachMove():
    def add(x, y):
        taught_sequence.append(("move", x, y))
        print(f"=== Step {len(taught_sequence)}: MOVE to X{x:.3f} Y{y:.3f} ===")
        teach_label.config(text=f"Steps: {len(taught_sequence)}")
    _read_xy(add)

def teachUndo():
    if taught_sequence:
        s = taught_sequence.pop()
        print(f"=== Removed step: {s[0]} ===")
        teach_label.config(text=f"Steps: {len(taught_sequence)}")
    else:
        print("=== Nothing to undo ===")

def teachClear():
    taught_sequence.clear()
    teach_label.config(text="Steps: 0")
    print("=== Sequence cleared ===")

def teachExport():
    if not taught_sequence:
        print("=== Nothing to export ===")
        return
    print("=== COPY BELOW TO HARDCODE THE SEQUENCE ===")
    print("taught_sequence = [")
    for s in taught_sequence:
        print(f"    {s},")
    print("]")
    print("=== END ===")

def teachReplay(dry_run=False):
    if not taught_sequence:
        print("=== No sequence taught ===")
        return
    def sequence():
        global coating_active, abort_requested
        abort_requested = False
        coating_active = True
        t = TEACH_PARAMS
        d = DIP_PARAMS
        mode = "DRY RUN" if dry_run else "REPLAY"
        print(f"=== {mode}: {len(taught_sequence)} steps ===")
        send_gcode("G90")
        send_gcode(f"G1 Z{t['z_lift']:.3f} F{t['feed_z']}")

        for i, step in enumerate(taught_sequence):
            if not coating_active:
                print("=== Stopped by user ===")
                send_gcode(f"G1 Z{t['z_lift']:.3f} F{t['feed_z']}", force=True)
                return
            action = step[0]

            if action == "dip":
                send_gcode(f"G1 Z{d['z_fixture_clear']:.3f} F{t['feed_z']}")
                send_gcode(f"G1 X{reservoir_pos['x']:.3f} Y{reservoir_pos['y']:.3f} F{t['feed_travel']}")
                send_gcode(f"G1 Z{d['z_reservoir_travel']:.3f} F{t['feed_z']}")
                if not dry_run:
                    send_gcode(f"G1 Z{d['dip_z']:.3f} F{t['feed_z']}")
                    send_gcode(f"G4 P{d['dip_dwell']}")
                    send_gcode(f"G1 Z{d['z_reservoir_travel']:.3f} F{t['feed_z']}")
                send_gcode(f"G1 Z{d['z_fixture_clear']:.3f} F{t['feed_z']}")
                send_gcode("M400")

            elif action == "deposit":
                _, x, y = step
                send_gcode(f"G1 Z{t['z_lift']:.3f} F{t['feed_z']}")
                send_gcode(f"G1 X{x:.3f} Y{y:.3f} F{t['feed_travel']}")
                send_gcode(f"G1 Z{t['z_contact']:.3f} F{t['feed_z']}")
                send_gcode("M400")
                if not dry_run:
                    send_gcode(f"G4 P{t['deposit_dwell']}")
                send_gcode(f"G1 Z{t['z_lift']:.3f} F{t['feed_z']}")

            elif action == "drag":
                _, x1, y1, x2, y2 = step
                send_gcode(f"G1 Z{t['z_lift']:.3f} F{t['feed_z']}")
                send_gcode(f"G1 X{x1:.3f} Y{y1:.3f} F{t['feed_travel']}")
                send_gcode(f"G1 Z{t['z_contact']:.3f} F{t['feed_z']}")
                send_gcode("M400")
                send_gcode(f"G1 X{x2:.3f} Y{y2:.3f} F{t['feed_drag']}")
                send_gcode("M400")
                send_gcode(f"G1 Z{t['z_lift']:.3f} F{t['feed_z']}")

            elif action == "move":
                _, x, y = step
                send_gcode(f"G1 Z{t['z_lift']:.3f} F{t['feed_z']}")
                send_gcode(f"G1 X{x:.3f} Y{y:.3f} F{t['feed_travel']}")

            print(f"=== Step {i+1}/{len(taught_sequence)}: {action} ===")
            sleep(0.2)

        print(f"=== {mode} complete ===")
        coating_active = False

    threading.Thread(target=sequence, daemon=True).start()


# =====================================================
# DIP-DROP-DRAG COATING (custom 2-drop routine)
# Two dips create two drops on the PCB. Each drag line
# starts by returning to its group's drop to pick up
# material, then drags continuously: drop -> line start
# -> line end, no lift mid-stroke. Lift only between lines.
# =====================================================

DDD_PARAMS = {
    "z_contact": 0.0,     # contact height (Z0)
    "z_lift": 1.0,        # lift height between lines
    "deposit_dwell": 400, # ms held down when placing a drop
    "feed_drag": 65,      # drag speed mm/min
    "feed_travel": 800,   # travel speed mm/min
    "feed_z": 600,        # Z speed mm/min
}

# Two drops and their drag-line groups
DDD_DROP1 = (-0.8, -0.4)
DDD_DROP2 = (-2.4, -0.4)
DDD_GROUP1_X = [0.2, -0.2, -0.6, -1.0, -1.4]   # fed by drop 1
DDD_GROUP2_X = [-1.8, -2.2, -2.6, -3.0, -3.4]  # fed by drop 2
DDD_LINE_Y_START = -0.4
DDD_LINE_Y_END   = -2.8

def runDipDropDrag(dry_run=False):
    def sequence():
        global coating_active, abort_requested
        abort_requested = False
        coating_active = True
        p = DDD_PARAMS
        d = DIP_PARAMS
        mode = "DRY RUN" if dry_run else "DIP-DROP-DRAG"
        print(f"=== {mode} started ===")

        send_gcode("G90")
        send_gcode(f"G1 Z{p['z_lift']:.3f} F{p['feed_z']}")

        def do_dip():
            # raise above fixture, go to reservoir, dip, return above fixture
            send_gcode(f"G1 Z{d['z_fixture_clear']:.3f} F{p['feed_z']}")
            send_gcode(f"G1 X{reservoir_pos['x']:.3f} Y{reservoir_pos['y']:.3f} F{p['feed_travel']}")
            send_gcode(f"G1 Z{d['z_reservoir_travel']:.3f} F{p['feed_z']}")
            if not dry_run:
                send_gcode(f"G1 Z{d['dip_z']:.3f} F{p['feed_z']}")
                send_gcode(f"G4 P{d['dip_dwell']}")
                send_gcode(f"G1 Z{d['z_reservoir_travel']:.3f} F{p['feed_z']}")
            else:
                print("   (dry run: skipping actual dip)")
            send_gcode(f"G1 Z{d['z_fixture_clear']:.3f} F{p['feed_z']}")
            send_gcode("M400")

        def deposit(x, y):
            # stay high (already at fixture-clear from do_dip), travel to the
            # drop XY FIRST, only THEN lower - prevents catching on the fixture
            send_gcode(f"G1 X{fx(x):.3f} Y{fy(y):.3f} F{p['feed_travel']}")
            send_gcode(f"G1 Z{p['z_contact']:.3f} F{p['feed_z']}")
            send_gcode("M400")
            if not dry_run:
                send_gcode(f"G4 P{p['deposit_dwell']}")
            send_gcode(f"G1 Z{p['z_lift']:.3f} F{p['feed_z']}")

        def coat_group(drop, xs, group_name, z_offset=0.0):
            # z_offset raises the contact height for this whole group (e.g. to
            # compensate for a non-level PCB). +0.15 = tip sits 150um higher.
            dx, dy = drop
            z_contact = p['z_contact'] + z_offset
            for i, lx in enumerate(xs):
                if not coating_active:
                    return False
                # go to the drop, lower into contact
                send_gcode(f"G1 Z{p['z_lift']:.3f} F{p['feed_z']}")
                send_gcode(f"G1 X{fx(dx):.3f} Y{fy(dy):.3f} F{p['feed_travel']}")
                send_gcode(f"G1 Z{z_contact:.3f} F{p['feed_z']}")
                send_gcode("M400")
                # ONE continuous contact drag: drop -> line start -> line end.
                # The previous file moved from firmware Y+0.4 to Y+2.8,
                # which physically travelled AWAY from the user. Keep the
                # same starting point and stroke length, but reverse the
                # firmware-Y direction so every vertical stroke travels TOWARD.
                line_start_y = fy(DDD_LINE_Y_START)
                # Extend the vertical stroke by another 0.4 mm at the far end.
                line_length = abs(DDD_LINE_Y_END - DDD_LINE_Y_START) + 0.6
                line_end_y = line_start_y - line_length
                send_gcode(f"G1 X{fx(lx):.3f} Y{line_start_y:.3f} F{p['feed_drag']}")
                send_gcode(f"G1 X{fx(lx):.3f} Y{line_end_y:.3f} F{p['feed_drag']}")
                send_gcode("M400")
                # lift before returning to the drop
                send_gcode(f"G1 Z{p['z_lift']:.3f} F{p['feed_z']}")
                print(f"=== {group_name} line {i+1}/5: X{lx:.3f} ===")
                sleep(0.2)
            return True

        # Drop 1 + group 1
        do_dip()
        if not coating_active: coating_active=False; return
        deposit(*DDD_DROP1)
        if not coat_group(DDD_DROP1, DDD_GROUP1_X, "Group 1"):
            print("=== Stopped by user ==="); 
            send_gcode(f"G1 Z{p['z_lift']:.3f} F{p['feed_z']}", force=True)
            coating_active=False; return

        # Drop 2 + group 2
        do_dip()
        if not coating_active: coating_active=False; return
        deposit(*DDD_DROP2)
        if not coat_group(DDD_DROP2, DDD_GROUP2_X, "Group 2", z_offset=0.1):
            print("=== Stopped by user ===")
            send_gcode(f"G1 Z{p['z_lift']:.3f} F{p['feed_z']}", force=True)
            coating_active=False; return

        print(f"=== {mode} complete ===")
        coating_active = False

    threading.Thread(target=sequence, daemon=True).start()

def stopCoating():
    """Emergency stop: halt Python loop AND flush Marlin's queued moves."""
    global coating_active, abort_requested
    abort_requested = True    # immediately blocks all further motion commands
    coating_active = False
    try:
        with serial_lock:
            # Reset the input buffer so queued outgoing data is dropped
            ser.reset_output_buffer()
            # M410 = quickstop. Sent directly, bypassing the normal queue path.
            ser.write(b"\nM410\n")
            ser.write(b"M104 S0\n")
    except Exception as e:
        print(f"Stop error: {e}")
    print("=== STOP: motion halted, solenoid closed ===")

# =====================================================
# OPTIONS
# =====================================================

def zeroAxes():
    send_gcode("G92 X0 Y0 Z0 E0")

def homeAxes():
    send_gcode("G28")

def disableMotors():
    send_gcode("M18")

def enableMotors():
    send_gcode("M17")

def get_textbox_input():
    val = command_to_send.get()
    send_gcode(val)

def open_camera():
    pass

def close_camera():
    pass

# =====================================================
# GUI
# =====================================================

mainwin = Tk()
mainwin.title("Dispenser Controls")
mainwin.geometry("1200x950")

xyz_unt = StringVar()

frame_l = Frame(mainwin)
frame_r = Frame(mainwin)

motorcontrol_frame = LabelFrame(frame_l, text="Motor Controls", padx=5, pady=5)
motorcontrol_frame.grid(row=0, column=0, sticky=N)

xyzresolution_frame = Frame(frame_l, padx=5, pady=5)
xyzresolution_frame.grid(row=1, column=0)
Xaxisresolution_frame = LabelFrame(xyzresolution_frame, text="X Axis Resolution", padx=5, pady=5)
Yaxisresolution_frame = LabelFrame(xyzresolution_frame, text="Y Axis Resolution", padx=5, pady=5)
Zaxisresolution_frame = LabelFrame(xyzresolution_frame, text="Z Axis Resolution", padx=5, pady=5)
Xaxisresolution_frame.grid(row=0, column=0, sticky=N)
Yaxisresolution_frame.grid(row=1, column=0)
Zaxisresolution_frame.grid(row=2, column=0)

entercommand_frame = LabelFrame(frame_r, text="Enter Command", padx=5, pady=5)
entercommand_frame.grid(row=1, column=1, sticky=W)

selectfluid_frame = LabelFrame(frame_r, text="Select Working Fluid", padx=5, pady=5)
selectfluid_frame.grid(row=2, column=1, sticky=W)

options_frame = LabelFrame(frame_r, text="Options", padx=5, pady=5)
options_frame.grid(row=3, column=1, sticky=W)

solenoid_frame = LabelFrame(frame_r, text="Solenoid Valve", padx=5, pady=5)
solenoid_frame.grid(row=4, column=1, sticky=W)

Button(motorcontrol_frame, text="+X",  bg="#f9dfad", fg="black", command=lambda:send_command("b")).grid(row=2, column=2, sticky=W+E, padx=5, pady=5)
Button(motorcontrol_frame, text="-X",  bg="#f9dfad", fg="black", command=lambda:send_command("a")).grid(row=2, column=0, sticky=W+E, padx=5, pady=5)
Button(motorcontrol_frame, text="+Y",  bg="#716ff8", fg="black", command=lambda:send_command("d")).grid(row=1, column=1, sticky=W+E, padx=5, pady=5)
Button(motorcontrol_frame, text="-Y",  bg="#716ff8", fg="black", command=lambda:send_command("c")).grid(row=3, column=1, sticky=W+E, padx=5, pady=5)
Button(motorcontrol_frame, text="+Z",  bg="#f8716f", fg="black", command=lambda:send_command("e")).grid(row=0, column=1, sticky=W+E, padx=5, pady=5)
Button(motorcontrol_frame, text="-Z",  bg="#f8716f", fg="black", command=lambda:send_command("f")).grid(row=4, column=1, sticky=W+E, padx=5, pady=5)
Button(motorcontrol_frame, text="Solenoid ON",   bg="#ade4f9", fg="black", command=lambda:send_command("i")).grid(row=0, column=3, sticky=W+E, padx=5, pady=5)

motorcontrol_frame.columnconfigure(0, weight=1)
motorcontrol_frame.columnconfigure(1, weight=1)
motorcontrol_frame.columnconfigure(2, weight=1)
motorcontrol_frame.columnconfigure(3, weight=1)

x_res = Entry(Xaxisresolution_frame, width=15)
x_res.grid(row=0, column=0)
y_res = Entry(Yaxisresolution_frame, width=15)
y_res.grid(row=0, column=0)
z_res = Entry(Zaxisresolution_frame, width=15)
z_res.grid(row=0, column=0)
Spinbox(xyzresolution_frame, values=("um", "mm", "step"), textvariable=xyz_unt, width=5).grid(row=1, column=1)
xyz_unt.set("mm")

command_to_send = Entry(entercommand_frame, width=10)
command_to_send.grid(row=1, column=0, sticky=W)
Button(entercommand_frame, text="Send", command=get_textbox_input).grid(row=1, column=1, sticky=W)

Button(selectfluid_frame, text="SU-8",           command=dispenseSU8).grid(row=0, column=0, sticky=W)

Button(options_frame, text="Home XYZ",       command=homeAxes).grid(row=0, column=0, sticky=W)
Button(options_frame, text="Zero Axes",      command=zeroAxes).grid(row=1, column=0, sticky=W)
Button(options_frame, text="Disable Motors", command=disableMotors).grid(row=2, column=0, sticky=W)
Button(options_frame, text="Enable Motors",  command=enableMotors).grid(row=3, column=0, sticky=W)

# Solenoid open/close/pulse (unchanged)
Button(solenoid_frame, text="Open",  bg="#90EE90", fg="black", command=solenoidOn).grid(row=0, column=0, sticky=W+E, padx=5, pady=5)
Button(solenoid_frame, text="Close", bg="#FFB6C1", fg="black", command=solenoidOff).grid(row=0, column=1, sticky=W+E, padx=5, pady=5)
Button(solenoid_frame, text="Pulse", bg="#ade4f9", fg="black", command=solenoidPulse).grid(row=0, column=2, sticky=W+E, padx=5, pady=5)

# NEW: dedicated pulse duration field
Label(solenoid_frame, text="Duration (ms):").grid(row=1, column=0, sticky=W, pady=3)
pulse_duration = Entry(solenoid_frame, width=8)
pulse_duration.insert(0, "100")
pulse_duration.grid(row=1, column=1, sticky=W, padx=5)

# NEW: pulse count + multi-pulse button
Label(solenoid_frame, text="Count:").grid(row=2, column=0, sticky=W, pady=3)
pulse_count = Entry(solenoid_frame, width=8)
pulse_count.insert(0, "50")
pulse_count.grid(row=2, column=1, sticky=W, padx=5)
Button(solenoid_frame, text="Multi Pulse", bg="#716ff8", fg="black", command=solenoidMultiPulse).grid(row=2, column=2, sticky=W+E, padx=5, pady=5)


# Automated coating frame
coating_frame = LabelFrame(frame_r, text="Automated Coating", padx=5, pady=5)
coating_frame.grid(row=5, column=1, sticky=W)

points_label = Label(coating_frame, text="Points recorded: 0")
points_label.grid(row=0, column=0, columnspan=3, sticky=W, padx=5)

Button(coating_frame, text="Record Point", bg="#ade4f9", fg="black", command=recordPoint).grid(row=1, column=0, sticky=W+E, padx=5, pady=5)
Button(coating_frame, text="Undo Last", command=undoLastPoint).grid(row=1, column=1, sticky=W+E, padx=5, pady=5)
Button(coating_frame, text="Clear Points", command=clearPoints).grid(row=1, column=2, sticky=W+E, padx=5, pady=5)
Button(coating_frame, text="Go to Pt 1", command=goToFirstPoint).grid(row=4, column=0, columnspan=3, sticky=W+E, padx=5, pady=5)
Button(coating_frame, text="Export Points", command=exportPoints).grid(row=3, column=0, columnspan=3, sticky=W+E, padx=5, pady=5)

Button(coating_frame, text="Dry Run", bg="#f9dfad", fg="black", command=lambda: runCoating(dry_run=True)).grid(row=2, column=0, sticky=W+E, padx=5, pady=5)
Button(coating_frame, text="Start",   bg="#90EE90", fg="black", command=lambda: runCoating(dry_run=False)).grid(row=2, column=1, sticky=W+E, padx=5, pady=5)
Button(coating_frame, text="STOP",    bg="#FFB6C1", fg="black", command=stopCoating).grid(row=2, column=2, sticky=W+E, padx=5, pady=5)

# Dip-transfer controls (acupuncture needle method)
dip_frame = LabelFrame(frame_r, text="Dip Transfer (Acupuncture Needle)", padx=5, pady=5)
dip_frame.grid(row=6, column=1, sticky=W)

reservoir_label = Label(dip_frame, text="Reservoir: not set")
reservoir_label.grid(row=0, column=0, columnspan=3, sticky=W, padx=5)
Button(dip_frame, text="Set Reservoir", bg="#ade4f9", fg="black", command=setReservoir).grid(row=1, column=0, columnspan=3, sticky=W+E, padx=5, pady=5)

Label(dip_frame, text="Pads per dip:").grid(row=2, column=0, sticky=W, padx=5)
pads_per_dip_entry = Entry(dip_frame, width=6)
pads_per_dip_entry.insert(0, "1")
pads_per_dip_entry.grid(row=2, column=1, sticky=W)

def applyDipSettings():
    try:
        DIP_PARAMS["pads_per_dip"] = max(1, int(pads_per_dip_entry.get()))
        print(f"=== Re-dip every {DIP_PARAMS['pads_per_dip']} pad(s) ===")
    except ValueError:
        print("=== Invalid pads-per-dip value ===")

Button(dip_frame, text="Apply", command=applyDipSettings).grid(row=2, column=2, sticky=W+E, padx=5)

Button(dip_frame, text="Dry Run", bg="#f9dfad", fg="black", command=lambda: runDipCoating(dry_run=True)).grid(row=3, column=0, sticky=W+E, padx=5, pady=5)
Button(dip_frame, text="Start",   bg="#90EE90", fg="black", command=lambda: runDipCoating(dry_run=False)).grid(row=3, column=1, sticky=W+E, padx=5, pady=5)
Button(dip_frame, text="STOP",    bg="#FFB6C1", fg="black", command=stopCoating).grid(row=3, column=2, sticky=W+E, padx=5, pady=5)

# Smear coating frame
smear_frame = LabelFrame(frame_r, text="Smear Coating (drag along pad lines)", padx=5, pady=5)
smear_frame.grid(row=7, column=1, sticky=W)

Label(smear_frame, text="Height offset (mm):").grid(row=0, column=0, sticky=W, padx=5)
smear_offset_entry = Entry(smear_frame, width=6)
smear_offset_entry.insert(0, "0.5")
smear_offset_entry.grid(row=0, column=1, sticky=W)
Label(smear_frame, text="(0 = contact)").grid(row=0, column=2, sticky=W)

def _smear_offset():
    try:
        return float(smear_offset_entry.get())
    except ValueError:
        return 0.5

Button(smear_frame, text="Rehearse (in air)", bg="#f9dfad", fg="black",
       command=lambda: runSmear(dry_run=True, height_offset=_smear_offset())).grid(row=1, column=0, sticky=W+E, padx=5, pady=5)
Button(smear_frame, text="Smear", bg="#90EE90", fg="black",
       command=lambda: runSmear(dry_run=False, height_offset=_smear_offset())).grid(row=1, column=1, sticky=W+E, padx=5, pady=5)
Button(smear_frame, text="STOP", bg="#FFB6C1", fg="black",
       command=stopCoating).grid(row=1, column=2, sticky=W+E, padx=5, pady=5)

# Teach & Repeat frame
right_col = Frame(mainwin)
teach_frame = LabelFrame(right_col, text="Teach & Repeat", padx=5, pady=5)
teach_frame.pack(side="top", anchor="n")

teach_label = Label(teach_frame, text="Steps: 0")
teach_label.grid(row=0, column=0, columnspan=3, sticky=W, padx=5)

Button(teach_frame, text="Dip",        bg="#ade4f9", fg="black", command=teachDip).grid(row=1, column=0, sticky=W+E, padx=3, pady=3)
Button(teach_frame, text="Deposit",    bg="#ade4f9", fg="black", command=teachDeposit).grid(row=1, column=1, sticky=W+E, padx=3, pady=3)
Button(teach_frame, text="Move",       command=teachMove).grid(row=1, column=2, sticky=W+E, padx=3, pady=3)

Button(teach_frame, text="Drag Start", bg="#f9dfad", fg="black", command=teachDragStart).grid(row=2, column=0, sticky=W+E, padx=3, pady=3)
Button(teach_frame, text="Drag End",   bg="#f9dfad", fg="black", command=teachDragEnd).grid(row=2, column=1, sticky=W+E, padx=3, pady=3)
Button(teach_frame, text="Undo",       command=teachUndo).grid(row=2, column=2, sticky=W+E, padx=3, pady=3)

Button(teach_frame, text="Clear",      command=teachClear).grid(row=3, column=0, sticky=W+E, padx=3, pady=3)
Button(teach_frame, text="Export",     command=teachExport).grid(row=3, column=1, sticky=W+E, padx=3, pady=3)

Button(teach_frame, text="Dry Run", bg="#f9dfad", fg="black", command=lambda: teachReplay(dry_run=True)).grid(row=4, column=0, sticky=W+E, padx=3, pady=3)
Button(teach_frame, text="Replay",  bg="#90EE90", fg="black", command=lambda: teachReplay(dry_run=False)).grid(row=4, column=1, sticky=W+E, padx=3, pady=3)
Button(teach_frame, text="STOP",    bg="#FFB6C1", fg="black", command=stopCoating).grid(row=4, column=2, sticky=W+E, padx=3, pady=3)

frame_l.grid(row=0, column=0, sticky=N)
frame_r.grid(row=0, column=1, sticky=N)
right_col.grid(row=0, column=2, sticky="n", padx=10)

# Dip-Drop-Drag frame
ddd_frame = LabelFrame(right_col, text="Dip-Drop-Drag (2-drop routine)", padx=5, pady=5)
ddd_frame.pack(side="top", anchor="n", pady=(10,0))

Button(ddd_frame, text="Dry Run", bg="#f9dfad", fg="black",
       command=lambda: runDipDropDrag(dry_run=True)).grid(row=0, column=0, sticky=W+E, padx=3, pady=3)
Button(ddd_frame, text="Start", bg="#90EE90", fg="black",
       command=lambda: runDipDropDrag(dry_run=False)).grid(row=0, column=1, sticky=W+E, padx=3, pady=3)
Button(ddd_frame, text="STOP", bg="#FFB6C1", fg="black",
       command=stopCoating).grid(row=0, column=2, sticky=W+E, padx=3, pady=3)


# Developer / IPA ip-rinse frame
rinse_frame = LabelFrame(right_col, text="Developer / IPA Dip-Rinse", padx=5, pady=5)
rinse_frame.pack(side="top", anchor="n", pady=(10, 0))

station_label = Label(rinse_frame, text="dev: not set   ipa: not set")
station_label.grid(row=0, column=0, columnspan=3, sticky=W, padx=5)

safez_label = Label(rinse_frame, text="safe_z: not set")
safez_label.grid(row=1, column=0, columnspan=3, sticky=W, padx=5)

Button(rinse_frame, text="Rec Developer", bg="#ade4f9", fg="black",
       command=lambda: recordStation("developer")).grid(row=2, column=0, sticky=W+E, padx=3, pady=3)
Button(rinse_frame, text="Rec IPA", bg="#ade4f9", fg="black",
       command=lambda: recordStation("ipa")).grid(row=2, column=1, sticky=W+E, padx=3, pady=3)
Button(rinse_frame, text="Set Safe Z", bg="#ade4f9", fg="black",
       command=recordSafeZ).grid(row=2, column=2, sticky=W+E, padx=3, pady=3)

Button(rinse_frame, text="Export Stations",
       command=exportStations).grid(row=3, column=0, columnspan=3, sticky=W+E, padx=3, pady=3)

depth_label = Label(rinse_frame, text="dev_depth: 0.000 mm   dip: -1250 um   [custom]")
depth_label.grid(row=4, column=0, columnspan=3, sticky=W, padx=5)

Button(rinse_frame, text="< Prev bracket", bg="#ade4f9", fg="black",
       command=prevTestDepth).grid(row=5, column=0, sticky=W+E, padx=3, pady=3)
Button(rinse_frame, text="Next bracket >", bg="#ade4f9", fg="black",
       command=nextTestDepth).grid(row=5, column=1, sticky=W+E, padx=3, pady=3)

Button(rinse_frame, text="Deeper +0.02", bg="#f9dfad", fg="black",
       command=devDepthDeeper).grid(row=6, column=0, sticky=W+E, padx=3, pady=3)
Button(rinse_frame, text="Shallower -0.02", bg="#f9dfad", fg="black",
       command=devDepthShallower).grid(row=6, column=1, sticky=W+E, padx=3, pady=3)

Button(rinse_frame, text="Run Dip-Rinse", bg="#90EE90", fg="black",
       command=runDipRinse).grid(row=7, column=0, columnspan=2, sticky=W+E, padx=3, pady=3)
Button(rinse_frame, text="STOP", bg="#FFB6C1", fg="black",
       command=stopCoating).grid(row=7, column=2, sticky=W+E, padx=3, pady=3)


# Contact test frame - find dev_depth where tips first touch liquid
contact_frame = LabelFrame(right_col, text="Contact Test (water, bare PCB)", padx=5, pady=5)
contact_frame.pack(side="top", anchor="n", pady=(10, 0))

contact_label = Label(contact_frame, text="depth: 1.150 mm   (step 0.050)")
contact_label.grid(row=0, column=0, columnspan=3, sticky=W, padx=5)

Button(contact_frame, text="Deeper +0.05", bg="#f9dfad", fg="black",
       command=contactStepDown).grid(row=1, column=0, sticky=W+E, padx=3, pady=3)
Button(contact_frame, text="Shallower -0.05", bg="#f9dfad", fg="black",
       command=contactStepUp).grid(row=1, column=1, sticky=W+E, padx=3, pady=3)

Button(contact_frame, text="Run Dip", bg="#90EE90", fg="black",
       command=runContactTest).grid(row=2, column=0, columnspan=2, sticky=W+E, padx=3, pady=3)
Button(contact_frame, text="STOP", bg="#FFB6C1", fg="black",
       command=stopCoating).grid(row=2, column=2, sticky=W+E, padx=3, pady=3)


mainwin.mainloop()