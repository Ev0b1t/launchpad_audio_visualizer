import asyncio
from launchpad_py import launchpad
from core.config import CONFIG
from core.state import BANDS_POS, VISUAL_STATE_CACHE


class VisualizerState:
    def __init__(self):
        self.smoothed_sub = 0.0
        self.smoothed_bass = 0.0
        self.smoothed_high = 0.0
        self.smoothed_mid_high = 0.0
        self.smoothed_low_mid_high = 0.0


VSTATE = VisualizerState()

# Smoothing coefficients
ALPHA_SUB = 0.8
ALPHA_BASS = 0.8
ALPHA_HIGH = 0.3
ALPHA_MID_HIGH = 0.4
ALPHA_LOW_MID_HIGH = 0.3


async def visualize_audio_bands(lp: launchpad.LaunchpadPro, bands_arr):
    global VSTATE
    tasks = []

    for pad_x, val in enumerate(bands_arr):
        new_level = round(val * CONFIG.pads.PADS_IN_COLUMN)

        if len(BANDS_POS) <= pad_x:
            BANDS_POS.append(0)

        old_level = BANDS_POS[pad_x]

        if new_level != old_level:
            # only changed buttons
            if new_level > old_level:
                level_from = old_level
                level_to = new_level
                level_side = 1
                # only new buttons
            else:
                level_from = new_level
                level_to = old_level
                level_side = -1
                # lights off other
            for y in range(level_from + 1, level_to + 1):
                pad_y = CONFIG.pads.PADS_IN_COLUMN - y + 1
                tasks.append(_visualize_pad_button(lp, pad_x, pad_y, level_side=level_side))

            BANDS_POS[pad_x] = new_level

    if tasks:
        await asyncio.gather(*tasks)

    await _visualize_side_buttons(
        lp, bands_arr[0], bands_arr[1],
        bands_arr[-4], bands_arr[-3], bands_arr[-2])


async def _visualize_pad_button(
        lp: launchpad.LaunchpadPro,
        pad_x: int, pad_y: int, level_side: int = 1):
    ''' check range of the pads and set the apporpriate color '''

    r = g = b = 0
    # check that we need to growth
    if level_side > -1:
        # 8,7,6 of y is ANOTHER, 5,4,3 of y is ANOTHER and 2,1 of y is ANOTHER
        if 6 <= pad_y <= 8:
            r, g, b = CONFIG.colors.RGB_LOW
        elif 3 <= pad_y <= 5:
            r, g, b = CONFIG.colors.RGB_MID
        else:
            r, g, b = CONFIG.colors.RGB_HIGH
    lp.LedCtrlXY(pad_x, pad_y, r, g, b)


async def _visualize_side_buttons(
        lp: launchpad.LaunchpadPro, sub_level: float,
        bass_level: float, low_mid_high: float, mid_high_level: float, high_level: float):
    """
    Side button visualization with smooth color transitions based on bass level.
    """
    global VSTATE, ALPHA_SUB, ALPHA_BASS, ALPHA_HIGH, ALPHA_MID_HIGH, VISUAL_STATE_CACHE

    # 1. UPDATE THE SMOOTHED VALUES using the EMA
    VSTATE.smoothed_sub = ALPHA_SUB * sub_level + (1 - ALPHA_SUB) * VSTATE.smoothed_sub
    VSTATE.smoothed_bass = ALPHA_BASS * bass_level + (1 - ALPHA_BASS) * VSTATE.smoothed_bass
    VSTATE.smoothed_high = ALPHA_HIGH * high_level + (1 - ALPHA_HIGH) * VSTATE.smoothed_high
    VSTATE.smoothed_mid_high = ALPHA_MID_HIGH * mid_high_level + (1 - ALPHA_MID_HIGH) * VSTATE.smoothed_mid_high
    VSTATE.smoothed_low_mid_high = ALPHA_MID_HIGH * low_mid_high + (1 - ALPHA_LOW_MID_HIGH) * VSTATE.smoothed_low_mid_high

    lx = 9
    rx = 8
    ty = 0
    by = 9

    lr = lg = lb = 0
    rr = rg = rb = 0
    tr = tg = tb = 0
    br = bg = bb = 0

    intensity = sub_level ** 1.1

    if sub_level > 0.3:
        start_color = (0, 0, 63)
        end_color = (63, 0, 0)
        lr = int(start_color[0] + (end_color[0] - start_color[0]) * intensity)
        lg = int(start_color[1] + (end_color[1] - start_color[1]) * intensity)
        lb = int(start_color[2] + (end_color[2] - start_color[2]) * intensity)

    if bass_level > 0.5:
        start_color = (63, 0, 0)
        end_color = (0, 0, 63)
        rr = int(start_color[0] + (end_color[0] - start_color[0]) * intensity)
        rg = int(start_color[1] + (end_color[1] - start_color[1]) * intensity)
        rb = int(start_color[2] + (end_color[2] - start_color[2]) * intensity)

    # Control the upper (green) and lower (orange) buttons
    # Top buttons (green) - for bass
    if VSTATE.smoothed_bass > 0.9 and VSTATE.smoothed_sub > 0.9 and sub_level > 0.9 and bass_level > 0.9:
        tr, tg, tb = 0, 63, 0
    else:
        tr, tg, tb = 0, int(VSTATE.smoothed_bass * 63), 0

    # Bottom buttons (orange) - for snares
    if VSTATE.smoothed_high > 0.7 and VSTATE.smoothed_mid_high > 0.7:
        br, bg, bb = 63, 20, 0
    else:
        smoothed_combined = (VSTATE.smoothed_high + VSTATE.smoothed_mid_high) / 2
        br, bg, bb = int(smoothed_combined * 63), int(smoothed_combined * 20), 0

    #2. CACHING AND UPDATING LEDS

    # Left side buttons
    for y in range(1, 9):
        current_color = (lr, lg, lb)
        cache_index = y - 1 # 0 - 7
        if VISUAL_STATE_CACHE[cache_index] != current_color:
            lp.LedCtrlXY(lx, y, lr, lg, lb)
            VISUAL_STATE_CACHE[cache_index] = current_color

    # Right side buttons
    for y in range(1, 9):
        current_color = (rr, rg, rb)
        cache_index = 8 + (y - 1) # 8 - 15
        if VISUAL_STATE_CACHE[cache_index] != current_color:
            lp.LedCtrlXY(rx, CONFIG.pads.PADS_IN_COLUMN - y + 1, rr, rg, rb)
            VISUAL_STATE_CACHE[cache_index] = current_color

    # Top buttons
    for x in range(0, 8):
        current_color = (tr, tg, tb)
        cache_index = 16 + x # 16 - 23
        if VISUAL_STATE_CACHE[cache_index] != current_color:
            lp.LedCtrlXY(x, ty, tr, tg, tb)
            VISUAL_STATE_CACHE[cache_index] = current_color

    # Bottom buttons
    for x in range(0, 8):
        current_color = (br, bg, bb)
        cache_index = 24 + x # 24 - 31
        if VISUAL_STATE_CACHE[cache_index] != current_color:
            lp.LedCtrlXY(x, by, br, bg, bb)
            VISUAL_STATE_CACHE[cache_index] = current_color
