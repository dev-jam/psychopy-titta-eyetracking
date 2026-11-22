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


class TittaSendMessageComponent(TittaComponent):
    """Sends a message to the recording, e.g. to mark the onset of a
    stimulus: the start message on the flip where the component starts, the
    stop message (optional) on the flip where it stops, or at the end of the
    Routine when the component has no stop. Without a stop the component
    doesn't keep the Routine running. The messages are evaluated at the
    start of each Routine (use $ for code, e.g. $'onset_' + image_file).
    """

    iconFile = icon_file(Path(__file__).parent, 'titta_send_message')
    iconSVG = Path(__file__).parent / 'TittaSendMessageComponent.svg'
    tooltip = _translate('Titta Send Message: mark an event in the eye tracking data')

    def __init__(self, exp, parentName, name='titta_message',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim='',
                 startMessage='onset_stimulusname', stopMessage=''):
        super().__init__(exp, parentName, name=name,
                         startType=startType, startVal=startVal,
                         stopType=stopType, stopVal=stopVal,
                         startEstim=startEstim, durationEstim=durationEstim,
                         syncScreenRefresh=True)
        self.params['startMessage'] = Param(
            startMessage, valType='str', inputType='single', categ='Basic',
            updates='set every repeat', allowedUpdates=[],
            hint=_translate('Sent on the flip where the component starts (empty: none)'),
            label=_translate('Start message'))
        self.params['stopMessage'] = Param(
            stopMessage, valType='str', inputType='single', categ='Basic',
            updates='set every repeat', allowedUpdates=[],
            hint=_translate('Sent on the flip where the component stops, or at the end of '
                            'the Routine without a stop (empty: none)'),
            label=_translate('Stop message'))
        self.order += ['startMessage', 'stopMessage']

    def writeInitCode(self, buff):
        buff.writeIndentedLines(
            f"{self.params['name']} = {MODULE}.TittaMessage("
            f"name='{self.params['name']}')\n")

    def writeRoutineStartCode(self, buff):
        name = self.params['name']
        buff.writeIndentedLines(
            f"{name}.start_message = {self.params['startMessage']}\n"
            f"{name}.stop_message = {self.params['stopMessage']}\n"
            f"{name}.stop_pending = False\n")

    def writeFrameCode(self, buff):
        name = self.params['name']
        buff.writeIndentedLines(f"\n# *{name}* updates\n")
        indented = self.writeStartTestCode(buff)
        if indented:
            code = f"{name}.on_start(win)\n"
            if self._no_stop():
                # Doesn't keep the Routine running
                code += f"{name}.status = FINISHED\n"
            buff.writeIndentedLines(code)
            buff.setIndentLevel(-indented, relative=True)
        indented = self.writeStopTestCode(buff)
        if indented:
            buff.writeIndentedLines(f"{name}.on_stop(win)\n")
            buff.setIndentLevel(-indented, relative=True)

    def writeRoutineEndCode(self, buff):
        buff.writeIndentedLines(
            f"# Titta: the stop message of {self.params['name']}, if not sent yet\n"
            f"{self.params['name']}.on_routine_end()\n")
        super().writeRoutineEndCode(buff)

    def _no_stop(self):
        return self.params['stopVal'].val in ('', None, -1, 'None')
