# PsychoPy Plugin: Titta Eye Tracking

*A PsychoPy Builder plugin for Tobii eye trackers through Titta: calibration, recording, messages, gaze plotting and saving the data.*

Copyright (C) 2026 Bob Rosbag, Diederick C. Niehorster & Marcus Nyström

## About

This plugin makes [Titta](https://github.com/marcus-nystrom/Titta) available as Builder components in PsychoPy, for experiments with Tobii eye trackers. It is the PsychoPy counterpart of the OpenSesame plugin [opensesame-plugin-titta_eyetracking](https://github.com/dev-jam/opensesame-plugin-titta_eyetracking) (version 7.1.1): the same seven steps, the same settings and checks, all based on the functions of Titta's demo experiment `read_me.py`.

Titta is a toolbox for using eye trackers from Tobii Pro AB with Python, specifically offering integration with PsychoPy. A Matlab version that integrates with PsychToolbox is also available from https://github.com/dcnieho/Titta. For a similar toolbox for SMI eye trackers, please see https://github.com/marcus-nystrom/SMITE.

Cite as: Niehorster, D.C., Andersson, R. & Nystrom, M. (2020). Titta: A toolbox for creating PsychToolbox and Psychopy experiments with Tobii eye trackers. Behavior Research Methods. doi: [10.3758/s13428-020-01358-8](https://doi.org/10.3758/s13428-020-01358-8)

Please mention: Bob Rosbag as creator of this plugin

For questions, bug reports or to check for updates on Titta, please visit https://github.com/marcus-nystrom/Titta. For the plugin, please visit https://github.com/dev-jam/psychopy-titta-eyetracking.

To minimize the risk of missing samples, Titta uses TittaPy, a C++ wrapper around the Tobii SDK, to pull samples made available from the eye tracker. TittaPy is installed together with Titta.

Titta is an alternative to PsychoPy's own eye tracking components (ioHub, *Experiment settings > Eyetracking*). The two don't work together: with this plugin, leave the eye tracker in the experiment settings at *None* and use the Titta components only.


## Components

The components are in the Builder's component panel under **Titta Eye Tracking**.

| Component | What it does | When |
| --- | --- | --- |
| **Titta Init** | Connects to the eye tracker and sets it up: the eye tracker model, dummy mode, calibration settings and an optional operator screen. One per experiment, put it in the first Routine. | When the experiment starts (*Begin Experiment*, after the window opened) |
| **Titta Calibrate** | Shows Titta's participant setup, calibration and validation screens (bimonocular and on the operator screen when chosen in Titta Init). | Routine start or end |
| **Titta Start Recording** | Starts the recording of the chosen data (gaze, time sync, eye images, notifications, external signal, positioning). | Routine start or end |
| **Titta Send Message** | Sends a message to the recording, e.g. to mark the onset of a stimulus: the start message on the screen flip where the component starts, the optional stop message on the flip where it stops. | Like a stimulus: start and stop time |
| **Titta Plot Gaze** | Shows the gaze in real time while it runs, e.g. during a stimulus: on the stimulus screen (by default), and/or on the operator screen as a copy of the stimulus screen with the gaze on top (for the researcher). | Like a stimulus: start and stop time |
| **Titta Stop Recording** | Stops the recording. | Routine start or end |
| **Titta Save Data** | Saves the recording as an HDF5 file next to PsychoPy's data file, and can also export every table to tsv files and the eye images to png files. | Routine start or end |

*Routine start or end*: every component except Titta Init, Titta Send Message and Titta Plot Gaze has the setting **When**: *Routine start* (before the first frame of the Routine) or *Routine end* (after its last frame). These components have no duration and don't keep a Routine running: a Routine with only Titta components ends right away. Components with the same *When* act in the order of the Routine (top to bottom). When a Routine has a *Skip if* condition (Routine settings) and it is true, the Titta components in it do nothing.


## Requirements

- PsychoPy 2024.2 or newer (tested: 2024.2.4 with Python 3.10 and 2026.2.5 with Python 3.12). Only the PsychoPy (Python) target; the components are not available for PsychoJS/online experiments.
- Titta 2.2.2 or newer (installed with the plugin), with TittaPy (installed with Titta).
- A Tobii eye tracker supported by Titta, e.g. Tobii Pro Spectrum, Fusion, Nano, Spark, X3-120 (see Titta's README). Make sure it works in the [Tobii Pro Eye Tracker Manager](https://www.tobii.com/products/software/applications-and-developer-kits/tobii-pro-eye-tracker-manager) first. Without an eye tracker, use dummy mode.
- PsychoPy itself is not installed with the plugin (it is not declared as a dependency, so pip can't change the PsychoPy installation).


## Installation

The plugin is a Python package. Install it in the Python environment that runs PsychoPy, then restart PsychoPy. (Whether the Builder also shows the components without a restart is not tested.)

### Standalone PsychoPy (Windows, macOS, Linux)

1. In the Builder, open **Tools > Plugin/packages manager...** and go to the **Packages** tab.
2. Either
   - click **Install from file** and choose the wheel file (`psychopy_titta_eyetracking-<version>-py3-none-any.whl`), or
   - type in the pip console of that tab (PsychoPy adds `python -m pip` itself; the plugin is on [PyPI](https://pypi.org/project/psychopy-titta-eyetracking/)):

         install psychopy-titta-eyetracking --user

3. Restart PsychoPy.

Without the Builder, the same with the Python of the standalone PsychoPy, from a command prompt in the PsychoPy folder (where `python.exe` is), as Titta's README describes for Titta:

    python -m pip install psychopy-titta-eyetracking

or, for the wheel file:

    python -m pip install C:\path\to\psychopy_titta_eyetracking-<version>-py3-none-any.whl

### PsychoPy installed with pip

In the same (virtual) environment as PsychoPy:

    python -m pip install psychopy-titta-eyetracking

### From the source folder

    python -m pip install /path/to/psychopy-titta-eyetracking

To build the wheel yourself: `python -m pip wheel --no-deps /path/to/psychopy-titta-eyetracking` (or `poetry build`). For development, `python -m pip install -e /path/to/psychopy-titta-eyetracking`, or point **Install from file** at its `pyproject.toml`.

### Checking the installation

In the Coder shell, or a Python shell of the same environment:

    from psychopy import plugins
    plugins.activatePlugins()
    print(plugins.listPlugins('loaded'))   # contains 'psychopy-titta-eyetracking'

The **Titta Eye Tracking** category should be in the component panel of the Builder. If it isn't, check the Runner's or the Builder's output for a plugin error (e.g. TittaPy that can't be imported).

### Windows and Python 3.12

PsychoPy uses pyglet 1.4 on Windows, whose text fails with Python 3.12 and later (`ctypes.ArgumentError ... LP_c_ubyte`); Titta's calibration screens show text. Titta Init works around that bug when the experiment starts, as the OpenSesame plugin does.


## Use

### A typical experiment

    Routine "setup"        Titta Init (+ instructions)
    Routine "calibration"  Titta Calibrate
    Routine "welcome"      text + keyboard, Titta Start Recording (When: Routine end)
    Loop "trials"
        Routine "trial"    fixation + Titta Send Message ("fix_on" / "fix_off"),
                           image + Titta Send Message ($'onset_' + image_file / $'offset_' + image_file),
                           Titta Plot Gaze (same start as the image), keyboard
    Routine "end"          Titta Stop Recording, Titta Save Data, goodbye text

The demo experiment `demo/titta_demo.psyexp` is this experiment, the same as the demo of the OpenSesame plugin (pictures included). It starts in dummy mode; open it in the Builder and run it.

### Titta Init

- **Dummy mode**: *No* connects to the eye tracker; *Yes* runs without one (Titta's dummy mode: the calibration screen only shows "Calibration Dummy mode", no data is saved); *When piloting* uses dummy mode in pilot mode only (the pilot/run switch of the Builder).
- **Verbose mode**: print what the plugin does (in the Runner output).
- **Eye tracker**, **Eye tracker address** (empty: the first eye tracker of the model), **Manual sampling rate** with **Sampling rate (Hz)**, **Tracking mode** (*Default* keeps Titta's default for the model).
- Tab **Calibration**: bimonocular calibration (left eye, then right eye; Tobii Pro Spectrum only), the number of calibration targets (0, 1, 3, 5, 9 or 13), eye images during calibration, and, with **Manual calibration settings**, the dot type and size, animation, pacing interval (at least 0.8 s), auto pace and movement duration (0: the target jumps). With **Manual 3D location of the head box center**: x, y, z in mm.
- Tab **Operator screen**: a second window for the operator: monitor name (from the PsychoPy Monitor Center), screen number, resolution and waitBlanking. Titta shows its operator view there during calibration (not in dummy mode), and Titta Plot Gaze can plot the gaze there.
- Tab **Data**: **Data file name**, by default `thisExp.dataFileName`, so the eye tracking data is `data/<participant>_<experiment>_<date>.h5`, next to PsychoPy's `.csv` and `.log` files.

All settings are checked when the experiment starts, also in dummy mode (Titta itself checks some of them only with a real eye tracker); an invalid setting stops the experiment with an error that says what is allowed. Number and text settings can be `$` expressions, e.g. a sampling rate `$int(expInfo['rate'])`.

### Titta Send Message

The **Start message** is sent on the screen flip where the component starts, the **Stop message** (optional) on the flip where it stops. Without a stop time, the stop message is sent at the end of the Routine, and the component doesn't keep the Routine running. Messages are text; use `$` for code, e.g. `$'onset_' + image_file`. They are evaluated at the start of each Routine. Give the component the same start (and stop) as the stimulus it marks. The time stamp is the moment just after the flip, as in Titta's demo.

### Titta Plot Gaze

Shows the gaze in real time while the component runs, every frame: left eye red, right eye blue. Give it the same start (and stop) as the stimulus, and put it below the stimuli in the Routine; without a stop time it runs until the Routine ends (e.g. a key press of a Keyboard component), as Titta Plot Gaze ran instead of the keyboard response in the OpenSesame demo.

- **Plot gaze on stimulus display** (on by default: one screen): draws the gaze on the participant's screen, on top of all stimuli.
- **Plot gaze on operator display** (off by default; enable the operator screen in Titta Init, and switch off the stimulus display to keep the gaze from the participant): the operator screen shows a copy of the stimulus screen with the gaze on top, for the researcher. With a Tobii connected this is the real gaze, live.
- **Operator display background**: *Copy every frame* (live; each frame of the stimulus screen is read back from the graphics card, which takes time: check the frame timing of your experiment: PsychoPy warns about dropped frames in the log, `t of last frame was ...`), *Copy at start* (one copy, enough for a static stimulus such as a picture, and cheaper), or *None* (gaze on a background of the window colour). The copy is made at the end of each flip of the stimulus screen, so the operator screen is one frame behind.
- **Force disabling of waitBlanking for gaze plot on operator screen**: only matters when waitBlanking is on for the operator screen in Titta Init; the two screens are flipped one after the other, so waitBlanking on the operator screen can make the stimulus screen miss frames.
- **Simulate gaze in dummy mode**: in dummy mode, gaze that moves in a circle; without it nothing is drawn in dummy mode.

### Titta Save Data

Saves `<data file>.h5` (`<data file>_1.h5`, ... when that file exists). **Additionally export to tsv files** writes every table of the HDF5 file to `<data file>_<table>.tsv` (gaze, msg, time_sync, external_signal, notification, calibration_history, log, eye_metadata, as far as recorded). **Additionally export eye images to png files** writes `<data file>_eye_image/<k>.png` (image `<k>` belongs to row `<k>` of `<data file>_eye_metadata.tsv`; eye images are only in the file when they were recorded; an existing folder is never written into, the new folder then gets the date and time). A failed export is a warning in the log and doesn't end the experiment; the data stays in the `.h5` file. The path of the file (without extension) goes to the data file as `<name>.file`. In dummy mode no data is saved.

Read the data with pandas, as in Titta's `read_me.py`:

    import pandas as pd
    gaze = pd.read_hdf('data/001_titta_demo_2026-11-22_10h00.00.000.h5', 'gaze')
    messages = pd.read_hdf('data/001_titta_demo_2026-11-22_10h00.00.000.h5', 'msg')

### Code components

The Titta Init component makes a session object under its name (default `titta`); the Titta object is `titta.tracker`, so everything in Titta's API is available in a Code component, e.g. the newest gaze sample for a gaze-contingent display:

    sample = titta.tracker.buffer.peek_N('gaze', 1)
    x = sample['left_gaze_point_on_display_area_x']

and the methods of the session, which do the same as the components (with the same checks):

    titta.send_message('response_' + key_resp.keys)
    titta.start_recording(gaze=True, time_sync=True, eye_image=False, notifications=True,
                          external_signal=True, positioning=True,
                          block_until_data_available=True)
    titta.stop_recording()
    titta.save_data(tsv_export=True)

`titta.plot_gaze(...)` shows the gaze over the current screen until a key press (the way the OpenSesame item does it), for Coder scripts; it reads the screen from the front buffer, which some graphics drivers don't support (the background is then black).

Use the session methods rather than `titta.tracker.start_recording()`/`stop_recording()` directly: the session keeps track of whether Titta is recording (`titta.recording`), and the other components check that.

### Coder scripts

The same session works in a Coder script:

    from psychopy import visual
    from psychopy_titta_eyetracking import TittaSession

    win = visual.Window(fullscr=True, units='norm')
    titta = TittaSession(win, 'data/test', tracker='Tobii Pro Spectrum', dummy_mode=True)
    titta.connect()
    titta.calibrate()
    titta.start_recording()
    titta.send_message('fix on')
    ...
    titta.stop_recording()
    titta.save_data(tsv_export=True)
    titta.close()
    win.close()

The parameters of `TittaSession` and its methods are documented in `psychopy_titta_eyetracking/session.py`.

### Good to know

- **Escape in Titta's calibration screens** closes the windows and ends the experiment (Titta calls `core.quit()`); the eye tracking data is not saved then.
- **Escape elsewhere, or an error**: the experiment ends; when Titta was still recording, a warning in the log says that the eye tracking data was not saved (PsychoPy 2025.1.1 and later; with older versions there is no warning after Escape). The plugin doesn't save data on its own.
- **Block until recording has started** (Titta Start Recording, on by default) waits for the first gaze sample, at most 5 s; after that the experiment stops with an error (Titta itself would wait forever when the eye tracker sends no gaze).
- **Dummy mode**: Titta simulates gaze with the mouse in `titta.tracker.buffer` after a calibration, but only for window units norm, deg or pix (a warning for other units, e.g. the Builder's default *height*). The plugin stops that simulation at the end of the experiment, also after an error (otherwise the experiment never ends).
- One recording per experiment is tested. Several starts and stops within an experiment are possible (each start needs a stop first), and several saves too (each gets its own file), but they are not tested with an eye tracker.


## Differences with the OpenSesame plugin

The components do what the items of the OpenSesame plugin do, with these differences:

- Builder has no item order of its own: the components act at the start or the end of their Routine (*When*), Titta Send Message at its start and stop time on the screen flip, Titta Init when the experiment starts.
- Titta Send Message has an optional stop message (e.g. the offset of a stimulus).
- The data file is named after PsychoPy's data file (`<participant>_<experiment>_<date>.h5`) instead of `subject-<nr>.h5`.
- Titta Plot Gaze is timed like a stimulus and draws every frame of its Routine (real time during the stimulus), instead of waiting for a key itself; a Keyboard component in the same Routine ends it. On the operator screen it can copy the stimulus screen every frame (moving stimuli) or once. An eye without a valid gaze position is not drawn.
- Blocking start of the recording has a timeout of 5 s.
- Dummy mode can be on in pilot mode only.
- `IS4_Large_Peripheral` (Tobii 4C with Pro upgrade key) is in the list of eye trackers.


## Development

- `tools/build_demo.py` builds `demo/titta_demo.psyexp` with the Builder API; `tools/make_icons.py` makes the component icons.
- Tests (need PsychoPy, Titta and a display; on Linux without a screen use `xvfb-run`):

      python -m pytest tests
      python tests/run_experiment.py demo/titta_demo.psyexp --answer y

  `run_experiment.py` compiles an experiment and runs it with scripted key presses (e.g. in dummy mode).
- Not tested so far: a real Tobii eye tracker (connection, calibration screens, real gaze, eye images, notifications), an operator screen on a second monitor, the Builder GUI itself (only the code it generates), PsychoPy Studio, Windows and macOS.


## License

This plugin is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version (GPL-3.0-or-later).

The full license text is in the file `COPYING`, and is also available at <https://www.gnu.org/licenses/gpl-3.0.html>.

This plugin contains works of others: it is based on Titta (CC BY 4.0, Marcus Nyström and Diederick C. Niehorster) and the demo experiment uses the pictures of the demo of the OpenSesame plugin.
