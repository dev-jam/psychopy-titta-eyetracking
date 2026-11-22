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

from .._base import MODULE, TIMING_PARAMS, TittaComponent, icon_file
from ...session import (AUTO_PACE, CALIBRATION_DOTS, N_CALIBRATION_TARGETS,
                        TRACKERS, TRACKING_MODES)

# Choices of the Dummy mode param, and the code they become
DUMMY_MODES = {
    'No': 'False',
    'Yes': 'True',
    'When piloting': 'PILOTING',
}


class TittaInitComponent(TittaComponent):
    """Connects to the eye tracker and sets it up when the experiment starts
    (after the window opens): the eye tracker model, dummy mode, calibration
    settings and an optional operator screen. One per experiment; put it in
    the first Routine. The session is available in Code components under the
    name of this component (`<name>.tracker` is the Titta object).
    """

    iconFile = icon_file(Path(__file__).parent, 'titta_init')
    iconSVG = Path(__file__).parent / 'TittaInitComponent.svg'
    tooltip = _translate('Titta Init: connect to and set up the Tobii eye tracker')

    def __init__(self, exp, parentName, name='titta',
                 dummyMode='No', verbose=False,
                 tracker='Tobii Pro Spectrum', trackerAddress='',
                 samplingRateManual=False, samplingRate='',
                 trackingMode='Default',
                 bimonocularCalibration=False, nCalibrationTargets='5',
                 recordEyeImagesDuringCalibration=False,
                 calibrationManual=False, calibrationDot='Thaler (default)',
                 calibrationDotSize=30, calibrationAnimate=True,
                 calibrationPacingInterval=1.0,
                 calibrationAutoPace='Autoaccept (default)',
                 calibrationMovementDuration=0.5,
                 headBoxManual=False, headBoxCenterX='', headBoxCenterY='',
                 headBoxCenterZ='',
                 operatorScreen=False, operatorScreenName='default',
                 operatorScreenNr=1, operatorXRes=1920, operatorYRes=1080,
                 operatorWaitBlanking=False,
                 dataFileName='thisExp.dataFileName'):
        super().__init__(exp, parentName, name=name)
        for param in TIMING_PARAMS:
            self.params.pop(param, None)

        # --- Basic ---
        self.params['dummyMode'] = Param(
            dummyMode, valType='str', inputType='choice', categ='Basic',
            allowedVals=list(DUMMY_MODES),
            hint=_translate('Run without an eye tracker (Titta\'s dummy mode; no data is '
                            'saved). "When piloting": in pilot mode only'),
            label=_translate('Dummy mode'))
        self._param_bool('verbose', verbose, 'Verbose mode',
                         'Print what Titta does')
        self.params['tracker'] = Param(
            tracker, valType='str', inputType='choice', categ='Basic',
            allowedVals=list(TRACKERS),
            hint=_translate('The model of the eye tracker'),
            label=_translate('Eye tracker'))
        self.params['trackerAddress'] = Param(
            trackerAddress, valType='str', inputType='single', categ='Basic',
            hint=_translate('IP address of the eye tracker, or empty to use the first one of '
                            'the model'),
            label=_translate('Eye tracker address (optional)'))
        self._param_bool('samplingRateManual', samplingRateManual, 'Manual sampling rate',
                         'Use the sampling rate below instead of Titta\'s default for the '
                         'model')
        self.params['samplingRate'] = Param(
            samplingRate, valType='code', inputType='single', categ='Basic',
            hint=_translate('Sampling rate in Hz (a rate the eye tracker supports)'),
            label=_translate('Sampling rate (Hz)'))
        self._depends('samplingRateManual', 'samplingRate')
        self.params['trackingMode'] = Param(
            trackingMode, valType='str', inputType='choice', categ='Basic',
            allowedVals=list(TRACKING_MODES),
            hint=_translate('Tracking mode (only for some eye trackers); Default keeps '
                            'Titta\'s default'),
            label=_translate('Tracking mode'))

        # --- Calibration ---
        self._param_bool('bimonocularCalibration', bimonocularCalibration,
                         'Bimonocular calibration',
                         'Calibrate the left and the right eye one after the other (Tobii '
                         'Pro Spectrum only)')
        self.params['nCalibrationTargets'] = Param(
            nCalibrationTargets, valType='str', inputType='choice', categ='Calibration',
            allowedVals=[str(n) for n in N_CALIBRATION_TARGETS],
            hint=_translate('Number of calibration targets'),
            label=_translate('Number of calibration targets'))
        self._param_bool('recordEyeImagesDuringCalibration', recordEyeImagesDuringCalibration,
                         'Record eye images during calibration',
                         'Record eye images during calibration (Spectrum and Fusion only)')
        self._param_bool('calibrationManual', calibrationManual,
                         'Manual calibration settings',
                         'Use the calibration settings below instead of Titta\'s defaults')
        self.params['calibrationDot'] = Param(
            calibrationDot, valType='str', inputType='choice', categ='Calibration',
            allowedVals=list(CALIBRATION_DOTS),
            hint=_translate('The calibration target'),
            label=_translate('Calibration dot type'))
        self.params['calibrationDotSize'] = Param(
            calibrationDotSize, valType='code', inputType='single', categ='Calibration',
            hint=_translate('Outer diameter of the calibration dot in pixels'),
            label=_translate('Calibration dot size (pixels)'))
        self._param_bool('calibrationAnimate', calibrationAnimate, 'Animate calibration',
                         'Static or animated calibration dots')
        self.params['calibrationPacingInterval'] = Param(
            calibrationPacingInterval, valType='code', inputType='single', categ='Calibration',
            hint=_translate('How long to present the target at a calibration/validation '
                            'location until samples are collected'),
            label=_translate('Calibration pacing interval (s, at least 0.8)'))
        self.params['calibrationAutoPace'] = Param(
            calibrationAutoPace, valType='str', inputType='choice', categ='Calibration',
            allowedVals=list(AUTO_PACE),
            hint=_translate('Accept all points with the space bar, semi autoaccept (accept '
                            'only the first point with the space bar), or autoaccept'),
            label=_translate('Calibration auto pace'))
        self.params['calibrationMovementDuration'] = Param(
            calibrationMovementDuration, valType='code', inputType='single',
            categ='Calibration',
            hint=_translate('Duration for the target to move from one position to the next '
                            '(0: the target jumps)'),
            label=_translate('Movement duration (s, lower is faster)'))
        for param in ('calibrationDot', 'calibrationDotSize', 'calibrationAnimate',
                      'calibrationPacingInterval', 'calibrationAutoPace',
                      'calibrationMovementDuration'):
            self._depends('calibrationManual', param)
        self._param_bool('headBoxManual', headBoxManual,
                         'Manual 3D location of the head box center',
                         'Position of the head circle in the participant setup screen')
        for axis, val in zip('XYZ', (headBoxCenterX, headBoxCenterY, headBoxCenterZ)):
            key = f'headBoxCenter{axis}'
            self.params[key] = Param(
                val, valType='code', inputType='single', categ='Calibration',
                hint=_translate(f'{axis} coordinate in the user coordinate system (UCS, mm)'),
                label=_translate(f'Head box center {axis} (mm)'))
            self._depends('headBoxManual', key)
        for key in ('bimonocularCalibration', 'recordEyeImagesDuringCalibration',
                    'calibrationManual', 'calibrationAnimate', 'headBoxManual'):
            self.params[key].categ = 'Calibration'

        # --- Operator screen ---
        self._param_bool('operatorScreen', operatorScreen, 'Operator screen',
                         'Open a second window for the operator (calibration and gaze plot)')
        self.params['operatorScreenName'] = Param(
            operatorScreenName, valType='str', inputType='single', categ='Operator screen',
            hint=_translate('Monitor in the PsychoPy Monitor Center'),
            label=_translate('Monitor name'))
        self.params['operatorScreenNr'] = Param(
            operatorScreenNr, valType='code', inputType='single', categ='Operator screen',
            hint=_translate('Screen number of the operator window'),
            label=_translate('Screen number'))
        self.params['operatorXRes'] = Param(
            operatorXRes, valType='code', inputType='single', categ='Operator screen',
            hint=_translate('Width of the operator window in pixels'),
            label=_translate('Resolution X (pixels)'))
        self.params['operatorYRes'] = Param(
            operatorYRes, valType='code', inputType='single', categ='Operator screen',
            hint=_translate('Height of the operator window in pixels'),
            label=_translate('Resolution Y (pixels)'))
        self._param_bool('operatorWaitBlanking', operatorWaitBlanking,
                         'Enable waitBlanking on operator screen',
                         'Wait for the vertical blank on the operator screen (can make '
                         'drawing there slow; the screens are flipped one after the other)')
        self.params['operatorScreen'].categ = 'Operator screen'
        self.params['operatorWaitBlanking'].categ = 'Operator screen'
        for param in ('operatorScreenName', 'operatorScreenNr', 'operatorXRes',
                      'operatorYRes', 'operatorWaitBlanking'):
            self._depends('operatorScreen', param)

        # --- Data ---
        self.params['dataFileName'] = Param(
            dataFileName, valType='code', inputType='single', categ='Data',
            hint=_translate('Path of the Titta data file without extension; by default the '
                            'name of the PsychoPy data file (.h5 next to the .csv)'),
            label=_translate('Data file name'))

        self.order = [
            'name', 'dummyMode', 'verbose', 'tracker', 'trackerAddress',
            'samplingRateManual', 'samplingRate', 'trackingMode',
            'bimonocularCalibration', 'nCalibrationTargets',
            'recordEyeImagesDuringCalibration', 'calibrationManual', 'calibrationDot',
            'calibrationDotSize', 'calibrationAnimate', 'calibrationPacingInterval',
            'calibrationAutoPace', 'calibrationMovementDuration', 'headBoxManual',
            'headBoxCenterX', 'headBoxCenterY', 'headBoxCenterZ',
            'operatorScreen', 'operatorScreenName', 'operatorScreenNr', 'operatorXRes',
            'operatorYRes', 'operatorWaitBlanking', 'dataFileName',
        ]

    def integrityCheck(self):
        # No timing to check
        from psychopy.alerts import alerttools
        alerttools.testDisabled(self)

    def writeInitCode(self, buff):
        # Begin Experiment: after the window opened, inside run()
        params = self.params
        p = {key: str(param) for key, param in params.items()}
        manual = params['calibrationManual'].val
        if params['headBoxManual'].val:
            head_box = (f"[{self._code_or_none(params['headBoxCenterX'])}, "
                        f"{self._code_or_none(params['headBoxCenterY'])}, "
                        f"{self._code_or_none(params['headBoxCenterZ'])}]")
        else:
            head_box = 'None'
        code = (
            f"# --- Titta: connect to the eye tracker ---\n"
            f"{p['name']} = {MODULE}.TittaSession(\n"
            f"    win=win,\n"
            f"    data_file_name={p['dataFileName']},\n"
            f"    tracker={p['tracker']},\n"
            f"    dummy_mode={DUMMY_MODES[params['dummyMode'].val]},\n"
            f"    verbose={p['verbose']},\n"
            f"    tracker_address={p['trackerAddress']},\n"
            f"    sampling_rate="
            f"{self._code_or_none(params['samplingRate']) if params['samplingRateManual'].val else 'None'},\n"
            f"    tracking_mode={p['trackingMode']},\n"
            f"    bimonocular_calibration={p['bimonocularCalibration']},\n"
            f"    n_calibration_targets={int(params['nCalibrationTargets'].val)},\n"
            f"    record_eye_images_during_calibration="
            f"{p['recordEyeImagesDuringCalibration']},\n"
        )
        if manual:
            code += (
                f"    calibration_dot={p['calibrationDot']},\n"
                f"    calibration_dot_size={self._code_or_none(params['calibrationDotSize'])},\n"
                f"    calibration_animate={p['calibrationAnimate']},\n"
                f"    calibration_pacing_interval="
                f"{self._code_or_none(params['calibrationPacingInterval'])},\n"
                f"    calibration_auto_pace={p['calibrationAutoPace']},\n"
                f"    calibration_movement_duration="
                f"{self._code_or_none(params['calibrationMovementDuration'])},\n"
            )
        code += f"    head_box_center={head_box},\n"
        code += f"    operator_screen={p['operatorScreen']},\n"
        if params['operatorScreen'].val:
            code += (
                f"    operator_screen_name={p['operatorScreenName']},\n"
                f"    operator_screen_nr={self._code_or_none(params['operatorScreenNr'])},\n"
                f"    operator_resolution=({self._code_or_none(params['operatorXRes'])}, "
                f"{self._code_or_none(params['operatorYRes'])}),\n"
                f"    operator_waitblanking={p['operatorWaitBlanking']},\n"
            )
        code += (
            f")\n"
            f"# at the end, also after Escape: warn when still recording, stop dummy mode\n"
            f"# and close the operator window (runAtExit: since PsychoPy 2025.1.1, not in 2024.2.4)\n"
            f"if 'runAtExit' in globals():\n"
            f"    runAtExit.append({p['name']}.close)\n"
            f"{p['name']}.connect()\n"
        )
        buff.writeIndentedLines(code)

    def writeExperimentEndCode(self, buff):
        # Older PsychoPy versions have no runAtExit (not after Escape then)
        buff.writeIndentedLines(
            f"if 'runAtExit' not in globals():\n"
            f"    {self.params['name']}.close()\n")
