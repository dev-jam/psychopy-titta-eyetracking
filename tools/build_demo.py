"""
Build the demo experiment demo/titta_demo.psyexp with PsychoPy's Builder
API, the same experiment as the demo of opensesame-plugin-titta_eyetracking.
Needs PsychoPy and this plugin installed.

Run from the repository root: python tools/build_demo.py

SPDX-License-Identifier: GPL-3.0-or-later
"""

import csv
from pathlib import Path

from psychopy import plugins

plugins.activatePlugins()

from psychopy import experiment  # noqa: E402
from psychopy.experiment.components.image import ImageComponent  # noqa: E402
from psychopy.experiment.components.keyboard import KeyboardComponent  # noqa: E402
from psychopy.experiment.components.text import TextComponent  # noqa: E402
from psychopy.experiment.loops import TrialHandler  # noqa: E402
from psychopy.experiment.routines import Routine  # noqa: E402

from psychopy_titta_eyetracking.components.calibrate import TittaCalibrateComponent  # noqa: E402
from psychopy_titta_eyetracking.components.init import TittaInitComponent  # noqa: E402
from psychopy_titta_eyetracking.components.plot_gaze import TittaPlotGazeComponent  # noqa: E402
from psychopy_titta_eyetracking.components.save_data import TittaSaveDataComponent  # noqa: E402
from psychopy_titta_eyetracking.components.send_message import \
    TittaSendMessageComponent  # noqa: E402
from psychopy_titta_eyetracking.components.start_recording import \
    TittaStartRecordingComponent  # noqa: E402
from psychopy_titta_eyetracking.components.stop_recording import \
    TittaStopRecordingComponent  # noqa: E402
from psychopy_titta_eyetracking.components._base import WHEN_END  # noqa: E402

DEMO = Path(__file__).resolve().parent.parent / 'demo'
BLOCKS = {
    'block1': [f'balls{row}{column}' for row in (1, 2, 3) for column in (1, 2, 3)],
    'block2': ['stim1', 'stim2'],
}
RESOLUTION = '1920x1080'

README = """Simple demo eye tracking experiment for the Titta PsychoPy plugin \
(psychopy-titta-eyetracking), the same as the demo of the Titta OpenSesame plugin.

By default it runs in dummy mode. To connect to a Tobii eye tracker, set Dummy mode \
to No in the 'titta' component (routine 'setup') and select the eye tracker.

The experiment asks whether to plot the gaze on the stimulus screen after each \
stimulus. In dummy mode the gaze moves in a circle; with an eye tracker it is the \
real gaze. Press space to go on. Eye tracking data: data/<participant>_titta_demo_<date>.h5 \
(and tsv files) next to the PsychoPy data file.

The pictures and the data are compatible with the demo analysis of Titta: \
https://github.com/marcus-nystrom/Titta"""


def text(routine, name, message, stop=''):
    component = TextComponent(routine.exp, routine.name, name=name, text=message,
                              letterHeight=0.04, stopVal=stop)
    routine.addComponent(component)
    return component


def keyboard(routine, name, keys, start=0.0, **kwargs):
    component = KeyboardComponent(routine.exp, routine.name, name=name, allowedKeys=keys,
                                  startVal=start, **kwargs)
    routine.addComponent(component)
    return component


def new_routine(exp, name, position):
    routine = Routine(name, exp)
    exp.addRoutine(name, routine)
    exp.flow.addRoutine(routine, position)
    return routine


def main():
    for block, stims in BLOCKS.items():
        with open(DEMO / f'{block}.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['stim'])
            writer.writerows([stim] for stim in stims)

    exp = experiment.Experiment()
    exp.settings.params['expName'].val = 'titta_demo'
    exp.settings.params['Experiment info'].val = "{'participant': '001', 'session': '001'}"
    exp.settings.params['Units'].val = 'norm'
    exp.settings.params['Window size (pixels)'].val = '[1920, 1080]'
    exp.settings.params['Show info dlg'].val = True
    exp.settings.params['Save excel file'].val = False

    setup = new_routine(exp, 'setup', 0)
    setup.addComponent(TittaInitComponent(exp, 'setup', name='titta', dummyMode='Yes'))
    text(setup, 'gaze_question', 'Titta demo\n\nPlot the gaze on the stimulus screen after each '
         'stimulus? (y/n)', stop='')
    keyboard(setup, 'gaze_response', "'y','n'")
    setup.settings.params['desc'].val = README

    calibrate_question = new_routine(exp, 'calibrate_question', 1)
    text(calibrate_question, 'calibrate_text', 'Calibrate the eye tracker? (y/n)', stop='')
    keyboard(calibrate_question, 'calibrate_response', "'y','n'")

    calibration = new_routine(exp, 'calibration', 2)
    calibration.addComponent(TittaCalibrateComponent(exp, 'calibration'))
    calibration.settings.params['skipIf'].val = "calibrate_response.keys != 'y'"

    welcome = new_routine(exp, 'welcome', 3)
    text(welcome, 'welcome_text', 'Look at the pictures. Press space to go on.\n\n'
         'Press space to start', stop='')
    keyboard(welcome, 'welcome_response', "'space'")
    welcome.addComponent(TittaStartRecordingComponent(exp, 'welcome', when=WHEN_END))

    position = 4
    for block in BLOCKS:
        trial = new_routine(exp, f'trial_{block}', position)
        text(trial, f'fix_cross_{block}', '+', stop=1.0)
        trial.addComponent(TittaSendMessageComponent(
            exp, trial.name, name=f'fix_message_{block}', startVal=0.0, stopVal=1.0,
            startMessage='fix_on', stopMessage='fix_off'))
        file_name = f"stim + '_{RESOLUTION}.jpg'"
        image = ImageComponent(
            exp, trial.name, name=f'stimulus_{block}', image=f'${file_name}',
            size=(2, 2), units='norm', startVal=1.0, stopVal='')
        image.params['image'].updates = 'set every repeat'
        trial.addComponent(image)
        trial.addComponent(TittaSendMessageComponent(
            exp, trial.name, name=f'stim_message_{block}', startVal=1.0, stopVal='',
            startMessage=f"$'onset_' + {file_name}",
            stopMessage=f"$'offset_' + {file_name}"))
        keyboard(trial, f'key_resp_{block}', "'space'", start=1.0)
        gaze = new_routine(exp, f'gaze_{block}', position + 1)
        gaze.addComponent(TittaPlotGazeComponent(
            exp, gaze.name, name=f'plot_gaze_{block}', stimulusDisplay=True,
            simulateGaze=True, responseKeys="'space'"))
        gaze.settings.params['skipIf'].val = "gaze_response.keys != 'y'"
        loop = TrialHandler(exp, name=block, loopType='sequential', nReps=1,
                            conditionsFile=f'{block}.csv')
        exp.flow.addLoop(loop, startPos=position, endPos=position + 2)
        position += 4  # two routines, loop start and end

    done = new_routine(exp, 'done', position)
    done.addComponent(TittaStopRecordingComponent(exp, 'done'))
    done.addComponent(TittaSaveDataComponent(exp, 'done', tsvExport=True))
    text(done, 'done_text', 'Done! Press space to end the experiment', stop='')
    keyboard(done, 'done_response', "'space'")

    exp.saveToXML(str(DEMO / 'titta_demo.psyexp'))


if __name__ == '__main__':
    main()
