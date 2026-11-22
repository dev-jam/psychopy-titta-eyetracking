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

from psychopy.alerts import alerttools
from psychopy.experiment.components import BaseComponent, Param, _translate

from .. import DISTRIBUTION

CATEGORY = 'Titta Eye Tracking'
# The generated script imports the plugin under this name
MODULE = 'psychopy_titta_eyetracking'
SESSION = f'{MODULE}.get_session()'
HELP_URL = 'https://github.com/dev-jam/psychopy-titta-eyetracking#readme'

# When an action component acts in its Routine
WHEN_START = 'Routine start'
WHEN_END = 'Routine end'

# Inherited timing params that an action component doesn't use
TIMING_PARAMS = ('startType', 'startVal', 'startEstim', 'stopType', 'stopVal',
                 'durationEstim', 'saveStartStop', 'syncScreenRefresh')


def icon_file(folder, stem):
    """The icon of a component: `<folder>/<stem>.png`; Builder reads
    `<folder>/<theme>/<stem>.png` and `<stem>@2x.png` (themes light, dark
    and classic).
    """
    return Path(folder) / f'{stem}.png'


class TittaComponent(BaseComponent):
    """Base class of the Titta components."""

    categories = [CATEGORY]
    targets = ['PsychoPy']
    plugin = DISTRIBUTION
    version = '2024.2.0'
    beta = False

    def __init__(self, exp, parentName, name='', **kwargs):
        super().__init__(exp, parentName, name=name, **kwargs)
        self.url = HELP_URL
        self.exp.requireImport(importName=MODULE)

    def _param_bool(self, key, val, label, hint):
        self.params[key] = Param(
            val, valType='bool', inputType='bool', categ='Basic',
            hint=_translate(hint), label=_translate(label))

    def _depends(self, on, param, condition='== True', false='disable'):
        self.depends.append({
            'dependsOn': on,
            'condition': condition,
            'param': param,
            'true': 'enable' if false == 'disable' else 'show',
            'false': false,
        })

    @staticmethod
    def _code_or_none(param):
        """The code of a number param, `None` when it is empty."""
        text = str(param).strip()
        return text if text else 'None'


class TittaActionComponent(TittaComponent):
    """A component that does one thing at the start or the end of its
    Routine (connect, calibrate, start recording, ...). It has no timing and
    doesn't keep the Routine running.
    """

    # Default of the When param
    default_when = WHEN_START

    def __init__(self, exp, parentName, name='', when=None, **kwargs):
        super().__init__(exp, parentName, name=name, **kwargs)
        for param in TIMING_PARAMS:
            self.params.pop(param, None)
        self.order = ['name', 'when']
        self.params['when'] = Param(
            when or self.default_when, valType='str', inputType='choice', categ='Basic',
            allowedVals=[WHEN_START, WHEN_END],
            hint=_translate('Act at the start of the Routine (before its first frame) or at '
                            'its end'),
            label=_translate('When'))

    def integrityCheck(self):
        # No timing to check
        alerttools.testDisabled(self)

    def writeRoutineStartCode(self, buff):
        if self.params['when'].val == WHEN_START:
            self._write_guarded_action(buff)

    def writeRoutineEndCode(self, buff):
        if self.params['when'].val == WHEN_END:
            self._write_guarded_action(buff)

    def _write_guarded_action(self, buff):
        # PsychoPy checks the 'Skip if' of a Routine after the Begin Routine
        # code, and runs the End Routine code of a skipped Routine too: the
        # action must not run in a skipped Routine
        condition = self._skip_condition()
        if not condition:
            self._write_action(buff)
            return
        buff.writeIndentedLines(f"if not ({condition}):  # 'Skip if' of the Routine\n")
        buff.setIndentLevel(1, relative=True)
        self._write_action(buff)
        buff.setIndentLevel(-1, relative=True)

    def _skip_condition(self):
        routine = self.exp.routines.get(self.parentName)
        settings = getattr(routine, 'settings', None)
        if settings is None or 'skipIf' not in settings.params:
            return ''
        condition = str(settings.params['skipIf'].val).strip()
        return condition[1:].strip() if condition.startswith('$') else condition

    def _write_action(self, buff):
        raise NotImplementedError
