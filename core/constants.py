
# CONSTANTS
# pads
PADS_IN_COLUMN = 8
FIRST_PADS_LINE_X = 0

# colors when audio will play
# colr max value and min value
CMXV = 63
CMNV = 0
RGB_LOW = (CMNV, CMNV, CMXV)
RGB_MID = tuple([CMXV for i in range(3)])
RGB_HIGH = (CMXV, CMNV, CMNV)

# GENERAL CONTAINER TO MONITORING and UPDATEING LEDS
BANDS_POS = []

PEAK_EMA = 1.0
EMA_SMOOTHING = 0.1

# GENERAL CONTAINER TO MONITORING and UPDATEING LEDS
BANDS_POS = []

# bands conveter
BANDS_MAX = 22050
BANDS_RANGE = [
    (0, 100),
    (100, 200),
    (200, 400),
    (400, 800),
    (800, 1600),
    (1600, 3200),
    (3200, 6400),
    (6400, BANDS_MAX) # Air
]
BANDS_PARTS = [((j - i) / BANDS_MAX) for i, j in BANDS_RANGE]

BANDS_EMA_PEAKS = [1.0] * len(BANDS_RANGE)
