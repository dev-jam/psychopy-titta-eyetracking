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

from .._base import SESSION, TittaActionComponent, icon_file


class TittaPlotGazeComponent(TittaActionComponent):
    """Shows the gaze position over the current display (the last flipped
    frame), on the stimulus display and/or the operator display, until a
    response key is pressed or the timeout has passed. The key and the
    response time go to the data file as `<name>.keys` and `<name>.rt`.
    """

    iconFile = icon_file(Path(__file__).parent, 'titta_plot_gaze')
    iconSVG = Path(__file__).parent / 'TittaPlotGazeComponent.svg'
    tooltip = _translate('Titta Plot Gaze: show the gaze position until a key press')

    def __init__(self, exp, parentName, name='titta_plot_gaze', when=None,
                 stimulusDisplay=False, operatorDisplay=False, simulateGaze=False,
                 disableWaitBlanking=False, responseKeys='', timeout=''):
        super().__init__(exp, parentName, name=name, when=when)
        self._param_bool('stimulusDisplay', stimulusDisplay, 'Plot gaze on stimulus display',
                         'Draw the gaze on the display of the participant')
        self._param_bool('operatorDisplay', operatorDisplay,
                         'Plot gaze on operator display',
                         'Draw the gaze on the operator screen (enable it in Titta Init)')
        self._param_bool('simulateGaze', simulateGaze, 'Simulate gaze in dummy mode',
                         'In dummy mode, draw gaze that moves in a circle')
        self._param_bool('disableWaitBlanking', disableWaitBlanking,
                         'Force disabling of waitBlanking for gaze plot on operator screen',
                         'Switch waitBlanking off on the operator screen while plotting')
        self._depends('operatorDisplay', 'disableWaitBlanking')
        self.params['responseKeys'] = Param(
            responseKeys, valType='list', inputType='single', categ='Basic',
            hint=_translate("Keys that end the plot, e.g. 'space', 'return'; empty: any key"),
            label=_translate('Response keys'))
        self.params['timeout'] = Param(
            timeout, valType='code', inputType='single', categ='Basic',
            hint=_translate('Time in seconds after which the plot ends; empty: no timeout'),
            label=_translate('Timeout (s, empty is infinite)'))
        self.order += ['stimulusDisplay', 'operatorDisplay', 'simulateGaze',
                       'disableWaitBlanking', 'responseKeys', 'timeout']

    def _write_action(self, buff):
        params = self.params
        name = params['name']
        escape = bool(self.exp.settings.params['Enable Escape'].val)
        code = (
            f"# Titta: plot gaze until a response key or the timeout\n"
            f"_titta_key, _titta_rt = {SESSION}.plot_gaze(\n"
            f"    stimulus_display={params['stimulusDisplay']},\n"
            f"    operator_display={params['operatorDisplay']},\n"
            f"    simulate_gaze={params['simulateGaze']},\n"
            f"    disable_waitblanking={params['disableWaitBlanking']},\n"
            f"    response_keys={params['responseKeys']},\n"
            f"    timeout={self._code_or_none(params['timeout'])},\n"
            f"    escape_key={escape})\n"
            f"thisExp.addData('{name}.keys', _titta_key)\n"
            f"thisExp.addData('{name}.rt', _titta_rt)\n"
        )
        if escape:
            code += (
                "if _titta_key == 'escape':\n"
                "    thisExp.status = FINISHED\n"
            )
        buff.writeIndentedLines(code)
