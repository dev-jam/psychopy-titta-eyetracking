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
"""

__author__ = "Bob Rosbag"
__license__ = "GPL-3.0-or-later"

from pathlib import Path

from psychopy.experiment.components import Param, _translate

from .._base import MODULE, TittaComponent, icon_file
from ...session import OPERATOR_BACKGROUNDS


class TittaPlotGazeComponent(TittaComponent):
    """Shows the gaze in real time while the component runs, e.g. during a
    stimulus: on the operator display as a copy of the stimulus display with
    the gaze on top (for the researcher), and/or on the stimulus display.
    Left eye red, right eye blue. Put it below the stimuli in the Routine
    and give it the same start and stop as the stimulus; without a stop it
    runs until the end of the Routine (e.g. a key press of a Keyboard
    component).
    """

    iconFile = icon_file(Path(__file__).parent, 'titta_plot_gaze')
    iconSVG = Path(__file__).parent / 'TittaPlotGazeComponent.svg'
    tooltip = _translate('Titta Plot Gaze: show the gaze in real time')

    def __init__(self, exp, parentName, name='titta_plot_gaze',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim='',
                 operatorDisplay=True, operatorBackground=OPERATOR_BACKGROUNDS[0],
                 stimulusDisplay=False, simulateGaze=False,
                 disableWaitBlanking=False):
        super().__init__(exp, parentName, name=name,
                         startType=startType, startVal=startVal,
                         stopType=stopType, stopVal=stopVal,
                         startEstim=startEstim, durationEstim=durationEstim,
                         syncScreenRefresh=True)
        self._param_bool('operatorDisplay', operatorDisplay,
                         'Plot gaze on operator display',
                         'Show a copy of the stimulus display with the gaze on the operator '
                         'screen (enable it in Titta Init)')
        self.params['operatorBackground'] = Param(
            operatorBackground, valType='str', inputType='choice', categ='Basic',
            allowedVals=list(OPERATOR_BACKGROUNDS),
            hint=_translate('Under the gaze on the operator display: a copy of the stimulus '
                            'display, made every frame (live, but reading the screen takes '
                            'time: check the frame timing) or once at the start of the '
                            'component (for a static stimulus), or nothing'),
            label=_translate('Operator display background'))
        self._depends('operatorDisplay', 'operatorBackground')
        self._param_bool('disableWaitBlanking', disableWaitBlanking,
                         'Force disabling of waitBlanking for gaze plot on operator screen',
                         'Switch waitBlanking off on the operator screen while plotting')
        self._depends('operatorDisplay', 'disableWaitBlanking')
        self._param_bool('stimulusDisplay', stimulusDisplay, 'Plot gaze on stimulus display',
                         'Draw the gaze on the display of the participant, on top of the '
                         'stimuli')
        self._param_bool('simulateGaze', simulateGaze, 'Simulate gaze in dummy mode',
                         'In dummy mode, draw gaze that moves in a circle')
        self.order += ['operatorDisplay', 'operatorBackground', 'disableWaitBlanking',
                       'stimulusDisplay', 'simulateGaze']

    def writeInitCode(self, buff):
        params = self.params
        buff.writeIndentedLines(
            f"{params['name']} = {MODULE}.TittaGazePlot(\n"
            f"    name='{params['name']}', win=win,\n"
            f"    stimulus_display={params['stimulusDisplay']},\n"
            f"    operator_display={params['operatorDisplay']},\n"
            f"    simulate_gaze={params['simulateGaze']},\n"
            f"    disable_waitblanking={params['disableWaitBlanking']},\n"
            f"    operator_background={params['operatorBackground']})\n")

    def writeFrameCode(self, buff):
        name = self.params['name']
        buff.writeIndentedLines(f"\n# *{name}* updates\n")
        indented = self.writeStartTestCode(buff)
        if indented:
            buff.writeIndentedLines(f"{name}.start()\n")
            buff.setIndentLevel(-indented, relative=True)
        indented = self.writeStopTestCode(buff)
        if indented:
            buff.writeIndentedLines(f"{name}.stop()\n")
            buff.setIndentLevel(-indented, relative=True)
        buff.writeIndentedLines(
            f"# Titta: draw the newest gaze sample\n"
            f"{name}.update()\n")

    def writeRoutineEndCode(self, buff):
        buff.writeIndentedLines(
            f"# Titta: stop plotting the gaze of {self.params['name']}\n"
            f"{self.params['name']}.stop()\n")
        super().writeRoutineEndCode(buff)
