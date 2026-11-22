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

# Labels of the streams
STREAM_LABELS = {
    'gaze': 'gaze',
    'time_sync': 'time sync',
    'eye_image': 'eye images',
    'notifications': 'notifications',
    'external_signal': 'external signal',
    'positioning': 'positioning',
}
# Streams that are on by default (eye images are big)
DEFAULT_STREAMS = {stream: stream != 'eye_image' for stream in STREAMS}


class TittaStartRecordingComponent(TittaActionComponent):
    """Starts the recording of the chosen data streams."""

    iconFile = icon_file(Path(__file__).parent, 'titta_start_recording')
    iconSVG = Path(__file__).parent / 'TittaStartRecordingComponent.svg'
    tooltip = _translate('Titta Start Recording: start recording eye tracking data')

    def __init__(self, exp, parentName, name='titta_start_recording', when=None,
                 gaze=True, time_sync=True, eye_image=False, notifications=True,
                 external_signal=True, positioning=True, blockingMode=True):
        super().__init__(exp, parentName, name=name, when=when)
        values = dict(gaze=gaze, time_sync=time_sync, eye_image=eye_image,
                      notifications=notifications, external_signal=external_signal,
                      positioning=positioning)
        for stream in STREAMS:
            self._param_bool(stream, values[stream], f'Record {STREAM_LABELS[stream]}',
                             f'Record the {STREAM_LABELS[stream]} stream (when the eye '
                             f'tracker has it)')
            self.order.append(stream)
        self._param_bool('blockingMode', blockingMode, 'Block until recording has started',
                         'Wait until the first gaze sample arrives (at most 5 s)')
        self.order.append('blockingMode')

    def _write_action(self, buff):
        streams = ', '.join(f'{stream}={self.params[stream]}' for stream in STREAMS)
        buff.writeIndentedLines(
            f"# Titta: start recording\n"
            f"{SESSION}.start_recording(\n"
            f"    {streams},\n"
            f"    block_until_data_available={self.params['blockingMode']})\n")
