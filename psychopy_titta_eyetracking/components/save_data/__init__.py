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


class TittaSaveDataComponent(TittaActionComponent):
    """Saves the recording as `<data file>.h5` next to PsychoPy's data file
    (`<data file>_1.h5`, ... when that file exists), and can also export
    every table to tsv files and the eye images to png files. A failed
    export is a warning in the log; the data stays in the .h5 file. In
    dummy mode no data is saved. The path (without extension) goes to the
    data file as `<name>.file`.
    """

    iconFile = icon_file(Path(__file__).parent, 'titta_save_data')
    iconSVG = Path(__file__).parent / 'TittaSaveDataComponent.svg'
    tooltip = _translate('Titta Save Data: save the eye tracking data (HDF5, tsv, png)')

    def __init__(self, exp, parentName, name='titta_save_data', when=None,
                 tsvExport=False, pngExport=False):
        super().__init__(exp, parentName, name=name, when=when)
        self._param_bool('tsvExport', tsvExport, 'Additionally export to tsv files',
                         'Export every table in the HDF5 file to <file>_<table>.tsv')
        self._param_bool('pngExport', pngExport,
                         'Additionally export eye images to png files',
                         'Export the eye images (when recorded) to <file>_eye_image/<k>.png')
        self.order += ['tsvExport', 'pngExport']

    def _write_action(self, buff):
        name = self.params['name']
        buff.writeIndentedLines(
            f"# Titta: save the data\n"
            f"thisExp.addData('{name}.file', {SESSION}.save_data(\n"
            f"    tsv_export={self.params['tsvExport']},\n"
            f"    png_export={self.params['pngExport']}))\n")
