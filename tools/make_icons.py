"""
Make the component icons of psychopy-titta-eyetracking: an eye with a badge
per component, as SVG (`<Class>.svg`) and as PNG for each Builder theme
(`<theme>/<stem>.png` 48 px and `<theme>/<stem>@2x.png` 96 px).

Run from the repository root: python tools/make_icons.py

SPDX-License-Identifier: GPL-3.0-or-later
"""

from pathlib import Path

from PIL import Image, ImageDraw

COMPONENTS = Path(__file__).resolve().parent.parent / 'psychopy_titta_eyetracking' / 'components'

# folder: (icon stem, class name, badge)
ICONS = {
    'init': ('titta_init', 'TittaInitComponent', 'power'),
    'calibrate': ('titta_calibrate', 'TittaCalibrateComponent', 'target'),
    'start_recording': ('titta_start_recording', 'TittaStartRecordingComponent', 'record'),
    'send_message': ('titta_send_message', 'TittaSendMessageComponent', 'flag'),
    'plot_gaze': ('titta_plot_gaze', 'TittaPlotGazeComponent', 'gaze'),
    'stop_recording': ('titta_stop_recording', 'TittaStopRecordingComponent', 'stop'),
    'save_data': ('titta_save_data', 'TittaSaveDataComponent', 'save'),
}

# Color of the eye per theme; the badges have their own colors
THEMES = {
    'light': (60, 60, 60),
    'classic': (40, 70, 120),
    'dark': (230, 230, 230),
}
BADGE = {
    'power': (37, 97, 163),
    'target': (37, 97, 163),
    'record': (200, 30, 30),
    'flag': (0, 140, 70),
    'gaze': (200, 30, 30),
    'stop': (140, 140, 140),
    'save': (0, 120, 200),
}
SIZES = {'': 48, '@2x': 96}
SCALE = 8  # draw large, then reduce (anti-aliasing)


def draw_icon(size, eye_color, badge):
    n = size * SCALE
    u = n / 32  # drawing unit: the icon is 32 x 32 units
    image = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    width = round(2 * u)
    # Eye: two arcs and the iris
    d.arc((1 * u, 6 * u, 25 * u, 30 * u), 225, 315, fill=eye_color, width=width)
    d.arc((1 * u, -6 * u, 25 * u, 18 * u), 45, 135, fill=eye_color, width=width)
    d.ellipse((8.5 * u, 6.5 * u, 17.5 * u, 15.5 * u), outline=eye_color, width=width)
    d.ellipse((11.5 * u, 9.5 * u, 14.5 * u, 12.5 * u), fill=eye_color)
    # Badge, bottom right
    color = BADGE[badge] + (255,)
    x0, y0, x1, y1 = 17 * u, 17 * u, 31 * u, 31 * u
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if badge == 'record':
        d.ellipse((x0 + u, y0 + u, x1 - u, y1 - u), fill=color)
    elif badge == 'stop':
        d.rectangle((x0 + 2 * u, y0 + 2 * u, x1 - 2 * u, y1 - 2 * u), fill=color)
    elif badge == 'target':
        d.ellipse((x0 + u, y0 + u, x1 - u, y1 - u), outline=color, width=width)
        d.ellipse((cx - 1.5 * u, cy - 1.5 * u, cx + 1.5 * u, cy + 1.5 * u), fill=color)
    elif badge == 'power':
        d.arc((x0 + u, y0 + u, x1 - u, y1 - u), 300, 240, fill=color, width=width)
        d.line((cx, y0, cx, cy), fill=color, width=width)
    elif badge == 'flag':
        d.line((x0 + 2 * u, y0, x0 + 2 * u, y1), fill=color, width=width)
        d.polygon([(x0 + 3 * u, y0), (x1, y0 + 3.5 * u), (x0 + 3 * u, y0 + 7 * u)], fill=color)
    elif badge == 'gaze':
        for dx, dy in ((-3, -3), (3, -1), (-1, 3), (4, 4)):
            r = 2 * u
            d.ellipse((cx + dx * u - r, cy + dy * u - r, cx + dx * u + r, cy + dy * u + r),
                      fill=color)
    elif badge == 'save':
        d.line((cx, y0, cx, y1 - 4 * u), fill=color, width=width)
        d.polygon([(cx - 4.5 * u, y1 - 7 * u), (cx + 4.5 * u, y1 - 7 * u), (cx, y1 - 2 * u)],
                  fill=color)
        d.line((x0 + u, y1 - u, x1 - u, y1 - u), fill=color, width=width)
    return image.resize((size, size), Image.LANCZOS)


def svg_icon(badge):
    eye = '#3c3c3c'
    color = '#%02x%02x%02x' % BADGE[badge]
    badges = {
        'record': f'<circle cx="24" cy="24" r="6" fill="{color}"/>',
        'stop': f'<rect x="19" y="19" width="10" height="10" fill="{color}"/>',
        'target': (f'<circle cx="24" cy="24" r="6" fill="none" stroke="{color}" '
                   f'stroke-width="2"/><circle cx="24" cy="24" r="1.5" fill="{color}"/>'),
        'power': (f'<path d="M20.5 20 A6 6 0 1 0 27.5 20" fill="none" stroke="{color}" '
                  f'stroke-width="2"/><line x1="24" y1="17" x2="24" y2="24" '
                  f'stroke="{color}" stroke-width="2"/>'),
        'flag': (f'<line x1="19" y1="17" x2="19" y2="31" stroke="{color}" stroke-width="2"/>'
                 f'<polygon points="20,17 31,20.5 20,24" fill="{color}"/>'),
        'gaze': ''.join(f'<circle cx="{24 + dx}" cy="{24 + dy}" r="2" fill="{color}"/>'
                        for dx, dy in ((-3, -3), (3, -1), (-1, 3), (4, 4))),
        'save': (f'<line x1="24" y1="17" x2="24" y2="27" stroke="{color}" stroke-width="2"/>'
                 f'<polygon points="19.5,24 28.5,24 24,29" fill="{color}"/>'
                 f'<line x1="18" y1="30" x2="30" y2="30" stroke="{color}" stroke-width="2"/>'),
    }
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg width="100%" height="100%" viewBox="0 0 32 32" version="1.1" '
        'xmlns="http://www.w3.org/2000/svg">\n'
        f'  <path d="M2.5 12 Q13 1 23.5 12" fill="none" stroke="{eye}" stroke-width="2"/>\n'
        f'  <path d="M2.5 12 Q13 23 23.5 12" fill="none" stroke="{eye}" stroke-width="2"/>\n'
        f'  <circle cx="13" cy="11" r="3.5" fill="none" stroke="{eye}" stroke-width="2"/>\n'
        f'  <circle cx="13" cy="11" r="1.5" fill="{eye}"/>\n'
        f'  {badges[badge]}\n'
        '</svg>\n'
    )


def main():
    for folder, (stem, class_name, badge) in ICONS.items():
        path = COMPONENTS / folder
        (path / f'{class_name}.svg').write_text(svg_icon(badge), encoding='utf-8')
        for theme, eye_color in THEMES.items():
            (path / theme).mkdir(exist_ok=True)
            for suffix, size in SIZES.items():
                draw_icon(size, eye_color + (255,), badge).save(path / theme / f'{stem}{suffix}.png')


if __name__ == '__main__':
    main()
