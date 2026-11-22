"""
Tests of the Builder components: registration through the entry points, a
save/load round trip of the .psyexp file and the generated Python code.

SPDX-License-Identifier: GPL-3.0-or-later
"""

import ast

import pytest
from psychopy import plugins

plugins.activatePlugins()

from psychopy import experiment  # noqa: E402
from psychopy.experiment.components import getAllComponents  # noqa: E402
from psychopy.experiment.routines import Routine  # noqa: E402

COMPONENTS = ['TittaInitComponent', 'TittaCalibrateComponent',
              'TittaStartRecordingComponent', 'TittaSendMessageComponent',
              'TittaPlotGazeComponent', 'TittaStopRecordingComponent',
              'TittaSaveDataComponent']


def build(params=None, when=None, skip_if=''):
    """An experiment with one Routine holding all Titta components."""
    all_components = getAllComponents()
    exp = experiment.Experiment()
    routine = Routine('trial', exp)
    exp.addRoutine('trial', routine)
    exp.flow.addRoutine(routine, 0)
    routine.settings.params['skipIf'].val = skip_if
    for name in COMPONENTS:
        component = all_components[name](exp, 'trial')
        for key, val in (params or {}).get(name, {}).items():
            component.params[key].val = val
        if when and 'when' in component.params:
            component.params['when'].val = when
        routine.addComponent(component)
    return exp


def test_registered():
    assert set(COMPONENTS) <= set(getAllComponents())
    for name in COMPONENTS:
        component = getAllComponents()[name]
        assert component.plugin == 'psychopy-titta-eyetracking'
        assert component.targets == ['PsychoPy']
        assert component.categories == ['Titta Eye Tracking']


@pytest.mark.parametrize('when', ['Routine start', 'Routine end'])
@pytest.mark.parametrize('skip_if', ['', "$key.keys != 'y'"])
@pytest.mark.parametrize('params', [
    {},
    {'TittaInitComponent': {
        'dummyMode': 'When piloting', 'samplingRateManual': True, 'samplingRate': 300,
        'calibrationManual': True, 'headBoxManual': True, 'headBoxCenterX': 0,
        'headBoxCenterY': -30, 'headBoxCenterZ': 650, 'operatorScreen': True},
     'TittaSendMessageComponent': {'stopVal': 2.0, 'startMessage': "$'onset_' + image"},
     'TittaPlotGazeComponent': {'responseKeys': "'space', 'return'", 'timeout': 5}},
])
def test_code(tmp_path, params, when, skip_if):
    exp = build(params, when, skip_if)
    path = tmp_path / 'exp.psyexp'
    exp.saveToXML(str(path))
    loaded = experiment.Experiment()
    loaded.loadFromXML(str(path))
    script = loaded.writeScript(target='PsychoPy')
    ast.parse(script)
    assert 'import psychopy_titta_eyetracking' in script
    assert 'runAtExit.append(titta.close)' in script
    if params:
        assert 'dummy_mode=PILOTING' in script
        assert 'sampling_rate=300' in script
        assert 'head_box_center=[0, -30, 650]' in script
        assert 'operator_resolution=(1920, 1080)' in script
        assert "response_keys=['space', 'return']" in script
        assert 'timeout=5' in script
        assert "start_message = 'onset_' + image" in script
        assert 'titta_message.on_stop(win)' in script
    else:
        assert 'sampling_rate=None' in script
        assert 'calibration_dot=' not in script
        assert 'titta_message.status = FINISHED' in script
    if skip_if:
        assert "if not (key.keys != 'y'):  # 'Skip if' of the Routine" in script


def test_disabled_component_writes_nothing():
    exp = build()
    for component in exp.routines['trial']:
        if type(component).__name__ == 'TittaCalibrateComponent':
            component.params['disabled'].val = True
    assert '.calibrate()' not in exp.writeScript(target='PsychoPy')
