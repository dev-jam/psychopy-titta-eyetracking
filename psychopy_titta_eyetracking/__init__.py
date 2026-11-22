# Copyright (C) 2026 Bob Rosbag <mail@bobrosbag.nl>, Diederick C. Niehorster, Marcus Nyström
# SPDX-License-Identifier: GPL-3.0-or-later

"""PsychoPy plugin for Tobii eye trackers through Titta.

The Builder components write calls to `TittaSession` (in `session.py`); the
same class can be used in Coder scripts. This module only imports PsychoPy
and Titta when a session is made, so that loading the plugin stays cheap.
"""

from importlib.metadata import PackageNotFoundError, version

# The name of the distribution, also stored in .psyexp files as the plugin
# of the components
DISTRIBUTION = 'psychopy-titta-eyetracking'

try:
    __version__ = version(DISTRIBUTION)
except PackageNotFoundError:
    # Running from a source folder that is not installed
    __version__ = 'unknown'

__all__ = ['TittaSession', 'TittaError', 'TittaMessage', 'TittaGazePlot',
           'get_session', '__version__']


def __getattr__(name):
    # Import session.py only when it is used (PEP 562)
    if name in ('TittaSession', 'TittaError', 'TittaMessage', 'TittaGazePlot', 'get_session'):
        from . import session
        return getattr(session, name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
