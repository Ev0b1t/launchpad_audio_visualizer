# Global variables which will be using at the runtime moment
from datetime import datetime, timedelta
from core.config import CONFIG
from utils.logger import logger

BANDS_POS = []

# Smoothing coefficients
ALPHA_0_100 = 0.8
ALPHA_100_200 = 0.8
ALPHA_6400_22000 = 0.3
ALPHA_800_1600 = 0.4
ALPHA_800_1600 = 0.3

# state of side buttons
class VisualizerState:
    def __init__(self):
        self.smoothed_0_100 = 0.0
        self.smoothed_100_200 = 0.0
        self.smoothed_6400_22000 = 0.0
        self.smoothed_3200_6400 = 0.0
        self.smoothed_800_1600 = 0.0


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