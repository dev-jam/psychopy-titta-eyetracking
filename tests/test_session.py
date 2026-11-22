"""
Tests of the run-time part (session.py) without a window or an eye tracker:
settings checks, recording state, the blocking start and saving/exporting
with a fake Titta object.

SPDX-License-Identifier: GPL-3.0-or-later
"""

import os

import h5py
import numpy as np
import pandas as pd
import pytest

from psychopy_titta_eyetracking import session as titta_session
from psychopy_titta_eyetracking.session import TittaError, TittaSession, get_session


@pytest.fixture(autouse=True)
def no_session():
    titta_session._current_session = None
    yield
    titta_session._current_session = None


class FakeWindow:
    units = 'norm'


class FakeBuffer:
    def __init__(self, timestamps):
        self.timestamps = timestamps

    def peek_N(self, stream, n):
        return {'system_time_stamp': np.array(self.timestamps[-n:] if self.timestamps else [])}


class FakeTracker:
    """Writes an HDF5 file like Titta's save_data()."""

    def __init__(self, settings, timestamps=(10, 20), eye_images=0):
        self.settings = settings
        self.buffer = FakeBuffer(list(timestamps))
        self.eye_images = eye_images
        self.calls = []

    def get_system_time_stamp(self):
        return 15

    def start_recording(self, **kwargs):
        self.calls.append(('start', kwargs))

    def stop_recording(self, **kwargs):
        self.calls.append(('stop', kwargs))

    def send_message(self, msg, ts=None):
        self.calls.append(('msg', msg, ts))

    def save_data(self, filename=None, append_version=True):
        path = os.path.join(self.settings.DATA_STORAGE_PATH, filename)
        pd.DataFrame({'system_time_stamp': [1, 2], 'x': [0.1, 0.2]}).to_hdf(
            path + '.h5', key='gaze')
        pd.DataFrame({'system_time_stamp': [1], 'msg': ['hi']}).to_hdf(path + '.h5', key='msg')
        if self.eye_images:
            with h5py.File(path + '.h5', 'a') as hf:
                group = hf.create_group('eye_image')
                for k in range(self.eye_images):
                    group.create_dataset(str(k), data=np.full((4, 6), k, dtype=np.uint8))
        self.calls.append(('save', filename))


def make_session(tmp_path, **kwargs):
    s = TittaSession(FakeWindow(), str(tmp_path / 'data' / '001_exp_2026-11-22_10h00.00.000'),
                     **kwargs)
    s._set_data_file()
    return s


def connect_fake(s, **kwargs):
    s.tracker = FakeTracker(s.settings, **kwargs)
    return s.tracker


def test_defaults(tmp_path):
    s = make_session(tmp_path)
    assert get_session() is s
    assert s.settings.eye_tracker_name == 'Tobii Pro Spectrum'
    assert s.settings.N_CAL_TARGETS == 5
    assert s.settings.CAL_TARGET is None
    assert s.settings.FILENAME == '001_exp_2026-11-22_10h00.00.000'


def test_one_session_only(tmp_path):
    s = make_session(tmp_path)
    with pytest.raises(TittaError, match='only one'):
        make_session(tmp_path)
    s.close()
    make_session(tmp_path)


def test_no_session():
    with pytest.raises(TittaError, match='Titta Init'):
        get_session()


@pytest.mark.parametrize('kwargs, message', [
    ({'tracker': 'Tobii Unknown'}, 'Eye tracker needs'),
    ({'n_calibration_targets': 7}, 'Number of calibration targets'),
    ({'n_calibration_targets': True}, 'Number of calibration targets'),
    ({'sampling_rate': 0}, 'Sampling rate'),
    ({'sampling_rate': 60.5}, 'Sampling rate'),
    ({'sampling_rate': '60'}, 'Sampling rate'),
    ({'tracking_mode': 'monkey'}, 'Tracking mode'),
    ({'dummy_mode': 'yes'}, 'Dummy mode'),
    ({'calibration_pacing_interval': 0.5}, 'at least 0.8'),
    ({'calibration_dot_size': -1}, 'Calibration dot size'),
    ({'calibration_dot_size': float('nan')}, 'Calibration dot size'),
    ({'calibration_movement_duration': -0.1}, 'Movement duration'),
    ({'calibration_dot': 'Red'}, 'Calibration dot type'),
    ({'calibration_auto_pace': 3}, 'auto pace'),
    ({'head_box_center': [0, 0]}, 'three dimensions'),
    ({'head_box_center': [0, 'a', 600]}, 'three dimensions'),
    ({'operator_screen': True, 'operator_resolution': (0, 1080)}, 'resolution X'),
    ({'operator_screen': True, 'operator_screen_nr': -1}, 'screen number'),
    ({'tracker_address': 5}, 'address'),
])
def test_invalid_settings(tmp_path, kwargs, message):
    with pytest.raises(TittaError, match=message):
        make_session(tmp_path, **kwargs)
    assert titta_session._current_session is None


def test_manual_settings(tmp_path):
    s = make_session(
        tmp_path, sampling_rate=120.0, tracking_mode='human', n_calibration_targets=3,
        calibration_dot='Black', calibration_dot_size=36, calibration_animate=False,
        calibration_pacing_interval=1, calibration_auto_pace='Space bar',
        calibration_movement_duration=0, head_box_center=[0, -30.5, 650])
    settings = s.settings
    assert settings.SAMPLING_RATE == 120 and isinstance(settings.SAMPLING_RATE, int)
    assert settings.TRACKING_MODE == 'human'
    assert settings.N_CAL_TARGETS == 3
    assert type(settings.CAL_TARGET).__name__ == 'MyDot3'
    assert settings.graphics.TARGET_SIZE == 36
    assert settings.graphics.TARGET_SIZE_INNER == 6
    assert settings.ANIMATE_CALIBRATION is False
    assert settings.PACING_INTERVAL == 1
    assert settings.AUTO_PACE == 0
    assert settings.MOVE_TARGET_DURATION == 0
    assert settings.HEAD_BOX_CENTER == [0, -30.5, 650]


def test_not_connected(tmp_path):
    s = make_session(tmp_path)
    with pytest.raises(TittaError, match='not connected'):
        s.start_recording()


def test_recording_state(tmp_path):
    s = make_session(tmp_path)
    tracker = connect_fake(s)
    with pytest.raises(TittaError, match='not recording'):
        s.stop_recording()
    s.start_recording(block_until_data_available=False, eye_image=True)
    assert tracker.calls[-1] == ('start', dict(
        gaze=True, time_sync=True, eye_image=True, notifications=True,
        external_signal=True, positioning=True, block_until_data_available=False))
    with pytest.raises(TittaError, match='still recording'):
        s.start_recording()
    with pytest.raises(TittaError, match='still recording'):
        s.save_data()
    s.stop_recording(positioning=False)
    assert tracker.calls[-1][1]['positioning'] is False
    assert s.recording is False


def test_blocking_start(tmp_path):
    s = make_session(tmp_path)
    connect_fake(s, timestamps=(10, 20))  # 20 > 15: a new sample
    s.start_recording()
    assert s.recording


def test_blocking_start_timeout(tmp_path, monkeypatch):
    monkeypatch.setattr(titta_session, 'BLOCK_TIMEOUT', 0.05)
    s = make_session(tmp_path)
    connect_fake(s, timestamps=())
    with pytest.raises(TittaError, match='No gaze data'):
        s.start_recording()
    # The streams were started: stopping must be possible
    assert s.recording
    s.stop_recording()


def test_send_message_as_text(tmp_path):
    s = make_session(tmp_path)
    tracker = connect_fake(s)
    s.send_message(5.0)
    assert tracker.calls[-1] == ('msg', '5.0', None)


def test_titta_error_wrapped(tmp_path):
    s = make_session(tmp_path)
    tracker = connect_fake(s)

    def fail(**kwargs):
        raise AssertionError('The given tracking\n   mode is not supported')
    tracker.start_recording = fail
    with pytest.raises(TittaError, match='Titta could not start recording: The given tracking '
                                         'mode is not supported'):
        s.start_recording(block_until_data_available=False)


def test_save_and_export(tmp_path):
    s = make_session(tmp_path)
    connect_fake(s, eye_images=3)
    file_name = s.save_data(tsv_export=True, png_export=True)
    assert file_name == str(tmp_path / 'data' / '001_exp_2026-11-22_10h00.00.000')
    assert os.path.exists(file_name + '_gaze.tsv')
    assert os.path.exists(file_name + '_msg.tsv')
    images = sorted(os.listdir(file_name + '_eye_image'))
    assert images == ['0.png', '1.png', '2.png']
    # A second save gets a new name (the name has dots: Titta's own check
    # misses it) and a new png folder
    second = s.save_data(png_export=True)
    assert second == file_name + '_1'
    assert os.path.exists(second + '.h5')


def test_failed_export_is_a_warning(tmp_path, monkeypatch):
    s = make_session(tmp_path)
    connect_fake(s)

    def fail(file_name):
        raise OSError('disk full')
    monkeypatch.setattr(s, '_export_tsv', fail)
    assert s.save_data(tsv_export=True)


def test_close(tmp_path):
    s = make_session(tmp_path)
    connect_fake(s)
    s.start_recording(block_until_data_available=False)
    s.close()
    s.close()  # twice is fine
    with pytest.raises(TittaError, match='has ended'):
        s.send_message('late')


@pytest.mark.parametrize('keys, expected', [
    (None, None),
    ([], None),
    ('', None),
    ('space', ['space']),
    ("a; b ,c", ['a', 'b', 'c']),
    (['space', ' return '], ['space', 'return']),
])
def test_key_list(keys, expected):
    assert titta_session._key_list(keys) == expected


def test_key_list_invalid():
    with pytest.raises(TittaError):
        titta_session._key_list([1])


class FakeStim:
    def __init__(self):
        self.autoDraw = False
        self.pos = None
        self.drawn = 0
        self.image = None

    def draw(self):
        self.drawn += 1


class FakeOperatorWindow:
    def __init__(self):
        self.waitBlanking = True
        self.flips = 0

    def flip(self):
        self.flips += 1


def test_gaze_plot_needs_operator_screen(tmp_path):
    s = make_session(tmp_path)
    connect_fake(s)
    plot = titta_session.TittaGazePlot('plot', FakeWindow(), operator_display=True)
    with pytest.raises(TittaError, match='operator screen is not enabled'):
        plot.start()


def test_gaze_plot_live(tmp_path):
    s = make_session(tmp_path, operator_screen=True, operator_waitblanking=True)
    connect_fake(s)
    s.dummy_mode = True  # simulated gaze, no buffer needed
    window = FakeOperatorWindow()
    s.operator_window = window
    plot = titta_session.TittaGazePlot('plot', FakeWindow(), stimulus_display=True,
                                       operator_display=True, simulate_gaze=True,
                                       disable_waitblanking=True)
    # No OpenGL here: fake stimuli and frame capture
    plot._stimulus_dots = [FakeStim(), FakeStim()]
    background, dots = FakeStim(), [FakeStim(), FakeStim()]
    plot._operator = (window, background, dots)
    plot._capture = FakeStim()
    plot.win._setCurrent = lambda: None
    plot.start()
    assert window.waitBlanking is False and plot._capture.autoDraw
    plot.update()  # nothing captured yet: no background
    assert background.drawn == 0 and all(d.autoDraw for d in plot._stimulus_dots)
    plot._store_frame('frame 1')  # what the flip of the stimulus display does
    plot.update()
    assert background.image == 'frame 1' and background.drawn == 1
    assert dots[0].drawn == 2 and window.flips == 2
    plot.stop()
    plot.stop()  # twice is fine (stop time and end of the Routine)
    assert window.waitBlanking is True
    assert not plot._capture.autoDraw and not any(d.autoDraw for d in plot._stimulus_dots)
    plot.update()  # after the stop: nothing happens
    assert window.flips == 2


def test_gaze_plot_dummy_without_simulation(tmp_path):
    s = make_session(tmp_path)
    connect_fake(s)
    s.dummy_mode = True
    plot = titta_session.TittaGazePlot('plot', FakeWindow(), stimulus_display=True,
                                       operator_display=False)
    plot._stimulus_dots = [FakeStim(), FakeStim()]
    plot.start()
    plot.update()
    assert not any(d.autoDraw for d in plot._stimulus_dots)
