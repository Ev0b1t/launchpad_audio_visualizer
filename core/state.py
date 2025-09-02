# Global variables which will be using at the runtime moment
from datetime import datetime, timedelta
from utils.logger import logger

BANDS_POS = []
EMA_GLOBAL_PEAK = 1.0

# Smoothing coefficients
ALPHA_SUB = 0.8
ALPHA_BASS = 0.8
ALPHA_HIGH = 0.3
ALPHA_MID_HIGH = 0.4
ALPHA_LOW_MID_HIGH = 0.3

# state of side buttons
class VisualizerState:
    def __init__(self):
        self.smoothed_sub = 0.0
        self.smoothed_bass = 0.0
        self.smoothed_high = 0.0
        self.smoothed_mid_high = 0.0
        self.smoothed_low_mid_high = 0.0


VSTATE = VisualizerState()

VISUAL_SIDE_STATE_CACHE = [(0, 0, 0) for _ in range(32)]
VSSCACHE_LEFT_INDEX = 0
VSSCACHE_RIGHT_INDEX = 8
VSSCACHE_TOP_INDEX = 16
VSSCACHE_BOTTOM_INDEX = 24

STATE_RESETTED = True
STATE_RESETTED_DATETIME = datetime.now()
STATE_RESETTED_COUNTDOWN = timedelta(seconds=4)

def reset_state():
    global BANDS_POS, EMA_GLOBAL_PEAK, VSTATE, VISUAL_SIDE_STATE_CACHE, STATE_RESETTED, STATE_RESETTED_DATETIME

    if STATE_RESETTED:
        return False

    if STATE_RESETTED_DATETIME > datetime.now() - STATE_RESETTED_COUNTDOWN:
        logger.debug("State not resetted because it was resetted less than %s seconds ago", STATE_RESETTED_COUNTDOWN.total_seconds())
        return False

    logger.debug("Resetting state...")
    BANDS_POS.clear()
    EMA_GLOBAL_PEAK = 1.0
    VSTATE = VisualizerState()
    VISUAL_SIDE_STATE_CACHE = [(0, 0, 0) for _ in VISUAL_SIDE_STATE_CACHE]
    STATE_RESETTED = True
    STATE_RESETTED_DATETIME = datetime.now()
    return True