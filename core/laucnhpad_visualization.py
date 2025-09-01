import asyncio
from launchpad_py import launchpad
from core.config import CONFIG
from core.state import BANDS_POS, VISUAL_SIDE_STATE_CACHE, VSTATE, ALPHA_SUB, ALPHA_BASS, ALPHA_HIGH, ALPHA_MID_HIGH, ALPHA_LOW_MID_HIGH, VSSCACHE_RIGHT_INDEX, VSSCACHE_TOP_INDEX, VSSCACHE_BOTTOM_INDEX


async def visualize_audio_bands(lp: launchpad.LaunchpadPro, bands_arr):
    global VSTATE, BANDS_POS, CONFIG
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
    global VISUAL_PAD_STATE_CACHE, CONFIG

    r = g = b = CONFIG.colors.MIN_VAL

    # check that we need to growth
    if level_side > -1:
        if CONFIG.pads.LOW_START_Y_POS <= pad_y <= CONFIG.pads.LOW_END_Y_POS:
            r, g, b = CONFIG.colors.RGB_LOW
        elif CONFIG.pads.MID_START_Y_POS <= pad_y <= CONFIG.pads.MID_END_Y_POS:
            r, g, b = CONFIG.colors.RGB_MID
        elif CONFIG.pads.HIGH_START_Y_POS <= pad_y <= CONFIG.pads.HIGH_END_Y_POS:
            r, g, b = CONFIG.colors.RGB_HIGH

    lp.LedCtrlXY(pad_x, pad_y, r, g, b)


async def _visualize_side_buttons(
        lp: launchpad.LaunchpadPro, sub_level: float,
        bass_level: float, low_mid_high: float, mid_high_level: float, high_level: float):
    """
    Side button visualization with smooth color transitions based on bass level.
    """
    global VSTATE, ALPHA_SUB, ALPHA_BASS, ALPHA_HIGH, ALPHA_MID_HIGH, VISUAL_SIDE_STATE_CACHE, CONFIG

    # 1. UPDATE THE SMOOTHED VALUES using the EMA
    VSTATE.smoothed_sub = ALPHA_SUB * sub_level + (1 - ALPHA_SUB) * VSTATE.smoothed_sub
    VSTATE.smoothed_bass = ALPHA_BASS * bass_level + (1 - ALPHA_BASS) * VSTATE.smoothed_bass
    VSTATE.smoothed_high = ALPHA_HIGH * high_level + (1 - ALPHA_HIGH) * VSTATE.smoothed_high
    VSTATE.smoothed_mid_high = ALPHA_MID_HIGH * mid_high_level + (1 - ALPHA_MID_HIGH) * VSTATE.smoothed_mid_high
    VSTATE.smoothed_low_mid_high = ALPHA_MID_HIGH * low_mid_high + (1 - ALPHA_LOW_MID_HIGH) * VSTATE.smoothed_low_mid_high

    # l - left, r - right, t - top, b - bottom
    lr = lg = lb = CONFIG.colors.MIN_VAL
    rr = rg = rb = CONFIG.colors.MIN_VAL
    tr = tg = tb = CONFIG.colors.MIN_VAL
    br = bg = bb = CONFIG.colors.MIN_VAL

    # Logic for the left side
    if VSTATE.smoothed_sub > CONFIG.threshold.LEFT_SUB:
        start_rgb = CONFIG.colors.LEFT_START_RGB
        end_rgb = CONFIG.colors.LEFT_END_RGB
        # Using a smoothed value
        lr = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * VSTATE.smoothed_sub)
        lg = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * VSTATE.smoothed_sub)
        lb = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * VSTATE.smoothed_sub)
    else:
        lr, lg, lb = CONFIG.colors.OFF_COLOR_RGB

    # Logic for the right side
    if VSTATE.smoothed_bass > CONFIG.threshold.RIGHT_BASS:
        start_rgb = CONFIG.colors.RIGHT_START_RGB
        end_rgb = CONFIG.colors.RIGHT_END_RGB
        # Using a smoothed value
        rr = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * VSTATE.smoothed_bass)
        rg = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * VSTATE.smoothed_bass)
        rb = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * VSTATE.smoothed_bass)
    else:
        rr, rg, rb = CONFIG.colors.OFF_COLOR_RGB

    # Control the upper (green) and lower (orange) buttons
    # Top buttons (green) - for bass
    if VSTATE.smoothed_bass > CONFIG.threshold.TOP_BASS and VSTATE.smoothed_sub > CONFIG.threshold.TOP_SUB:
        tr, tg, tb = CONFIG.colors.TOP_RGB
    else:
        tr, tg, tb = CONFIG.colors.MIN_VAL, int(VSTATE.smoothed_bass * CONFIG.colors.MAX_VAL), CONFIG.colors.MIN_VAL

    # Bottom buttons (orange) - for snares
    if VSTATE.smoothed_high > CONFIG.threshold.BOTTOM_HIGH and VSTATE.smoothed_mid_high > CONFIG.threshold.BOTTOM_MID_HIGH:
        br, bg, bb = CONFIG.colors.BOTTOM_RGB
    else:
        smoothed_combined = (VSTATE.smoothed_high + VSTATE.smoothed_mid_high) / 2
        br, bg, bb = int(smoothed_combined * CONFIG.colors.MAX_VAL), int(smoothed_combined * CONFIG.colors.MAX_VAL), CONFIG.colors.MIN_VAL

    # 2. CACHING AND UPDATING LEDS

    # Left side buttons
    for y in range(CONFIG.pads.LEFT_Y_RANGE[0], CONFIG.pads.LEFT_Y_RANGE[1]):
        current_color = (lr, lg, lb)
        cache_index = y - 1 # 0 - 7
        if VISUAL_SIDE_STATE_CACHE[cache_index] != current_color:
            lp.LedCtrlXY(CONFIG.pads.LEFT_X_POS, y, lr, lg, lb)
            VISUAL_SIDE_STATE_CACHE[cache_index] = current_color

    # Right side buttons
    for y in range(CONFIG.pads.RIGHT_Y_RANGE[0], CONFIG.pads.RIGHT_Y_RANGE[1]):
        current_color = (rr, rg, rb)
        cache_index = VSSCACHE_RIGHT_INDEX + (y - 1) # 8 - 15
        if VISUAL_SIDE_STATE_CACHE[cache_index] != current_color:
            lp.LedCtrlXY(CONFIG.pads.RIGHT_X_POS, CONFIG.pads.PADS_IN_COLUMN - y + 1, rr, rg, rb)
            VISUAL_SIDE_STATE_CACHE[cache_index] = current_color

    # Top buttons
    for x in range(CONFIG.pads.TOP_X_RANGE[0], CONFIG.pads.TOP_X_RANGE[1]):
        current_color = (tr, tg, tb)
        cache_index = VSSCACHE_TOP_INDEX + x # 16 - 23
        if VISUAL_SIDE_STATE_CACHE[cache_index] != current_color:
            lp.LedCtrlXY(x, CONFIG.pads.TOP_Y_POS, tr, tg, tb)
            VISUAL_SIDE_STATE_CACHE[cache_index] = current_color

    # Bottom buttons
    for x in range(CONFIG.pads.BOTTOM_X_RANGE[0], CONFIG.pads.BOTTOM_X_RANGE[1]):
        current_color = (br, bg, bb)
        cache_index = VSSCACHE_BOTTOM_INDEX + x # 24 - 31
        if VISUAL_SIDE_STATE_CACHE[cache_index] != current_color:
            lp.LedCtrlXY(x, CONFIG.pads.BOTTOM_Y_POS, br, bg, bb)
            VISUAL_SIDE_STATE_CACHE[cache_index] = current_color
