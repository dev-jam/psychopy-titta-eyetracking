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
from ...session import STREAMS
from ..start_recording import STREAM_LABELS


class TittaStopRecordingComponent(TittaActionComponent):
    """Stops the recording of the chosen data streams."""

    iconFile = icon_file(Path(__file__).parent, 'titta_stop_recording')
    iconSVG = Path(__file__).parent / 'TittaStopRecordingComponent.svg'
    tooltip = _translate('Titta Stop Recording: stop recording eye tracking data')

    def __init__(self, exp, parentName, name='titta_stop_recording', when=None,
                 gaze=True, time_sync=True, eye_image=False, notifications=True,
                 external_signal=True, positioning=True):
        super().__init__(exp, parentName, name=name, when=when)
        values = dict(gaze=gaze, time_sync=time_sync, eye_image=eye_image,
                      notifications=notifications, external_signal=external_signal,
                      positioning=positioning)
        for stream in STREAMS:
            self._param_bool(stream, values[stream],
                             f'Stop recording {STREAM_LABELS[stream]}',
                             f'Stop the {STREAM_LABELS[stream]} stream')
            self.order.append(stream)

    def _write_action(self, buff):
        streams = ', '.join(f'{stream}={self.params[stream]}' for stream in STREAMS)
        buff.writeIndentedLines(
            f"# Titta: stop recording\n"
            f"{SESSION}.stop_recording(\n"
            f"    {streams})\n")
