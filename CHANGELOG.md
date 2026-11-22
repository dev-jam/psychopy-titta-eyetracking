# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-11-22

- changed: Titta Plot Gaze shows the gaze on the stimulus screen by default (one screen); the operator display is off by default
- changelog: links to the versions

## [0.2.0] - 2026-11-22

- changed: Titta Plot Gaze is a timed component that shows the gaze in real time while it runs (e.g. during a stimulus), on the operator screen as a copy of the stimulus screen with the gaze on top (new setting *Operator display background*: copy every frame, at start, or none) and/or on the stimulus screen; it no longer waits for a key itself (settings *Response keys*, *Timeout* and *When* removed). Plot gaze on operator display is on by default
- demo: the gaze is shown during the stimulus, as in the OpenSesame demo (no separate gaze Routine)

## [0.1.0] - 2026-11-22

- first version: Builder components Titta Init, Titta Calibrate, Titta Start Recording, Titta Send Message, Titta Plot Gaze, Titta Stop Recording and Titta Save Data, ported from opensesame-plugin-titta_eyetracking 7.1.1 (based on Titta's demo `read_me.py`)
- `TittaSession` for Code components and Coder scripts
- demo experiment `demo/titta_demo.psyexp` (the demo of the OpenSesame plugin)

[Unreleased]: https://github.com/dev-jam/psychopy-titta-eyetracking/compare/0.2.1...HEAD
[0.2.1]: https://github.com/dev-jam/psychopy-titta-eyetracking/compare/0.2.0...0.2.1
[0.2.0]: https://github.com/dev-jam/psychopy-titta-eyetracking/compare/0.1.0...0.2.0
[0.1.0]: https://github.com/dev-jam/psychopy-titta-eyetracking/releases/tag/0.1.0
