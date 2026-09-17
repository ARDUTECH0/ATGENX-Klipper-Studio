# Klipper Studio - User guide

This guide explains every page and every setting of Klipper Studio 1.0.0-beta.4, and walks through the most common tasks. The same explanations appear inside the app in the help panel on the right - point at any setting to read them.

## Contents

- 1. Install and start
- 2. The screen
- 3. Common tasks
- 4. Pages and settings
- 5. Features and catalog
- 6. How the generated printer.cfg is organized
- 7. Safety and backups
- 8. FAQ

## 1. Install and start

Install Python 3.9 or newer, then:



```bash
git clone https://github.com/ARDUTECH0/ATGENX-Klipper-Studio.git
cd ATGENX-Klipper-Studio
pip install -r requirements.txt
python -m studio
```



On Windows you can double-click `run.bat`. Language: toolbar -> العربية / English.

## 2. The screen

- **Sidebar** - the pages, top to bottom in the order you normally use them. A page with problems shows a badge: ✖ errors, ▲ warnings.
- **Page** - the settings. Use Next / Back at the bottom, or click any page in the sidebar.
- **Help panel** (right) - what the current page is for, and the explanation of the setting under the mouse, including where it goes in printer.cfg. Hide it from the toolbar.
- **Toolbar** - new project, open / save a project (.studio.json), open a local printer.cfg, help panel, user guide, language, support, about.

## 3. Common tasks

### Set up a printer that already runs Klipper

1. Start -> **I have a running Klipper printer**.
2. Type the printer address, press **Test connection**, then **Import from printer**. Every setting and every config file is loaded.
3. Check **Board** (the detected board is selected) and change what you need on the other pages.
4. Open **Review & upload**: fix every red check (click it to jump to its page), read **Differences**, then **Upload and restart**.

### Set up a new printer

1. Start -> **Set up a new printer**, choose your board and press **Apply board pins**.
2. Untick **Keep my motor directions** for a new printer so the board's default directions are used.
3. Fill **Machine**, **Motors & drivers**, **Hotend & bed**, **Probe** and switch features on in **Features**.
4. **Review & upload** -> **Save to computer**, or connect and upload.
5. On the printer: run `PID_CALIBRATE`, `PROBE_CALIBRATE` and `SHAPER_CALIBRATE`, each followed by `SAVE_CONFIG`. Import again afterwards - the app keeps those values.

### Move a motor to another driver socket / add a second Z motor

1. **Motors & drivers** -> in the motor's row choose another **Driver socket**. All its pins, bus pins and DIAG pin move with it.
2. **Add motor** -> Z2 (or Z3, Z4, X2, Y2). It takes the next free socket and the settings of the first Z motor.
3. With a probe, `z_tilt` is added automatically; choose `quad_gantry_level` for a 4-motor moving gantry. Run `Z_TILT_ADJUST` or `QUAD_GANTRY_LEVEL` after homing.

### Turn on sensorless homing

1. Put the DIAG jumpers for X and Y on the board (see its manual) and unplug the X/Y endstop switches.
2. **Features** -> **Sensorless homing** on (or tick **Sensorless** per motor). Hold current is removed automatically.
3. Upload, then tune: `SET_TMC_FIELD STEPPER=stepper_x FIELD=SGTHRS VALUE=255` and lower it until `G28 X` stops at the end without stopping early. Put the final value in **StallGuard threshold**.

### Switch a feature on or off, or add a new one

1. **Features -> Built-in**: flip the switch. Whatever it needs is switched on with it (for example adaptive mesh turns on the probe, print macros and exclude object).
2. **Features -> In your file**: every other section of printer.cfg. Off comments it out with `#`; on removes the `#` again. Nothing is deleted.
3. **Features -> Add a feature**: press **Add** on a catalog item, edit the template (fill empty pins), then upload. It is added at the end of printer.cfg.

### Edit moonraker.conf, crowsnest.conf or any other file

1. **All config files** -> **Load all files from printer**.
2. Click a file or a section in the tree, edit, then **Save to printer**. A backup is made and only the matching service is restarted.

### Fix a Klipper error

1. **Troubleshooter** -> **Check printer now** (or paste the error message).
2. Read the cause and the steps, and press **Open the related page** to fix it there.

## 4. Pages and settings

### Start

Pick what you want to do. Every path ends on Review & upload, where you see the checks and the exact changes before anything reaches the printer.

### Connection

1. Type the printer address (the same one you open Mainsail or Fluidd with).  
2. Test connection: you should see Klipper, Moonraker and the MCU.  
3. Import from printer: every field is filled from your printer.cfg and its included files.  
  
Nothing is changed on the printer here.

| Setting | What it does | In printer.cfg |
|---|---|---|
| **Printer address** | The printer's IP address or host name, the same one you open Mainsail or Fluidd with. Example: 192.168.1.50 or mainsailos.local. |  |
| **Port** | Moonraker's port. Leave 7125 unless you changed it. | `moonraker.conf [server] port` |
| **Printer name** | A name for this project. It appears in the header of the generated file and in the project file name. |  |

### Board

1. Choose your board (type to search). After importing, the detected board is already selected.  
2. Apply board pins fills every motor socket, heater, fan and sensor pin.  
3. Detect on printer finds the serial path of the board.  
  
Keep 'Keep my motor directions' ticked on a printer that already moves correctly.

| Setting | What it does | In printer.cfg |
|---|---|---|
| **Board** | Your controller board. The app knows its driver sockets, heater and fan outputs, sensor inputs and the required extra sections. Choose Custom if it isn't listed and type the pins yourself. |  |
| **Add the sections this board requires (USB pull-up, digipots, ...)** | Some boards need extra sections to work at all (USB pull-up, stepper current PWM, digipots). Leave it on for a new printer. | `[static_digital_output ...] / [output_pin ...]` |
| **Serial** | How Klipper finds the board. Use Detect on printer and pick the /dev/serial/by-id/usb-Klipper_... path. For CAN boards write canbus_uuid: <uuid>. | `[mcu] serial` |
| **Keep my motor directions (recommended when importing)** | Keeps the Invert setting of every motor when applying a board. Untick it only for a new printer, to use the board file's default directions. | `[stepper_*] dir_pin` |

### Features

Built-in: switch app features on or off - what a feature needs is switched on with it.  
In your file: every other section of printer.cfg. Off comments it out with #, on removes the #.  
Add a feature: pick a well-known section or plugin, edit the template, and it is added at the end of printer.cfg.  
  
All changes show up in Review & upload before anything is sent.

### Machine

Set the build volume and the motion limits. Start conservative (acceleration 3000, velocity 300) and raise them after input shaper tuning.

| Setting | What it does | In printer.cfg |
|---|---|---|
| **Kinematics** | Cartesian: X and Y each move one axis (bed slingers like Ender 3, Prusa). CoreXY: two motors move the head together (Voron, Bambu-style frames). | `[printer] kinematics` |
| **X size** | Furthest X position the nozzle can reach. Measure it: home, then move X in small steps until it touches the end. | `[stepper_x] position_max` |
| **Y size** | Furthest Y position the nozzle can reach. | `[stepper_y] position_max` |
| **Max Z height** | Maximum print height. | `[stepper_z] position_max` |
| **X minimum** | Lowest X position, usually 0. Negative when the endstop sits before the bed edge. | `[stepper_x] position_min` |
| **Y minimum** | Lowest Y position, usually 0. | `[stepper_y] position_min` |
| **Z minimum** | Lowest Z. A small negative value (-2 to -5) lets you lower the nozzle during PROBE_CALIBRATE. | `[stepper_z] position_min` |
| **X endstop position** | X position when the endstop triggers: 0 if the endstop is at the minimum, position_max if it's at the maximum. | `[stepper_x] position_endstop` |
| **Y endstop position** | Y position when the endstop triggers. | `[stepper_y] position_endstop` |
| **Max velocity** | Speed limit for any move. The slicer can't go faster. 200-300 mm/s for bed slingers, 300-500 for CoreXY. | `[printer] max_velocity` |
| **Max acceleration** | Acceleration limit. Too high causes ringing and layer shifts. Start at 2000-3000; after SHAPER_CALIBRATE use the value it recommends. | `[printer] max_accel` |
| **Max Z velocity** | Z speed limit. Lead screws: 10-20 mm/s. Belt-driven Z: higher. | `[printer] max_z_velocity` |
| **Max Z acceleration** | Z acceleration limit. Must not be higher than max_accel. Lead screws: 100-500. | `[printer] max_z_accel` |
| **Square corner velocity** | Speed through 90° corners. 5 is the Klipper default; lower it if corners bulge. | `[printer] square_corner_velocity` |
| **Homing speed** | Speed while homing X and Y. 50 is typical; sensorless homing often needs 40-100. | `[stepper_x/y] homing_speed` |

### Motors & drivers

Each row is one motor.  
1. Driver socket: where the motor is plugged on the board.  
2. Driver: the driver module in that socket.  
3. Current, microsteps, rotation distance.  
4. Click a row for its details: hold current, step angle, sensorless homing, bus pins, TMC Autotune.  
  
Add motor: second X/Y motor (AWD) or up to 4 Z motors. Copy to motors of the same axis keeps Z motors identical.

| Setting | What it does | In printer.cfg |
|---|---|---|
| **Method** | With 2-4 Z motors: z_tilt levels a bed or a fixed gantry (run Z_TILT_ADJUST). quad_gantry_level is for a Voron 2.4 style gantry with 4 motors (run QUAD_GANTRY_LEVEL). Needs a probe. | `[z_tilt] / [quad_gantry_level]` |
| **Probe points** | Where the probe measures, one X, Y per line. Leave empty and the app places them near each Z motor inside the reachable area. | `[z_tilt] points / [quad_gantry_level] points` |
| **Gantry corners (QGL)** | Two opposite corners of the gantry (front-left, back-right), usually outside the bed. Empty = estimated from the bed size. | `[quad_gantry_level] gantry_corners` |
| **Motor supply voltage (Autotune)** | Power supply voltage of the motors, used only by TMC Autotune. 24 V for most printers. | `[autotune_tmc ...] voltage` |
| **Driver socket** | The driver socket on the board this motor is plugged into. Changing it moves all its pins, the driver bus pins and the DIAG pin at once. | `[stepper_*] step_pin / dir_pin / enable_pin` |
| **Driver** | The driver module in that socket. TMC2209/2208 use UART, TMC2130/5160/2240 use SPI. Standalone means A4988, DRV8825 or a TMC in standalone mode (no current setting). | `[tmcXXXX stepper_*]` |
| **Current (A)** | RMS current while moving. Start at about 70% of the motor's rated current (a 1.5 A motor -> ~1.0 A). Too high: hot motors and drivers. Too low: skipped steps. | `[tmcXXXX stepper_*] run_current` |
| **Microsteps** | Steps per full step. 16 is the best default (with interpolate). 32 on X/Y can be quieter; more than 64 overloads the board. | `[stepper_*] microsteps` |
| **Rotation distance** | Distance moved per motor revolution. Belts: pulley teeth x belt pitch (20T GT2 = 40). Lead screws: pitch x starts (T8x8 = 8, T8x2 = 2). Extruder: calibrate by extruding 100 mm and measuring. | `[stepper_*] rotation_distance` |
| **Invert** | Tick it if the motor turns the wrong way. Test with STEPPER_BUZZ or a small move after homing. | `[stepper_*] dir_pin: !PIN` |
| **StealthChop (mm/s)** | spreadCycle (0) is accurate and strong - best for X/Y. A speed turns on silent stealthChop below it. 999999 = always silent (fine for Z and the extruder). | `[tmcXXXX stepper_*] stealthchop_threshold` |
| **Sensorless** | Home X/Y without endstop switches, using the driver's StallGuard. Needs a TMC2209/2130/5160/2240, the DIAG jumper on the board and tuning of the threshold. | `[stepper_x] endstop_pin: tmc2209_stepper_x:virtual_endstop` |
| **Hold current** | Lower current while the motor stands still. Usually leave it empty (same as run current) - Klipper recommends that, and it's required for sensorless homing. | `[tmcXXXX stepper_*] hold_current` |
| **Sense resistor** | Resistor value on the driver module. Leave the default unless your module is different (BTT TMC5160 Pro = 0.075, TMC2660 on Duet 2 = 0.051). | `[tmcXXXX stepper_*] sense_resistor` |
| **Motor step angle** | 1.8° motors (most printers) = 200. 0.9° motors (e.g. LDO 0.9° on Voron) = 400. | `[stepper_*] full_steps_per_rotation` |
| **Interpolate to 256 microsteps (smoother, tiny position error)** | The driver smooths each microstep into 256. Quieter and smoother with a very small position error. Keep it on unless you need maximum dimensional precision. | `[tmcXXXX stepper_*] interpolate` |
| **StallGuard threshold** | Sensorless sensitivity. TMC2209: 255 most sensitive, lower it until homing stops at the end without stopping early. TMC2130/5160/2240: -64 most sensitive, raise it. Tune live with SET_TMC_FIELD. | `[tmc2209 stepper_x] driver_SGTHRS / [tmc5160 stepper_x] driver_SGT` |
| **DIAG pin** | The board pin connected to the driver's DIAG output - on most boards it's the endstop header of that socket, with a DIAG jumper. TMC2209: ^PIN. SPI drivers: ^!PIN. | `[tmc2209 stepper_x] diag_pin` |
| **Z pivot position (X, Y)** | Where this Z motor (lead screw or pivot) is, in nozzle coordinates X, Y. Empty = estimated (2 motors: left/right; 3: front-left, back, front-right; 4: corners). | `[z_tilt] z_positions` |
| **TMC Autotune motor** | Optional: the klipper_tmc_autotune plugin tunes the driver for your exact motor model. Install the plugin first, then choose your motor (type to search). | `[autotune_tmc stepper_*] motor` |
| **Autotune goal** | auto = performance for X/Y and silent for Z/extruder. Choose silent or performance to force one. | `[autotune_tmc stepper_*] tuning_goal` |
| **uart_pin / tx_pin / uart_address / cs_pin / spi_bus** | How the board talks to the driver. Filled from the board. uart_address is used on boards with one shared UART line (SKR Mini, Manta...). | `[tmcXXXX stepper_*] uart_pin / cs_pin ...` |

### Hotend & bed

Set the hotend and bed thermistors and heater limits. After the first start run PID_CALIBRATE for both heaters and SAVE_CONFIG; the app keeps those values.

| Setting | What it does | In printer.cfg |
|---|---|---|
| **Nozzle diameter** | Nozzle size, usually 0.4 mm. | `[extruder] nozzle_diameter` |
| **Filament diameter** | 1.75 mm for almost all printers. | `[extruder] filament_diameter` |
| **Bowden (not direct drive)** | Tick for a Bowden tube (extruder on the frame). It only changes the pressure advance advice: Bowden needs 0.3-0.8, direct drive 0.02-0.1. |  |
| **Pressure advance** | Compensates filament pressure in the nozzle: sharper corners, less stringing and blobs. Calibrate with a pressure advance tower (Orca Slicer has one). | `[extruder] pressure_advance` |
| **Pressure advance smooth time** | Smoothing for pressure advance. Keep 0.040 unless you know why to change it. | `[extruder] pressure_advance_smooth_time` |
| **Hotend thermistor** | Hotend thermistor type. Most stock hotends: EPCOS 100K B57560G104F or Generic 3950. A wrong type reads the wrong temperature. | `[extruder] sensor_type` |
| **PID Kp** | PID values come from PID_CALIBRATE HEATER=extruder TARGET=220, then SAVE_CONFIG. Don't copy them from another printer. | `[extruder] pid_Kp` |
| **PID Ki** | See PID Kp. | `[extruder] pid_Ki` |
| **PID Kd** | See PID Kp. | `[extruder] pid_Kd` |
| **Hotend max temperature** | Klipper shuts down above this. 260-280 for PTFE-lined hotends, up to 300+ for all-metal. | `[extruder] max_temp` |
| **Bed thermistor** | Bed thermistor type. | `[heater_bed] sensor_type` |
| **PID Kp** | From PID_CALIBRATE HEATER=heater_bed TARGET=60, then SAVE_CONFIG. | `[heater_bed] pid_Kp` |
| **PID Ki** | See bed PID Kp. | `[heater_bed] pid_Ki` |
| **PID Kd** | See bed PID Kp. | `[heater_bed] pid_Kd` |
| **Bed max temperature** | Bed safety limit, usually 110-130. | `[heater_bed] max_temp` |
| **Cold room / strong part fan - relaxed heater verification** | Relaxed heater verification for cold rooms or strong part fans that cause 'Heater not heating at expected rate'. Keep it off otherwise. | `[verify_heater extruder] / [verify_heater heater_bed]` |
| **Part fan max power** | Caps the part cooling fan. 1.0 = full power; lower it if 100% is too strong for your fan. | `[fan] max_power` |
| **Hotend fan turns on at** | The heatsink fan turns on above this hotend temperature. 50 °C is safe. | `[heater_fan hotend_fan] heater_temp` |

### Probe & leveling

1. Choose the probe type and its X/Y offset from the nozzle.  
2. The mesh area is calculated so the probe can reach every point.  
3. With 2-4 Z motors the leveling (z_tilt / quad gantry) is on the Motors page.  
  
Z offset: run PROBE_CALIBRATE, then SAVE_CONFIG.

| Setting | What it does | In printer.cfg |
|---|---|---|
| **Type** | Inductive/switch probe, BLTouch (or clones like CR Touch), or none (Z endstop switch). A probe enables bed mesh and Z leveling. | `[probe] / [bltouch]` |
| **X offset** | Probe position relative to the nozzle on X. Probe to the right of the nozzle = positive, left = negative. | `[probe] x_offset` |
| **Y offset** | Probe behind the nozzle = positive, in front = negative. | `[probe] y_offset` |
| **Z offset** | Distance between probe trigger and nozzle. Run PROBE_CALIBRATE (paper test), then SAVE_CONFIG. The app reads it back from SAVE_CONFIG. | `[probe] z_offset` |
| **Samples per point** | How many times each point is probed. 2-3 is more reliable. | `[probe] samples` |
| **Margin from the edges** | Distance kept from the bed edges (clips, magnets). The app also keeps the probe reachable. | `[bed_mesh] mesh_min / mesh_max` |
| **Points per axis** | Points per axis. 5 is a good default, 7-9 for large or warped beds. | `[bed_mesh] probe_count` |

### LEDs & extras

Optional features. Each one adds its own section to printer.cfg and can be switched off later - the app removes the section again.

| Setting | What it does | In printer.cfg |
|---|---|---|
| **NeoPixel / WS2812 strip installed** | A WS2812/NeoPixel strip connected to the board. | `[neopixel case_leds]` |
| **LED count** | Number of LEDs on the strip. | `[neopixel case_leds] chain_count` |
| **Color order** | Try GRB first; if red and green are swapped use RGB. | `[neopixel case_leds] color_order` |
| **Live indicators (fill with temperature and print progress)** | Animated indicators: the strip fills with heater temperature and print progress. Requires the klipper-led_effect plugin. | `[led_effect ...]` |
| **Enabled** | Cancels ringing so you can print faster. Measure the frequencies with SHAPER_CALIBRATE (accelerometer) or a ringing tower. | `[input_shaper]` |
| **{axis} frequency** | Resonance frequency of X, from SHAPER_CALIBRATE. | `[input_shaper] shaper_freq_x` |
| **{axis} type** | Shaper algorithm. mzv is a good default; use what SHAPER_CALIBRATE recommends. | `[input_shaper] shaper_type_x` |
| **{axis} frequency** | Resonance frequency of Y. On a bed slinger measure it with the sensor on the bed. | `[input_shaper] shaper_freq_y` |
| **{axis} type** | Shaper algorithm for Y. | `[input_shaper] shaper_type_y` |
| **Z frequency (0 = off)** | Optional Z shaping (0 = off). Only useful with fast Z moves. | `[input_shaper] shaper_freq_z` |
| **{axis} type** | Shaper algorithm for Z. | `[input_shaper] shaper_type_z` |
| **Damping ratio** | Keep 0.1 unless SHAPER_CALIBRATE tells you otherwise. | `[input_shaper] damping_ratio_x / y` |
| **Filament runout sensor (pauses the print)** | Pauses the print when the filament runs out. | `[filament_switch_sensor filament_sensor]` |
| **Arc support G2/G3** | Accept G2/G3 arcs (Arc Fitting in the slicer). | `[gcode_arcs]` |
| **Cancel single objects during a print** | Cancel one failed part during a print. Turn on 'Label objects' in the slicer. | `[exclude_object]` |
| **Show Raspberry Pi / host temperature** | Shows the Raspberry Pi temperature in Mainsail/Fluidd. | `[temperature_sensor host]` |
| **Show controller board temperature (not on LPC176x / AVR)** | Shows the board temperature. Not available on LPC176x (SKR 1.3/1.4) and AVR boards. | `[temperature_sensor mcu]` |
| **Turn off when idle after (0 = Klipper default)** | Turn off motors and heaters after this many idle minutes. 0 = Klipper default (10 minutes). | `[idle_timeout] timeout` |
| **Enabled - turn on 'Use firmware retraction' in your slicer** | The printer handles retraction (G10/G11) instead of the slicer, so you can tune it during a print with SET_RETRACTION. Enable 'Use firmware retraction' in the slicer. | `[firmware_retraction]` |
| **Retract length** | Direct drive: 0.5-1 mm. Bowden: 3-6 mm. | `[firmware_retraction] retract_length` |
| **Retract speed** | Typically 30-50 mm/s. | `[firmware_retraction] retract_speed` |
| **Unretract speed** | Typically 20-40 mm/s. | `[firmware_retraction] unretract_speed` |
| **Generate START_PRINT, END_PRINT and M600 (your own macros with these names are never replaced)** | Ready macros: heat, home, level, mesh, purge / retract, park, cool down / filament change. Put START_PRINT and END_PRINT in the slicer's start and end G-code. | `[gcode_macro START_PRINT] / END_PRINT / M600` |
| **Adaptive mesh - probe only where the part is** | Measure the bed only under the printed parts - faster starts. Needs exclude object and 'Label objects' in the slicer. | `BED_MESH_CALIBRATE ADAPTIVE=1` |
| **Purge line before printing** | Draws a line at the front-left edge before printing to prime the nozzle. | `START_PRINT` |

### Pins

Every pin in one table: motor pins, driver bus pins, heaters, fans, probe, LEDs. Filled from the board page - edit only if your wiring differs.  
^ = pull-up, ~ = pull-down, ! = inverted.

### Wiring map

The wiring map: your board in the middle and every device around it, each line labelled with the pin it uses.  
  
Click a device to see and edit its pins. Red = a problem (empty pin, the same pin used twice, or a pin on a second board that is switched off).  
Drag devices to arrange them, scroll to zoom, and Export image saves the diagram as a PNG - handy for documenting your printer or asking for help.  
  
Add device adds a motor, a feature or a section from the catalog.

### Review & upload

1. Checks: errors (red) must be fixed - click one to open its page. Warnings (yellow) are advice.  
2. Differences: exactly which lines change in your printer.cfg.  
3. Upload and restart: backup, upload, FIRMWARE_RESTART, wait for Klipper.  
  
Smart merge keeps your file and changes only what's needed. Clean new file rewrites it in a tidy order.

| Setting | What it does | In printer.cfg |
|---|---|---|
| **Smart merge - keeps your order, comments and macros** | Changes only the lines that really change. Your order, comments, macros and extra sections stay exactly as they are. Recommended for a printer that already works. |  |
| **Clean new file** | Writes a tidy new printer.cfg: sections grouped (board, motion, motors, heaters, probe, extras) with a short explanation above each. With 'Keep macros' your macros and other sections are added at the end. |  |

### All config files

All files of the printer. Click a file or a section in the tree, edit, then Save to printer. A backup is made first and only the matching service restarts (Klipper for .cfg, Moonraker for moonraker.conf...).

### Troubleshooter

Check printer now reads Klipper's state and the last klippy.log session. Or paste an error message. Each problem shows the cause, the fix, and a button to the page where you fix it.

## 5. Features and catalog

### Built-in features (switch on the Features page)

| Feature | What it does | Needs |
|---|---|---|
| 🎯 **Bed probe** | Probe the bed: bed mesh, Z homing with the probe, Z leveling. |  |
| ⚖️ **Multiple Z motors** | Second Z motor on its own driver, leveled automatically with z_tilt. | Bed probe |
| 🗺️ **Adaptive mesh** | Probes only under the printed parts at the start of each print. | Bed probe, Print macros, Cancel objects |
| 🧲 **Sensorless homing** | Home X and Y without endstop switches using StallGuard. |  |
| 🔁 **AWD (dual X/Y motors)** | A second motor on the X and Y axes. |  |
| 🎛️ **TMC Autotune** | Driver tuning for your exact motor model. Choose the motor per axis. | klipper_tmc_autotune |
| 〰️ **Input shaper** | Cancels ringing so you can print faster and cleaner. |  |
| ↩️ **Firmware retraction** | G10/G11 retraction you can tune during a print. |  |
| ⌒ **Arc moves** | Accept G2/G3 arcs from the slicer. |  |
| ✂️ **Cancel objects** | Cancel one failed part without stopping the print. |  |
| ▶️ **Print macros** | START_PRINT, END_PRINT and M600 filament change. |  |
| 🧵 **Filament runout sensor** | Pause when the filament runs out. |  |
| 💡 **LED strip** | NeoPixel / WS2812 strip on the board. |  |
| 🌈 **LED status effects** | The strip fills with temperature and print progress. | klipper-led_effect |
| 🌡️ **Raspberry Pi temperature** | Shown in Mainsail / Fluidd. |  |
| 🔥 **Board temperature** | Internal MCU temperature (STM32, RP2040, SAM). |  |
| ⏱️ **Idle timeout** | Turn motors and heaters off after 30 idle minutes. |  |
| ❄️ **Relaxed heater check** | For cold rooms or strong fans that trigger 'not heating at expected rate'. |  |

### Catalog - features you can add

| Feature | What it does | Adds |
|---|---|---|
| 🖥️ **Mainsail macros** | PAUSE / RESUME / CANCEL_PRINT macros shipped with Mainsail. (Mainsail) | `[include mainsail.cfg]` |
| 🖥️ **Fluidd macros** | PAUSE / RESUME / CANCEL_PRINT macros shipped with Fluidd. (Fluidd) | `[include fluidd.cfg]` |
| 🎞️ **Timelapse** | Layer-by-layer timelapse videos (moonraker-timelapse). (moonraker-timelapse) | `[include timelapse.cfg]` |
| 📊 **Shake&Tune** | Belt comparison and resonance graphs for input shaper tuning. (Klippain Shake&Tune) | `[shaketune]` |
| 📐 **ADXL345 on the Raspberry Pi** | Accelerometer wired to the Pi's SPI for SHAPER_CALIBRATE. Needs the Linux host MCU service. | `[mcu rpi]` `[adxl345]` `[resonance_tester]` |
| 📐 **ADXL345 on a Raspberry Pi Pico** | Accelerometer on a USB Pico. Put your Pico's serial path. | `[mcu adxl]` `[adxl345]` `[resonance_tester]` `[output_pin power_mode]` |
| 📐 **ADXL345 on the printer board** | Accelerometer on the board's SPI header. Fill cs_pin and spi_bus. | `[adxl345]` `[resonance_tester]` |
| 📏 **Skew correction** | Corrects a frame that isn't perfectly square (SET_SKEW). | `[skew_correction]` |
| 🌀 **Axis twist compensation** | Compensates a twisted X gantry for probes mounted off the nozzle. | `[axis_twist_compensation]` |
| 🔩 **Bed screws helper (probe)** | SCREWS_TILT_CALCULATE tells how much to turn each bed screw. | `[screws_tilt_adjust]` |
| 🔩 **Bed screws helper (paper test)** | BED_SCREWS_ADJUST moves to each screw for manual leveling. | `[bed_screws]` |
| 💾 **Save variables** | Macros can store values across restarts (SAVE_VARIABLE). | `[save_variables]` |
| 🛠️ **Force move** | Move a motor without homing (FORCE_MOVE, SET_KINEMATIC_POSITION). Use with care. | `[force_move]` |
| 🧵 **Filament motion sensor** | Detects jams and runout (BTT SFS and similar). Fill switch_pin. | `[filament_motion_sensor smart_sensor]` |
| 🌬️ **Electronics fan** | Runs while the motors are enabled. Fill the fan pin. | `[controller_fan electronics_fan]` |
| 🌬️ **Chamber exhaust fan** | Temperature-controlled fan for enclosures. Fill pin and sensor_pin. | `[temperature_fan chamber]` |
| 🌡️ **Chamber thermistor** | Shows the enclosure temperature. Fill sensor_pin. | `[temperature_sensor chamber]` |
| 💡 **Case light** | Dimmable light on a fan/heater output (SET_PIN PIN=caselight VALUE=1). | `[output_pin caselight]` |
| 🔔 **Beeper** | Buzzer for M300 style notifications. Fill the pin. | `[output_pin beeper]` |
| 🔘 **G-code button** | Run G-code when a physical button is pressed. | `[gcode_button my_button]` |
| 🦾 **Servo** | A hobby servo (SET_SERVO), e.g. for a nozzle wiper. | `[servo my_servo]` |
| 📝 **Custom section** | Write any Klipper section yourself. | `[my_section]` |

## 6. How the generated printer.cfg is organized

- **Smart merge** (recommended for a working printer) keeps your file: only values that really change are rewritten; comments, order, macros and unknown sections stay. New sections get a one-line explanation.
- **Clean new file** writes the sections grouped in this order, each group with a heading and each section with a short explanation: Controller board, Motion limits, Motors and drivers, Hotend/bed/fans, Probe/mesh/Z leveling, Lights, Extras, Print macros. Your other sections follow at the end.
- **SAVE_CONFIG** stays at the bottom. Values the app now writes (PID, probe offset, input shaper) are removed from it so the main file wins; bed meshes are kept.
- Macros written by the app contain `Klipper Studio` in their description. Remove that word to keep your own edits - the app never replaces a macro without it.

## 7. Safety and backups

- Nothing is sent to the printer until you press **Upload and restart** (or **Save to printer** on All config files).
- Upload is refused while the printer is printing or paused, and when printer.cfg changed on the printer after you loaded it (for example after SAVE_CONFIG). Load it again first.
- Before every upload a backup is saved on the printer in `studio_backups/` and on your computer in `~/.atgenx-studio/backups/`.
- After an upload that doesn't start Klipper, press **Restore last backup**.

## 8. FAQ

**Is my printer changed when I import?**  
No. Importing only reads files. Only Upload / Save to printer write, after a backup.

**My board isn't in the list.**  
Choose Custom, type the pins on the Pins page, and please open a board request on GitHub with the pinout.

**Moonraker refuses the connection.**  
Add your computer's network to `trusted_clients` in moonraker.conf, or enter an API key on the Connection page.

**Why did my SAVE_CONFIG values move into the main file?**  
Values in the main file are overridden by SAVE_CONFIG. Moving them keeps one source of truth, so what you set in the app really applies. The next SAVE_CONFIG works as usual.

**Does it support delta printers?**  
Not yet. Delta, polar and other machines are never rewritten - the app leaves those files untouched.
