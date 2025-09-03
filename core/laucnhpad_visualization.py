import asyncio
from launchpad_py import launchpad
from core.config import CONFIG
from core.state import BANDS_POS, VISUAL_SIDE_STATE_CACHE, VSTATE, ALPHA_0_100, ALPHA_100_200, ALPHA_6400_22000, ALPHA_800_1600, VSSCACHE_RIGHT_INDEX, VSSCACHE_TOP_INDEX, VSSCACHE_BOTTOM_INDEX


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
        bands_arr[-4], bands_arr[-2], bands_arr[-1])


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
        lp: launchpad.LaunchpadPro, lvl_0_100: float,
        lvl_100_200: float, lvl_800_1600: float, lvl_3200_6400: float, lvl_6400_22000: float):
    """
    Side button visualization with smooth color transitions based on bass level.
    """
    global VSTATE, ALPHA_0_100, ALPHA_100_200, ALPHA_6400_22000, ALPHA_800_1600, VISUAL_SIDE_STATE_CACHE, CONFIG

    # 1. UPDATE THE SMOOTHED VALUES using the EMA
    VSTATE.smoothed_0_100 = ALPHA_0_100 * lvl_0_100 + (1 - ALPHA_0_100) * VSTATE.smoothed_0_100
    VSTATE.smoothed_100_200 = ALPHA_100_200 * lvl_100_200 + (1 - ALPHA_100_200) * VSTATE.smoothed_100_200
    VSTATE.smoothed_800_1600 = ALPHA_800_1600 * lvl_800_1600 + (1 - ALPHA_800_1600) * VSTATE.smoothed_800_1600
    VSTATE.smoothed_3200_6400 = ALPHA_800_1600 * lvl_3200_6400 + (1 - ALPHA_800_1600) * VSTATE.smoothed_3200_6400
    VSTATE.smoothed_6400_22000 = ALPHA_6400_22000 * lvl_6400_22000 + (1 - ALPHA_6400_22000) * VSTATE.smoothed_6400_22000

    # l - left, r - right, t - top, b - bottom
    lr = lg = lb = CONFIG.colors.MIN_VAL
    rr = rg = rb = CONFIG.colors.MIN_VAL
    tr = tg = tb = CONFIG.colors.MIN_VAL
    br = bg = bb = CONFIG.colors.MIN_VAL

    # Logic for the left side
    if VSTATE.smoothed_0_100 > CONFIG.threshold.LEFT_SUB:
        start_rgb = CONFIG.colors.LEFT_START_RGB
        end_rgb = CONFIG.colors.LEFT_END_RGB
        # Using a smoothed value
        lr = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * VSTATE.smoothed_0_100)
        lg = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * VSTATE.smoothed_0_100)
        lb = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * VSTATE.smoothed_0_100)
    else:
        lr, lg, lb = CONFIG.colors.OFF_COLOR_RGB

    # Logic for the right side
    if VSTATE.smoothed_100_200 > CONFIG.threshold.RIGHT_BASS:
        start_rgb = CONFIG.colors.RIGHT_START_RGB
        end_rgb = CONFIG.colors.RIGHT_END_RGB
        # Using a smoothed value
        rr = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * VSTATE.smoothed_100_200)
        rg = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * VSTATE.smoothed_100_200)
        rb = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * VSTATE.smoothed_100_200)
    else:
        rr, rg, rb = CONFIG.colors.OFF_COLOR_RGB

    # 2. CACHING AND UPDATING LEDS

    # Left side buttons
    if CONFIG.pads.TURN_ON_LEFT_BUTTONS:
        for y in range(CONFIG.pads.LEFT_Y_RANGE[0], CONFIG.pads.LEFT_Y_RANGE[1]):
            current_color = (lr, lg, lb)
            cache_index = y - 1
            if VISUAL_SIDE_STATE_CACHE[cache_index] != current_color:
                lp.LedCtrlXY(CONFIG.pads.LEFT_X_POS, y, lr, lg, lb)
                VISUAL_SIDE_STATE_CACHE[cache_index] = current_color

    # Right side buttons
    if CONFIG.pads.TURN_ON_RIGHT_BUTTONS:
        for y in range(CONFIG.pads.RIGHT_Y_RANGE[0], CONFIG.pads.RIGHT_Y_RANGE[1]):
            current_color = (rr, rg, rb)
            cache_index = VSSCACHE_RIGHT_INDEX + (y - 1)
            if VISUAL_SIDE_STATE_CACHE[cache_index] != current_color:
                lp.LedCtrlXY(CONFIG.pads.RIGHT_X_POS, CONFIG.pads.PADS_IN_COLUMN - y + 1, rr, rg, rb)
                VISUAL_SIDE_STATE_CACHE[cache_index] = current_color

    # Top buttons
    if CONFIG.pads.TURN_ON_TOP_BUTTONS:
        # split range into left and right halves
        left_range = list(range(CONFIG.pads.TOP_X_RANGE[0], (CONFIG.pads.TOP_X_RANGE[0] + CONFIG.pads.TOP_X_RANGE[1]) // 2))
        right_range = reversed(list(range((CONFIG.pads.TOP_X_RANGE[0] + CONFIG.pads.TOP_X_RANGE[1]) // 2, CONFIG.pads.TOP_X_RANGE[1])))

        left_intensity = VSTATE.smoothed_800_1600
        right_intensity = VSTATE.smoothed_3200_6400
        thresholds = CONFIG.threshold.SIDE_HALF_THRESHOLD

        # --- LEFT (example: green-blue tones) ---
        for i, x in enumerate(left_range):
            threshold = thresholds[i % len(thresholds)]
            if left_intensity >= threshold:
                tr = int(CONFIG.colors.MAX_VAL * (0.3 * left_intensity))
                tg = int(CONFIG.colors.MAX_VAL * (0.7 * left_intensity))
                tb = int(CONFIG.colors.MAX_VAL * (0.8 * left_intensity))
            else:
                tr = tg = tb = CONFIG.colors.MIN_VAL

            current_color = (tr, tg, tb)
            cache_index = VSSCACHE_TOP_INDEX + x
            if VISUAL_SIDE_STATE_CACHE[cache_index] != current_color:
                lp.LedCtrlXY(x, CONFIG.pads.TOP_Y_POS, tr, tg, tb)
                VISUAL_SIDE_STATE_CACHE[cache_index] = current_color

        # --- RIGHT (example: purple-pink tones) ---
        for i, x in enumerate(right_range):
            threshold = thresholds[i % len(thresholds)]
            if right_intensity >= threshold:
                tr = int(CONFIG.colors.MAX_VAL * (0.8 * right_intensity))
                tg = int(CONFIG.colors.MAX_VAL * (0.3 * right_intensity))
                tb = int(CONFIG.colors.MAX_VAL * (0.7 * right_intensity))
            else:
                tr = tg = tb = CONFIG.colors.MIN_VAL

            current_color = (tr, tg, tb)
            cache_index = VSSCACHE_TOP_INDEX + x
            if VISUAL_SIDE_STATE_CACHE[cache_index] != current_color:
                lp.LedCtrlXY(x, CONFIG.pads.TOP_Y_POS, tr, tg, tb)
                VISUAL_SIDE_STATE_CACHE[cache_index] = current_color

    # Bottom buttons
    # Bottom buttons (split into left and right halves)
    if CONFIG.pads.TURN_ON_BOTTOM_BUTTONS:
        mid_range = list(range(CONFIG.pads.BOTTOM_X_RANGE[0], (CONFIG.pads.BOTTOM_X_RANGE[0] + CONFIG.pads.BOTTOM_X_RANGE[1]) // 2))
        high_range = reversed(list(range((CONFIG.pads.BOTTOM_X_RANGE[0] + CONFIG.pads.BOTTOM_X_RANGE[1]) // 2, CONFIG.pads.BOTTOM_X_RANGE[1])))

        mid_intensity = VSTATE.smoothed_3200_6400
        thresholds = CONFIG.threshold.SIDE_HALF_THRESHOLD

        for i, x in enumerate(mid_range):
            threshold = thresholds[i]
            if mid_intensity >= threshold:
                br = int(CONFIG.colors.MAX_VAL * mid_intensity)
                bg = int(CONFIG.colors.MAX_VAL * mid_intensity * 0.6)
                bb = 0
            else:
                br = bg = bb = CONFIG.colors.MIN_VAL

            current_color = (br, bg, bb)
            cache_index = VSSCACHE_BOTTOM_INDEX + x
            if VISUAL_SIDE_STATE_CACHE[cache_index] != current_color:
                lp.LedCtrlXY(x, CONFIG.pads.BOTTOM_Y_POS, br, bg, bb)
                VISUAL_SIDE_STATE_CACHE[cache_index] = current_color

        # --- RIGHT (high = hats/sibilants) ---
        high_intensity = VSTATE.smoothed_6400_22000
        thresholds = CONFIG.threshold.SIDE_HALF_THRESHOLD

        for i, x in enumerate(high_range):
            threshold = thresholds[i]
            if high_intensity >= threshold:
                br = int(CONFIG.colors.MAX_VAL * high_intensity * 0.4)
                bg = int(CONFIG.colors.MAX_VAL * high_intensity * 0.5)
                bb = int(CONFIG.colors.MAX_VAL * high_intensity)
            else:
                br = bg = bb = CONFIG.colors.MIN_VAL
            current_color = (br, bg, bb)
            cache_index = VSSCACHE_BOTTOM_INDEX + x
            if VISUAL_SIDE_STATE_CACHE[cache_index] != current_color:
                lp.LedCtrlXY(x, CONFIG.pads.BOTTOM_Y_POS, br, bg, bb)
                VISUAL_SIDE_STATE_CACHE[cache_index] = current_color
