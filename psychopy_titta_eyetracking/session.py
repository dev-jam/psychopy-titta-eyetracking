"""
This file is part of psychopy-titta-eyetracking.

Copyright (C) 2026 Bob Rosbag <mail@bobrosbag.nl>, Diederick C. Niehorster, Marcus Nyström

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

SPDX-License-Identifier: GPL-3.0-or-later

The run-time part of the plugin: one `TittaSession` per experiment, made
by the Titta Init component (or by a Coder script). The other components
call its methods through `get_session()`. The steps follow Titta's demo
`read_me.py` and the items of opensesame-plugin-titta_eyetracking 7.1.1.
"""

__author__ = "Bob Rosbag"
__license__ = "GPL-3.0-or-later"

import math
import os
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from psychopy import logging
from psychopy.constants import FINISHED, NOT_STARTED, STARTED

from .pyglet_text_fix import fix_pyglet_text

# Eye tracker names that Titta.get_defaults() knows
TRACKERS = (
    'Tobii Pro Spectrum',
    'Tobii Pro Fusion',
    'Tobii Pro X3-120 EPU',
    'Tobii Pro X3-120',
    'Tobii Pro Nano',
    'Tobii Pro Spark',
    'Tobii TX300',
    'Tobii T60 XL',
    'Tobii T60',
    'Tobii T120',
    'Tobii X60',
    'Tobii X120',
    'X2-60_Compact',
    'X2-30_Compact',
    'IS4_Large_Peripheral',
)

# 'Default' keeps the tracking mode of Titta's settings for the tracker
TRACKING_MODES = ('Default', 'human', 'animal')

# Streams that start_recording() and stop_recording() switch on and off
STREAMS = ('gaze', 'time_sync', 'eye_image', 'notifications',
           'external_signal', 'positioning')

AUTO_PACE = {
    'Space bar': 0,
    'Semi autoaccept': 1,
    'Autoaccept (default)': 2,
}

# Classes in titta.helpers_tobii
CALIBRATION_DOTS = {
    'Thaler (default)': 'MyDot2',
    'Black': 'MyDot3',
}

# Numbers of calibration targets that Titta accepts
N_CALIBRATION_TARGETS = (0, 1, 3, 5, 9, 13)
# Titta checks this only on a real eye tracker, not in dummy mode
MIN_PACING_INTERVAL = 0.8  # s

# Operator screen
OPERATOR_SCREEN_WIDTH = 52.7  # cm
OPERATOR_VIEWING_DISTANCE = 63  # distance from eye to center of screen (cm)

# Window units for which Titta's dummy mode can simulate gaze with the mouse
DUMMY_GAZE_UNITS = ('norm', 'deg', 'pix')

# Blocking start of a recording: Titta itself waits without a timeout
BLOCK_TIMEOUT = 5.0  # s
BLOCK_POLL_INTERVAL = 0.001  # s

# Gaze plot
DOT_RADIUS = 0.02  # norm units
# Simulated gaze in dummy mode: both eyes move in a circle (norm units)
SIMULATION_RADIUS = 0.05
SIMULATION_LEFT_X = -0.02
SIMULATION_RIGHT_X = 0.12
SIMULATION_STEPS = 60  # samples per circle
POLL_INTERVAL = 0.001  # s, between keyboard checks when nothing is drawn
# autoDraw depths (more negative is drawn later, on top): the copy of the
# stimulus display for the operator is made after all stimuli, then the
# gaze dots are drawn
CAPTURE_DEPTH = -1e9
GAZE_DEPTH = -2e9
# What the operator display shows under the gaze (Titta Plot Gaze component)
OPERATOR_BACKGROUNDS = ('Copy every frame', 'Copy at start', 'None')

# Data that Titta always saves, or saves with the external signal stream;
# a warning when one of them is missing. All pandas tables in the HDF5
# file are exported, also the ones not listed here (e.g. time_sync,
# notification, eye_metadata, log)
TSV_EXPECTED = ('gaze', 'msg', 'external_signal', 'calibration_history')
# Group in the HDF5 file with one dataset per eye image (Titta writes it
# with h5py; dataset <k> belongs to row <k> of eye_metadata)
EYE_IMAGE_GROUP = 'eye_image'

# The session of the running experiment (one at a time)
_current_session = None


class TittaError(Exception):
    """An error the user can fix: a wrong setting, a missing component, or
    an error that Titta reported (with Titta's message).
    """


def get_session():
    """Returns the running `TittaSession`, made by the Titta Init component.

    Raises
    ------
    TittaError
        When there is no session.
    """
    if _current_session is None:
        raise TittaError('There is no Titta session: put a Titta Init component in the '
                         'first Routine of the experiment')
    return _current_session


class TittaSession:
    """Connects to a Tobii eye tracker through Titta, and calibrates, records,
    plots gaze and saves the data. All settings are checked when the session
    is made, also in dummy mode; Titta only checks some of them on a real
    eye tracker.

    Parameters
    ----------
    win : psychopy.visual.Window
        The window of the experiment (the stimulus display).
    data_file_name : str
        Path of the data file without extension (in Builder:
        `thisExp.dataFileName`). Titta writes `<data_file_name>.h5`, or
        `<data_file_name>_1.h5`, ... when that file exists.
    tracker : str
        Eye tracker model, one of `TRACKERS`.
    dummy_mode : bool
        Use Titta's dummy mode (no eye tracker; no data is saved).
    verbose : bool
        Print what the session does.
    tracker_address : str
        Address of the eye tracker; empty: the first one of the model.
    sampling_rate : int or None
        Sampling rate in Hz; None: Titta's default for the model.
    tracking_mode : str
        One of `TRACKING_MODES`; 'Default' keeps Titta's default.
    bimonocular_calibration : bool
        Calibrate the left and the right eye one after the other.
    n_calibration_targets : int
        One of `N_CALIBRATION_TARGETS`.
    record_eye_images_during_calibration : bool
    calibration_dot : str or None
        One of `CALIBRATION_DOTS`. This and the following five settings are
        Titta's defaults when None.
    calibration_dot_size : int or float or None
        Outer diameter of the calibration dot in pixels.
    calibration_animate : bool or None
    calibration_pacing_interval : int or float or None
        In seconds, at least `MIN_PACING_INTERVAL`.
    calibration_auto_pace : str or None
        One of `AUTO_PACE`.
    calibration_movement_duration : int or float or None
        In seconds, 0 or more (0: the target jumps).
    head_box_center : sequence of three numbers or None
        Position of the head box center (x, y, z in mm, user coordinate
        system); None: Titta's default.
    operator_screen : bool
        Open a window for the operator.
    operator_screen_name : str
        Monitor of the operator window in the PsychoPy Monitor Center.
    operator_screen_nr : int
        Screen number of the operator window.
    operator_resolution : sequence of two ints
        Size of the operator window in pixels.
    operator_waitblanking : bool
        waitBlanking of the operator window.
    """

    def __init__(self, win, data_file_name, tracker='Tobii Pro Spectrum',
                 dummy_mode=False, verbose=False, tracker_address='',
                 sampling_rate=None, tracking_mode='Default',
                 bimonocular_calibration=False, n_calibration_targets=5,
                 record_eye_images_during_calibration=False,
                 calibration_dot=None, calibration_dot_size=None,
                 calibration_animate=None, calibration_pacing_interval=None,
                 calibration_auto_pace=None,
                 calibration_movement_duration=None, head_box_center=None,
                 operator_screen=False, operator_screen_name='default',
                 operator_screen_nr=1, operator_resolution=(1920, 1080),
                 operator_waitblanking=False):
        global _current_session
        if _current_session is not None:
            raise TittaError('There can be only one Titta session (one Titta Init component) '
                             'in an experiment')
        self.win = win
        self.data_file_name = os.fspath(data_file_name)
        self.dummy_mode = _bool(dummy_mode, 'Dummy mode')
        self.verbose = _bool(verbose, 'Verbose mode')
        self.bimonocular_calibration = _bool(
            bimonocular_calibration, 'Bimonocular calibration')
        self.operator_screen = _bool(operator_screen, 'Operator screen')
        self.operator_screen_name = str(operator_screen_name)
        self.operator_waitblanking = _bool(
            operator_waitblanking, 'waitBlanking on the operator screen')
        if self.operator_screen:
            self.operator_screen_nr = _number(
                operator_screen_nr, 'Operator screen number', int, allow_zero=True)
            self.operator_resolution = _resolution(operator_resolution)
        if fix_pyglet_text():
            self._show_message('Applied the pyglet 1.x text fix for Python 3.12 and later')
        self.settings = self._make_settings(
            tracker=tracker,
            tracker_address=tracker_address,
            sampling_rate=sampling_rate,
            tracking_mode=tracking_mode,
            n_calibration_targets=n_calibration_targets,
            record_eye_images_during_calibration=record_eye_images_during_calibration,
            calibration_dot=calibration_dot,
            calibration_dot_size=calibration_dot_size,
            calibration_animate=calibration_animate,
            calibration_pacing_interval=calibration_pacing_interval,
            calibration_auto_pace=calibration_auto_pace,
            calibration_movement_duration=calibration_movement_duration,
            head_box_center=head_box_center,
        )
        # Shared state, also for Code components
        self.tracker = None  # the Titta object, after connect()
        self.operator_window = None
        self.recording = None  # None: not started yet; then True or False
        self.file_name = None  # the last data file, without extension
        self._closed = False
        _current_session = self

    # --- Public methods ---------------------------------------------------

    def connect(self):
        """Opens the operator window (when asked for), connects to the eye
        tracker and applies the settings.
        """
        from titta import Titta

        self._set_data_file()
        if self.operator_screen:
            self._open_operator_window()
        self._show_message('Initialising Eye Tracker')
        with self._titta_errors('initialise the eye tracker'):
            self.tracker = Titta.Connect(self.settings)
            if self.dummy_mode:
                self._show_message('Dummy mode activated')
                self.tracker.set_dummy_mode()
                self._stop_dummy_buffer_at_exit()
                self._check_dummy_units()
            self.tracker.init()

    def calibrate(self):
        """Shows Titta's participant setup, calibration and validation
        screens. Escape in these screens ends the experiment (Titta calls
        `core.quit()`); the data is not saved then.
        """
        self._check_connected()
        self._show_message('Starting calibration')
        # Titta's dummy mode has no operator screen
        kwargs = {'win_operator': self.operator_window} \
            if self.operator_screen and not self.dummy_mode else {}
        if self.bimonocular_calibration:
            self._calibrate(eye='left', calibration_number='first', **kwargs)
            self._calibrate(eye='right', calibration_number='second', **kwargs)
        else:
            self._calibrate(**kwargs)

    def start_recording(self, gaze=True, time_sync=True, eye_image=False,
                        notifications=True, external_signal=True,
                        positioning=True, block_until_data_available=True):
        """Starts the recording of the chosen streams. With
        `block_until_data_available`, waits until the first gaze sample
        arrives, at most `BLOCK_TIMEOUT` seconds (an error after that).
        """
        self._check_connected()
        if self.recording:
            raise TittaError('Titta is still recording, you first have to stop recording '
                             'before starting')
        streams = _streams(locals())
        block = _bool(block_until_data_available, 'Block until recording has started')
        with self._titta_errors('start recording'):
            if self.dummy_mode or not block:
                self.tracker.start_recording(
                    **streams, block_until_data_available=block)
            else:
                t0 = self.tracker.get_system_time_stamp()
                self.tracker.start_recording(**streams)
        self.recording = True
        if block and not self.dummy_mode:
            self._wait_for_gaze(t0)

    def stop_recording(self, gaze=True, time_sync=True, eye_image=False,
                       notifications=True, external_signal=True,
                       positioning=True):
        """Stops the recording of the chosen streams."""
        self._check_connected()
        if not self.recording:
            raise TittaError('Titta is not recording, you first have to start recording '
                             'before stopping')
        streams = _streams(locals())
        with self._titta_errors('stop recording'):
            self.tracker.stop_recording(**streams)
        self.recording = False

    def send_message(self, message, ts=None):
        """Stores a message with a time stamp (now, or `ts`, Tobii system
        time in microseconds) in the data. The message is sent as text.
        """
        self._check_connected()
        with self._titta_errors('send the message'):
            self.tracker.send_message(str(message), ts)

    def plot_gaze(self, stimulus_display=False, operator_display=False,
                  simulate_gaze=False, disable_waitblanking=False,
                  response_keys=None, timeout=None, escape_key=True):
        """Shows the gaze position on the current display, until a response
        key is pressed or the timeout has passed.

        Parameters
        ----------
        stimulus_display, operator_display : bool
            Where to draw the gaze (the operator display needs the operator
            screen).
        simulate_gaze : bool
            In dummy mode, draw gaze moving in a circle.
        disable_waitblanking : bool
            Switch waitBlanking off on the operator screen while plotting.
        response_keys : str, sequence of str or None
            Keys that end the plot; None or empty: any key.
        timeout : int, float or None
            In seconds; None: no timeout.
        escape_key : bool
            Escape also ends the plot (returned as 'escape').

        Returns
        -------
        tuple
            The key (None after the timeout) and the response time in s.
        """
        from psychopy import visual
        from psychopy.hardware import keyboard

        self._check_connected()
        stimulus_display = _bool(stimulus_display, 'Plot gaze on stimulus display')
        operator_display = _bool(operator_display, 'Plot gaze on operator display')
        if operator_display and not self.operator_screen:
            raise TittaError('Plot gaze on operator display selected, but the operator screen '
                             'is not enabled in the Titta Init component')
        simulate_gaze = _bool(simulate_gaze, 'Simulate gaze in dummy mode')
        # Only needed when waitBlanking is enabled on the operator screen
        disable_waitblanking = operator_display and self.operator_waitblanking \
            and _bool(disable_waitblanking, 'Disable waitBlanking')
        key_list = _key_list(response_keys)
        if key_list is not None and _bool(escape_key, 'Escape key') \
                and 'escape' not in key_list:
            key_list.append('escape')
        if timeout is not None:
            timeout = _number(timeout, 'Timeout')
        self._show_message(f'Response key(s) set to {key_list}')

        # The current stimulus display is the background of the gaze plot
        # (_getFrame() is private PsychoPy API)
        background = self.win._getFrame()
        aspect_ratio = self.win.size[0] / self.win.size[1]
        displays = []
        if stimulus_display:
            displays.append(self.win)
        if operator_display:
            displays.append(self.operator_window)
        plots = [
            (visual.ImageStim(window, image=background, units='norm', size=(2, 2)),
             visual.Circle(window, radius=(DOT_RADIUS, aspect_ratio * DOT_RADIUS),
                           units='norm', opacity=0.5))
            for window in displays
        ]
        plot = bool(plots) and (not self.dummy_mode or simulate_gaze)

        kb = keyboard.Keyboard()
        kb.clearEvents()
        if disable_waitblanking:
            self.operator_window.waitBlanking = False
        try:
            step = 1
            key = None
            rt = None
            kb.clock.reset()
            while key is None:
                if timeout is not None and kb.clock.getTime() >= timeout:
                    rt = kb.clock.getTime()
                    break
                if plot:
                    gaze = self._gaze(step)
                    step += 1
                    for image, dot in plots:
                        _draw_gaze(image, dot, gaze)
                    # The operator display first, as in the OpenSesame plugin
                    for window in reversed(displays):
                        window.flip()
                keys = kb.getKeys(keyList=key_list, waitRelease=False)
                if keys:
                    key, rt = keys[0].name, keys[0].rt
                elif not plot:
                    # Nothing to draw (flip() would pace the loop)
                    time.sleep(POLL_INTERVAL)
        finally:
            if disable_waitblanking:
                self.operator_window.waitBlanking = True
        self._show_message(f"Detected press on button: '{key}'")
        self._show_message(f'Response time: {round(rt * 1000, 1)} ms')
        return key, rt

    def save_data(self, tsv_export=False, png_export=False):
        """Saves the recording as `<data file>.h5` (`<data file>_1.h5`, ...
        when that file exists), and optionally exports every table to
        `<file>_<table>.tsv` and the eye images to
        `<file>_eye_image/<k>.png`. A failed export is a warning and doesn't
        raise. In dummy mode Titta saves nothing.

        Returns
        -------
        str or None
            The path of the data file without extension, None in dummy mode.
        """
        self._check_connected()
        if self.recording:
            raise TittaError('Titta is still recording, you first have to stop recording '
                             'before saving data')
        tsv_export = _bool(tsv_export, 'tsv export')
        png_export = _bool(png_export, 'png export')
        file_name = self._free_file_name()
        with self._titta_errors('save the data'):
            self.tracker.save_data(filename=os.path.basename(file_name))
        if self.dummy_mode:
            return None
        self.file_name = file_name
        self._show_message(f'Data saved to {file_name}.h5')
        if tsv_export:
            self._export('tsv', self._export_tsv, file_name)
        if png_export:
            self._export('png', self._export_eye_images, file_name)
        return file_name

    def close(self):
        """Ends the session: warns when Titta is still recording (the data
        was not saved), stops the gaze simulation of dummy mode and closes
        the operator window. The Titta Init component runs it when the
        experiment ends, also after Escape.
        """
        global _current_session
        if self._closed:
            return
        self._closed = True
        if _current_session is self:
            _current_session = None
        if self.recording:
            logging.warning('Titta was still recording at the end of the experiment: '
                            'the eye tracking data was not saved')
        self._stop_dummy_buffer()
        if self.operator_window is not None:
            self.operator_window.close()
            self.operator_window = None

    # --- Settings -----------------------------------------------------------

    def _make_settings(self, tracker, tracker_address, sampling_rate,
                       tracking_mode, n_calibration_targets,
                       record_eye_images_during_calibration, calibration_dot,
                       calibration_dot_size, calibration_animate,
                       calibration_pacing_interval, calibration_auto_pace,
                       calibration_movement_duration, head_box_center):
        try:
            from titta import Titta, helpers_tobii
        except Exception as e:
            raise TittaError(f'Could not import titta: {e}') from e

        tracker = _choice(tracker, TRACKERS, 'Eye tracker')
        # Default settings for the selected tracker
        with self._titta_errors(f'find the settings of {tracker}'):
            settings = Titta.get_defaults(tracker)
        settings.N_CAL_TARGETS = _choice(
            n_calibration_targets, N_CALIBRATION_TARGETS, 'Number of calibration targets')
        if not isinstance(tracker_address, str):
            raise TittaError('Eye tracker address needs to be text')
        if tracker_address.strip():
            settings.TRACKER_ADDRESS = tracker_address

        if sampling_rate is not None:
            settings.SAMPLING_RATE = _number(sampling_rate, 'Sampling rate', int)
            self._show_message(f'Using manual sampling rate: {settings.SAMPLING_RATE}')
        else:
            self._show_message(f'Using default sampling rate: {settings.SAMPLING_RATE}')

        if _choice(tracking_mode, TRACKING_MODES, 'Tracking mode') != 'Default':
            settings.TRACKING_MODE = tracking_mode
            self._show_message(f'Using tracking mode: {settings.TRACKING_MODE}')

        settings.RECORD_EYE_IMAGES_DURING_CALIBRATION = _bool(
            record_eye_images_during_calibration, 'Record eye images during calibration')

        if head_box_center is not None:
            center = list(head_box_center) \
                if isinstance(head_box_center, (list, tuple)) else None
            if center is None or len(center) != 3 or not all(_is_number(v) for v in center):
                raise TittaError('Head box center coordinates must be numbers and have values '
                                 'for three dimensions')
            settings.HEAD_BOX_CENTER = center
            self._show_message(f'Using head box center: {settings.HEAD_BOX_CENTER}')

        graphics = settings.graphics
        if calibration_dot is not None or calibration_dot_size is not None:
            if calibration_dot_size is not None:
                graphics.TARGET_SIZE = _number(calibration_dot_size, 'Calibration dot size')
                graphics.TARGET_SIZE_INNER = graphics.TARGET_SIZE / 6
            dot = _choice(calibration_dot or 'Thaler (default)', CALIBRATION_DOTS,
                          'Calibration dot type')
            settings.CAL_TARGET = getattr(helpers_tobii, CALIBRATION_DOTS[dot])(
                units='pix',
                outer_diameter=graphics.TARGET_SIZE,
                inner_diameter=graphics.TARGET_SIZE_INNER
            )
        if calibration_pacing_interval is not None:
            settings.PACING_INTERVAL = _number(
                calibration_pacing_interval, 'Pacing interval')
            if settings.PACING_INTERVAL < MIN_PACING_INTERVAL:
                raise TittaError(f'Pacing interval needs to be at least {MIN_PACING_INTERVAL} s')
        if calibration_movement_duration is not None:
            # 0 is valid: the target jumps to the next position
            settings.MOVE_TARGET_DURATION = _number(
                calibration_movement_duration, 'Movement duration', allow_zero=True)
        if calibration_animate is not None:
            settings.ANIMATE_CALIBRATION = _bool(calibration_animate, 'Animate calibration')
        if calibration_auto_pace is not None:
            settings.AUTO_PACE = AUTO_PACE[_choice(
                calibration_auto_pace, AUTO_PACE, 'Calibration auto pace')]
        return settings

    def _set_data_file(self):
        folder, name = os.path.split(self.data_file_name)
        if not name:
            raise TittaError(f'The data file name has no file part: {self.data_file_name}')
        if folder:
            # PsychoPy normally made the folder already
            os.makedirs(folder, exist_ok=True)
        self.settings.FILENAME = name
        self.settings.DATA_STORAGE_PATH = folder
        self._show_message(f'Data will be stored in: {os.path.normpath(self.data_file_name)}')

    def _open_operator_window(self):
        from psychopy import monitors, visual

        resolution = list(self.operator_resolution)
        # The monitor needs to exist in the PsychoPy Monitor Center
        monitor = monitors.Monitor(self.operator_screen_name)
        monitor.setWidth(OPERATOR_SCREEN_WIDTH)
        monitor.setDistance(OPERATOR_VIEWING_DISTANCE)
        monitor.setSizePix(resolution)
        self.operator_window = visual.Window(
            monitor=monitor,
            fullscr=False,
            screen=self.operator_screen_nr,
            size=resolution,
            units='norm',
            waitBlanking=self.operator_waitblanking
        )

    def _check_dummy_units(self):
        if self.win.units not in DUMMY_GAZE_UNITS:
            logging.warning(f"Titta's dummy mode simulates gaze with the mouse only for window "
                            f"units {', '.join(DUMMY_GAZE_UNITS)}, not '{self.win.units}': "
                            f"tracker.buffer has no gaze then")

    # --- Helpers --------------------------------------------------------------

    def _calibrate(self, **kwargs):
        if self.dummy_mode:
            # Each calibration starts a new thread that simulates gaze
            self._stop_dummy_buffer()
        with self._titta_errors('calibrate'):
            self.tracker.calibrate(self.win, **kwargs)

    def _wait_for_gaze(self, t0):
        # As Titta's block_until_data_available, but with a timeout: Titta
        # waits forever when the eye tracker sends no gaze
        deadline = time.monotonic() + BLOCK_TIMEOUT
        while True:
            with self._titta_errors('read the gaze buffer'):
                ts = self.tracker.buffer.peek_N('gaze', 1)['system_time_stamp']
            if len(ts) > 0 and ts[0] > t0:
                return
            if time.monotonic() > deadline:
                raise TittaError(f'No gaze data from the eye tracker within {BLOCK_TIMEOUT} s '
                                 f'after the start of the recording (is the gaze stream '
                                 f'started?)')
            time.sleep(BLOCK_POLL_INTERVAL)

    def _gaze(self, step):
        """Returns the left and right gaze position in norm units (None for
        an eye without a valid position), or None when the buffer has no
        sample yet.
        """
        if not self.dummy_mode:
            sample = self.tracker.buffer.peek_N('gaze', 1)
            if len(sample['system_time_stamp']) == 0:
                return None
            gaze = []
            for eye in ('left', 'right'):
                x = sample[f'{eye}_gaze_point_on_display_area_x'][0]
                y = sample[f'{eye}_gaze_point_on_display_area_y'][0]
                gaze.append(None if math.isnan(x) or math.isnan(y)
                            else (x * 2 - 1, 1 - y * 2))
            return tuple(gaze)
        angle = 2 * math.pi * step / SIMULATION_STEPS
        dx = SIMULATION_RADIUS * math.cos(angle)
        dy = SIMULATION_RADIUS * math.sin(angle)
        return (SIMULATION_LEFT_X + dx, dy), (SIMULATION_RIGHT_X + dx, dy)

    def _check_connected(self):
        if self._closed:
            raise TittaError('The Titta session has ended')
        if self.tracker is None:
            raise TittaError('Titta is not connected to the eye tracker yet')

    def _stop_dummy_buffer(self):
        # In dummy mode, Titta's calibrate() starts a thread that simulates
        # gaze with the mouse and never stops it; a running thread keeps the
        # experiment from ending. _stop_sample_buffer() is private Titta API.
        buffer = getattr(self.tracker, 'buffer', None)
        if self.dummy_mode and buffer is not None:
            buffer._stop_sample_buffer()

    def _stop_dummy_buffer_at_exit(self):
        # Also when the experiment ends with an error (close() doesn't run
        # then): Python waits for the simulation thread before it exits. The
        # main thread counts as ended before Python waits for other threads.
        def stop():
            threading.main_thread().join()
            self._stop_dummy_buffer()
        threading.Thread(target=stop, name='titta-dummy-buffer-stop',
                         daemon=True).start()

    def _free_file_name(self):
        # Titta adds _1, _2, ... to the file name when a .h5 file with that
        # name (the part before the first dot) exists; choose the free name
        # here, to export the data from the right file. PsychoPy's data file
        # names have dots (in the time), so also check the whole name
        folder, base = os.path.split(self.data_file_name)
        files = list(Path(folder or '.').glob('*.h5'))
        taken = {path.name.split('.')[0] for path in files} | \
                {path.name[:-len('.h5')] for path in files}
        name = base
        i = 1
        while name in taken:
            name = f'{base}_{i}'
            i += 1
        return os.path.join(folder, name)

    def _export(self, kind, export, file_name):
        # An export must never end the experiment: Titta has already written
        # the .h5 file. A failure is a warning in the log instead
        try:
            export(file_name)
        except Exception as e:
            logging.warning(f'{kind} export of {file_name}.h5 failed, '
                            f'the experiment continues: {e!r}')

    def _export_tsv(self, file_name):
        import pandas as pd

        with pd.HDFStore(f'{file_name}.h5', 'r') as store:
            keys = [key.lstrip('/') for key in store.keys()]
            for key in TSV_EXPECTED:
                if key not in keys:
                    logging.warning(f"'{key}' not found in HDF5 file")
            for key in keys:
                # One table that fails doesn't stop the export of the others
                output_file = f'{file_name}_{key.replace("/", "_")}.tsv'
                try:
                    pd.read_hdf(store, key).to_csv(output_file, sep='\t')
                except Exception as e:
                    logging.warning(f"tsv export of '{key}' to {output_file} failed: {e!r}")
                    continue
                self._show_message(f'Saved {key} to {output_file}')

    def _export_eye_images(self, file_name):
        import h5py
        from PIL import Image

        # Each eye image becomes <file_name>_eye_image/<k>.png
        with h5py.File(f'{file_name}.h5', 'r') as hf:
            if EYE_IMAGE_GROUP not in hf:
                # Eye images are only recorded when asked for: not an error
                self._show_message('No eye images in the HDF5 file, no png export')
                return
            group = hf[EYE_IMAGE_GROUP]
            folder = _free_folder_name(f'{file_name}_{EYE_IMAGE_GROUP}')
            os.makedirs(folder)
            saved = 0
            failed = []
            for name, dataset in group.items():
                # One image that fails doesn't stop the export of the others;
                # one warning for all failures
                output_file = os.path.join(folder, f'{name}.png')
                try:
                    Image.fromarray(dataset[()]).save(output_file)
                except Exception as e:
                    failed.append((name, e))
                    continue
                saved += 1
            if failed:
                name, e = failed[0]
                logging.warning(f'png export: {len(failed)} of {len(group)} eye images '
                                f'failed, the first ({name}): {e!r}')
            self._show_message(f'Saved {saved} eye images to {folder}')

    @contextmanager
    def _titta_errors(self, action):
        # Titta raises plain exceptions (e.g. eye tracker not found, with the
        # list of the trackers it found); show its message in one line
        try:
            yield
        except TittaError:
            raise
        except Exception as e:
            message = ' '.join(str(e).split()) or type(e).__name__
            raise TittaError(f'Titta could not {action}: {message}') from e

    def _show_message(self, message):
        logging.debug(f'Titta: {message}')
        if self.verbose:
            print(message)


class TittaGazePlot:
    """The object of a Titta Plot Gaze component in a Routine: while it runs,
    it shows the gaze in real time, every frame, on the stimulus display
    (dots on top of the stimuli) and/or on the operator display (a copy of
    the stimulus display with the gaze on top).

    Parameters
    ----------
    name : str
        Name of the component.
    win : psychopy.visual.Window
        The stimulus display.
    stimulus_display, operator_display, simulate_gaze, disable_waitblanking : bool
        As in `TittaSession.plot_gaze()`.
    operator_background : str
        One of `OPERATOR_BACKGROUNDS`: what the operator display shows under
        the gaze.
    """

    def __init__(self, name, win, stimulus_display=True, operator_display=False,
                 simulate_gaze=False, disable_waitblanking=False,
                 operator_background='Copy every frame'):
        self.name = name
        self.win = win
        self.settings = dict(stimulus_display=stimulus_display,
                             operator_display=operator_display,
                             simulate_gaze=simulate_gaze,
                             disable_waitblanking=disable_waitblanking,
                             operator_background=operator_background)
        self.status = NOT_STARTED
        self.tStart = self.tStop = self.tStartRefresh = self.tStopRefresh = None
        self.frameNStart = self.frameNStop = None
        self._stimulus_dots = []
        self._operator = None  # (window, background image, dots)
        self._step = 0
        self._captured = False
        self._waitblanking_off = False
        self._running = False
        self._capture = None
        self._frame = None

    def start(self):
        """Checks the settings and prepares the drawing (when the component
        starts).
        """
        from psychopy import visual

        session = get_session()
        session._check_connected()
        settings = self.settings
        self.stimulus_display = _bool(settings['stimulus_display'],
                                      'Plot gaze on stimulus display')
        self.operator_display = _bool(settings['operator_display'],
                                      'Plot gaze on operator display')
        if self.operator_display and not session.operator_screen:
            raise TittaError('Plot gaze on operator display selected, but the operator screen '
                             'is not enabled in the Titta Init component')
        self.simulate_gaze = _bool(settings['simulate_gaze'], 'Simulate gaze in dummy mode')
        self.operator_background = _choice(settings['operator_background'],
                                           OPERATOR_BACKGROUNDS, 'Operator display background')
        self.session = session
        self._step = 0
        self._captured = False
        if not self._stimulus_dots and self.stimulus_display:
            self._stimulus_dots = _gaze_dots(self.win, self.win)
        if self._operator is None and self.operator_display:
            window = session.operator_window
            background = visual.ImageStim(window, image=None, units='norm', size=(2, 2))
            self._operator = (window, background, _gaze_dots(window, self.win))
        self._frame = None
        if self.operator_display and self.operator_background != 'None':
            if self._capture is None:
                self._capture = _FrameCapture(self.win, self._store_frame)
            self._capture.autoDraw = True
        # Only needed when waitBlanking is enabled on the operator screen
        self._waitblanking_off = self.operator_display and session.operator_waitblanking \
            and _bool(settings['disable_waitblanking'], 'Disable waitBlanking')
        if self._waitblanking_off:
            self._operator[0].waitBlanking = False
        self._running = True
        self.status = STARTED

    def update(self):
        """Draws the newest gaze sample (every frame while the component
        runs).
        """
        if not self._running:
            return
        session = self.session
        if session.dummy_mode and not self.simulate_gaze:
            gaze = None
        else:
            self._step += 1
            with session._titta_errors('read the gaze buffer'):
                gaze = session._gaze(self._step)
        for dot, pos in zip(self._stimulus_dots, gaze or (None, None)):
            # depth: on top of all stimuli, drawn by the flip of the Routine
            dot.autoDraw = pos is not None
            if pos is not None:
                dot.pos = pos
        if self._operator is not None:
            self._update_operator(gaze)

    def stop(self):
        """Stops drawing (when the component stops or the Routine ends)."""
        # PsychoPy's stop test sets the status before this call
        if not self._running:
            return
        self._running = False
        for dot in self._stimulus_dots:
            dot.autoDraw = False
        if self._capture is not None:
            self._capture.autoDraw = False
        if self._waitblanking_off:
            self._operator[0].waitBlanking = True
        self.status = FINISHED

    def _store_frame(self, image):
        # Called by the flip of the stimulus display, with the frame it shows
        self._frame = image
        if self.operator_background == 'Copy at start':
            self._capture.autoDraw = False

    def _update_operator(self, gaze):
        window, background, dots = self._operator
        if self._frame is not None:
            # The frame of the previous flip of the stimulus display
            background.image = self._frame
            self._frame = None
            self._captured = True
        if self._captured:
            background.draw()
        for dot, pos in zip(dots, gaze or (None, None)):
            if pos is not None:
                dot.pos = pos
                dot.draw()
        window.flip()
        # Drawing of the Routine goes on in the stimulus display
        self.win._setCurrent()


def _FrameCapture(win, callback):
    """An invisible autoDraw stimulus, drawn after all stimuli in the flip of
    the stimulus display: it reads the frame from the back buffer and passes
    it to `callback` (the front buffer can't be read reliably after the
    flip, and the flip clears the back buffer before callOnFlip functions
    run). Made here: psychopy.visual loads OpenGL.
    """
    from psychopy.visual.basevisual import MinimalStim

    class FrameCapture(MinimalStim):
        def __init__(self):
            self.win = win
            self.depth = CAPTURE_DEPTH
            super().__init__(name='titta_frame_capture', autoLog=False)

        def draw(self, win=None):
            # _getFrame() is private PsychoPy API
            callback(self.win._getFrame(buffer='back'))

    return FrameCapture()


def _gaze_dots(window, stimulus_window):
    """A red (left eye) and a blue (right eye) dot, round on the stimulus
    display (norm units), drawn on top of everything.
    """
    from psychopy import visual

    aspect_ratio = stimulus_window.size[0] / stimulus_window.size[1]
    return [visual.Circle(window, radius=(DOT_RADIUS, aspect_ratio * DOT_RADIUS),
                          units='norm', opacity=0.5, lineColor=color, fillColor=color,
                          depth=GAZE_DEPTH, autoLog=False)
            for color in ('red', 'blue')]


class TittaMessage:
    """The object of a Titta Send Message component in a Routine: sends its
    start message on the flip where the component starts, and its stop
    message on the flip where it stops (or at the end of the Routine).
    """

    def __init__(self, name, start_message='', stop_message=''):
        self.name = name
        self.start_message = start_message
        self.stop_message = stop_message
        # True from the start until the stop message is on its way
        self.stop_pending = False
        self.status = NOT_STARTED
        self.tStart = self.tStop = self.tStartRefresh = self.tStopRefresh = None
        self.frameNStart = self.frameNStop = None

    def on_start(self, win):
        """The component starts: send the start message on the next flip."""
        get_session()  # an error now, not in the flip
        self.stop_pending = True
        win.callOnFlip(self.send_start)

    def on_stop(self, win):
        """The component stops: send the stop message on the next flip."""
        self.stop_pending = False
        win.callOnFlip(self.send_stop)

    def on_routine_end(self):
        """The Routine ends: send the stop message now when the component
        started and didn't stop.
        """
        if self.stop_pending:
            self.stop_pending = False
            self.send_stop()

    def send_start(self):
        _send_if_text(self.start_message)

    def send_stop(self):
        _send_if_text(self.stop_message)


def _send_if_text(message):
    # An empty message is not sent; 0 is
    if message is None or message == '':
        return
    if _current_session is None or _current_session._closed:
        # A flip after the end of the session (e.g. the last flip of the
        # experiment) can't store the message anymore
        logging.warning(f"Titta message '{message}' not sent: the Titta session has ended")
        return
    get_session().send_message(message)


def _draw_gaze(image, dot, gaze):
    image.draw()
    if gaze is None:
        return
    for color, pos in zip(('red', 'blue'), gaze):
        if pos is None:
            continue
        dot.lineColor = color
        dot.fillColor = color
        dot.pos = pos
        dot.draw()


def _streams(arguments):
    return {stream: _bool(arguments[stream], f'Stream {stream}') for stream in STREAMS}


def _key_list(response_keys):
    if response_keys is None:
        return None
    if isinstance(response_keys, str):
        response_keys = response_keys.replace(',', ';').split(';')
    keys = []
    for key in response_keys:
        if not isinstance(key, str):
            raise TittaError(f'Response keys need to be key names, not {key!r}')
        key = key.strip().strip('\'"').strip()
        if key:
            keys.append(key)
    return keys or None


def _free_folder_name(folder):
    # Never write into an existing folder (e.g. left by an earlier run whose
    # .h5 file was moved): add the date and time, and a number when that
    # exists too
    if not os.path.exists(folder):
        return folder
    stamped = f'{folder}_{datetime.now():%Y%m%d-%H%M%S}'
    name = stamped
    i = 1
    while os.path.exists(name):
        name = f'{stamped}_{i}'
        i += 1
    logging.warning(f'png export: {folder} exists, the eye images go to {name}')
    return name


def _is_number(value):
    # bool is an int in Python, but True is no number of pixels
    return isinstance(value, (int, float)) and not isinstance(value, bool) \
        and math.isfinite(value)


def _number(value, label, types=(int, float), allow_zero=False):
    if types is int and isinstance(value, float) and value.is_integer():
        value = int(value)
    if not _is_number(value) or not isinstance(value, types) or value < 0 \
            or (value == 0 and not allow_zero):
        kind = 'integer' if types is int else 'number'
        requirement = f'0 or a positive {kind}' if allow_zero else f'a positive {kind}'
        raise TittaError(f'{label} needs to be {requirement}, not {value!r}')
    return value


def _bool(value, label):
    if not isinstance(value, bool):
        raise TittaError(f'{label} needs to be True or False, not {value!r}')
    return value


def _choice(value, options, label):
    if value not in options or isinstance(value, bool):
        raise TittaError(f'{label} needs to be one of: '
                         f'{", ".join(str(option) for option in options)}; not {value!r}')
    return value


def _resolution(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise TittaError(f'Operator screen resolution needs to be two numbers (x, y), '
                         f'not {value!r}')
    return tuple(_number(v, f'Operator screen resolution {axis}', int)
                 for v, axis in zip(value, 'XY'))
