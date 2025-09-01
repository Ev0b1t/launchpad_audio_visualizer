# Global variables which will be using at the runtime moment

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