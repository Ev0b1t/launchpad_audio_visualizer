# Global variables which will be using at the runtime moment
from datetime import datetime, timedelta
from core.config import CONFIG
from utils.logger import logger

BANDS_POS = []

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
STATE_RESETTED_COUNTDOWN = timedelta(seconds=2)
STATE_RESETTED_DATETIME = datetime.now() + STATE_RESETTED_COUNTDOWN

def reset_state():
    global BANDS_POS, VISUAL_SIDE_STATE_CACHE, STATE_RESETTED, STATE_RESETTED_DATETIME, VSTATE

    if STATE_RESETTED:
        logger.debug("State is already resetted.")
        return False

    if STATE_RESETTED_DATETIME > datetime.now():
        logger.debug("State not resetted because it was resetted less than %s seconds ago", STATE_RESETTED_COUNTDOWN.total_seconds())
        return False

    logger.info("Resetting state...")
    BANDS_POS = []
    VSTATE = VisualizerState()
    VISUAL_SIDE_STATE_CACHE = [(0, 0, 0) for _ in VISUAL_SIDE_STATE_CACHE]

    STATE_RESETTED = True
    STATE_RESETTED_DATETIME = datetime.now() + STATE_RESETTED_COUNTDOWN

    # TODO: change from config to constants
    logger.debug("Resetting state...")
    CONFIG.bands.FAST = [0.0] * len(CONFIG.bands.FAST)
    CONFIG.bands.SLOW = [0.0] * len(CONFIG.bands.SLOW)

    logger.info("State resetted.")
    return True