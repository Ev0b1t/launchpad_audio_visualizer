from launchpad_py import launchpad
from core.constants import *


async def visualize_audio_bands(lp: launchpad.LaunchpadPro, bands_arr):
    for pad_x, val in enumerate(bands_arr):
        new_level = round(val * PADS_IN_COLUMN)

        if len(BANDS_POS) <= pad_x:
            BANDS_POS.append(0)

        old_level = BANDS_POS[pad_x]

        if new_level > old_level:
            # up
            for y in range(old_level + 1, new_level + 1):
                pad_y = PADS_IN_COLUMN - y + 1
                await _visualize_pad_button(lp, pad_x, pad_y)

        elif new_level < old_level:
            # down
            for y in range(new_level + 1, old_level + 1):
                pad_y = PADS_IN_COLUMN - y + 1
                await _visualize_pad_button(lp, pad_x, pad_y, level_side=-1)

        # update the curr value
        BANDS_POS[pad_x] = new_level

    # visualize side buttons
    await _visualize_side_buttons(lp, bands_arr[0], bands_arr[1])

async def _visualize_pad_button(
        lp: launchpad.LaunchpadPro,
        pad_x: int, pad_y: int, level_side: int = 1):
    ''' check range of the pads and set the apporpriate color '''

    r = g = b = 0
    # check that we need to growth
    if level_side > -1:
        # 8,7,6 of y is ANOTHER, 5,4,3 of y is ANOTHER and 2,1 of y is ANOTHER
        if 6 <= pad_y <= 8:
            r, g, b = RGB_LOW
        elif 3 <= pad_y <= 5:
            r, g, b = RGB_MID
        else:
            r, g, b = RGB_HIGH
    lp.LedCtrlXY(pad_x, pad_y, r, g, b)


async def _visualize_side_buttons(lp: launchpad.LaunchpadPro, sub_level: float, bass_level: float):
    """
    Side button visualization with smooth color transitions based on bass level.
    """
    left_x = 9
    right_x = 8
    lr = lg = lb = 0
    rr = rg = rb = 0

    intensity = sub_level ** 1.1

    # TODO: different modes automatically
    # for ex. together or unique

    if sub_level > 0.3:
        # Interpolate color from a start color to an end color
        start_color = (0, 0, 63)
        end_color = (63, 0, 0)

        # Scale sub level to a 0-1 range for a color gradient.
        # Use a power function to make it more sensitive to strong bass hits.
        lr = int(start_color[0] + (end_color[0] - start_color[0]) * intensity)
        lg = int(start_color[1] + (end_color[1] - start_color[1]) * intensity)
        lb = int(start_color[2] + (end_color[2] - start_color[2]) * intensity)

    if bass_level > 0.5:
        # Interpolate color from a start color to an end color
        start_color = (63, 0, 0)
        end_color = (0, 0, 63)

        # Scale bass_level to a 0-1 range for a color gradient.
        # Use a power function to make it more sensitive to strong bass hits.
        rr = int(start_color[0] + (end_color[0] - start_color[0]) * intensity)
        rg = int(start_color[1] + (end_color[1] - start_color[1]) * intensity)
        rb = int(start_color[2] + (end_color[2] - start_color[2]) * intensity)

    # left
    for y in range(1, 9):
        lp.LedCtrlXY(left_x, y, lr, lg, lb)

    # right
    for y in range(1, 9):
        lp.LedCtrlXY(right_x, PADS_IN_COLUMN - y + 1, rr, rg, rb)