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

from psychopy.experiment.components import _translate

from .._base import SESSION, TittaActionComponent, icon_file


class TittaCalibrateComponent(TittaActionComponent):
    """Shows Titta's participant setup, calibration and validation screens
    (bimonocular and with the operator screen when chosen in Titta Init).
    Escape in these screens ends the experiment without saving the eye
    tracking data.
    """

    iconFile = icon_file(Path(__file__).parent, 'titta_calibrate')
    iconSVG = Path(__file__).parent / 'TittaCalibrateComponent.svg'
    tooltip = _translate('Titta Calibrate: participant setup, calibration and validation')

    def __init__(self, exp, parentName, name='titta_calibrate', when=None):
        super().__init__(exp, parentName, name=name, when=when)

    def _write_action(self, buff):
        buff.writeIndentedLines(
            f"# Titta: participant setup, calibration and validation\n"
            f"{SESSION}.calibrate()\n")
