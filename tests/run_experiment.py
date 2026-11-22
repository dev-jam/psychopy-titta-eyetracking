"""
Compile a .psyexp file and run it without a person: every keyboard check
that accepts one of the scripted keys gets that key, at most one key per
--interval seconds. Escape is never pressed unless --escape-after is given.
For tests in dummy mode, e.g. under Xvfb:

    xvfb-run -a python tests/run_experiment.py demo/titta_demo.psyexp --answer y

SPDX-License-Identifier: GPL-3.0-or-later
"""

import argparse
import runpy
import sys
import time
from pathlib import Path


class FakeKey:
    def __init__(self, name, rt):
        self.name = name
        self.value = name
        self.code = name
        self.rt = rt
        self.tDown = rt
        self.t = rt
        self.duration = 0.05

    def __eq__(self, other):
        return self.name == other

    def __ne__(self, other):
        return self.name != other

    def __hash__(self):
        return hash(self.name)


def install_fake_keyboard(answer, interval, escape_after):
    from psychopy.hardware import keyboard

    state = {'last': time.monotonic(), 'start': time.monotonic(), 'log': []}
    preferred = [answer, 'space', 'y', 'n']

    def get_keys(self, keyList=None, ignoreKeys=None, waitRelease=True, clear=True):
        now = time.monotonic()
        if escape_after is not None and now - state['start'] > escape_after:
            if keyList is None or 'escape' in keyList:
                return [FakeKey('escape', 0.0)]
        if now - state['last'] < interval:
            return []
        if keyList is None:
            key = 'space'
        else:
            keys = [k for k in preferred if k in keyList]
            if not keys:
                return []
            key = keys[0]
        if ignoreKeys and key in ignoreKeys:
            return []
        state['last'] = now
        state['log'].append(key)
        return [FakeKey(key, interval)]

    keyboard.KeyboardDevice.getKeys = get_keys
    keyboard.Keyboard.getKeys = get_keys
    return state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('psyexp')
    parser.add_argument('--answer', default='y', help='answer to y/n questions')
    parser.add_argument('--interval', type=float, default=0.4)
    parser.add_argument('--escape-after', type=float, default=None)
    parser.add_argument('--participant', default='test')
    args = parser.parse_args()

    from psychopy import plugins
    plugins.activatePlugins()
    from psychopy import experiment

    psyexp = Path(args.psyexp).resolve()
    exp = experiment.Experiment()
    exp.loadFromXML(str(psyexp))
    exp.settings.params['Show info dlg'].val = False
    exp.settings.params['Full-screen window'].val = False
    script = psyexp.with_name(psyexp.stem + '_test_run.py')
    script.write_text(exp.writeScript(target='PsychoPy'), encoding='utf-8')
    install_fake_keyboard(args.answer, args.interval, args.escape_after)
    sys.argv = [str(script)]
    try:
        runpy.run_path(str(script), run_name='__main__')
    finally:
        script.unlink()


if __name__ == '__main__':
    main()
