from dataclasses import dataclass, field
from functools import cached_property
from datetime import timedelta

# =====================
# CONFIG DATACLASSES
# =====================

# dataclass for capture audio channels, monitors etc
@dataclass(frozen=True)
class AudioConfig:
    MONITOR_SRC: str = 'alsa_output.pci-0000_00_1f.3.analog-stereo.monitor'
    FORMAT_AUDIO_CARD: str = "pulse"
    CODEC: str = "pcm_f32le"
    RAW_FORMAT: str = "f32le"
    CHANNELS: int = 2
    SAMPLERATE: int = 44100
    OUTPUT: str = "pipe:1"
    CHUNK_SIZE: int = 1024 * 1
    FLUSH_PACKETS: int = 0
    BLOCK_SIZE: int = 65536

    SAMPLE_WIDTH: int = 4 # pcm 32 -> 4 bytes

@dataclass(frozen=True)
class PadsConfig:
    # layout
    PADS_IN_COLUMN: int = 8
    PADS_IN_ROW: int = 7

    # start positions
    LEFT_X_POS: int = 9
    RIGHT_X_POS: int = 8
    TOP_Y_POS: int = 0
    BOTTOM_Y_POS: int = 9

    # RGB low, mid, high has different colors
    LOW_START_Y_POS = 6
    LOW_END_Y_POS = 8
    MID_START_Y_POS = 3
    MID_END_Y_POS = 5
    HIGH_START_Y_POS = 1
    HIGH_END_Y_POS = 2

    # Range of side buttons (left, top, right, bottom)
    TOP_X_RANGE = (0, 8)
    BOTTOM_X_RANGE = (0, 8)
    LEFT_Y_RANGE = (1, 9)
    RIGHT_Y_RANGE = (1, 9)

    TURN_ON_TOP_BUTTONS: bool = True
    TURN_ON_BOTTOM_BUTTONS: bool = True
    TURN_ON_LEFT_BUTTONS: bool = True
    TURN_ON_RIGHT_BUTTONS: bool = True

@dataclass(frozen=True)
class ColorConfig:
    # Colors when audio will play
    MAX_VAL: int = 63  # max value
    MIN_VAL: int = 0   # min value

    # Central pads color (the bands)
    RGB_LOW = (MIN_VAL, MAX_VAL, MAX_VAL // 2)
    RGB_MID = (MIN_VAL, MAX_VAL, MAX_VAL // 2)
    RGB_HIGH = (MIN_VAL, MAX_VAL, MAX_VAL // 2)

    # Side buttons color
    TOP_RGB = (MIN_VAL, MIN_VAL, MAX_VAL)
    BOTTOM_RGB = (MAX_VAL // 2, MAX_VAL // 2, MAX_VAL // 2)

    # start and end colors (gradient)
    RIGHT_START_RGB = (MAX_VAL, MIN_VAL, MIN_VAL)
    RIGHT_END_RGB = (MIN_VAL, MIN_VAL, MAX_VAL)

    LEFT_START_RGB = (MIN_VAL, MIN_VAL, MAX_VAL)
    LEFT_END_RGB = (MAX_VAL, MIN_VAL, MIN_VAL)

    # top and bottom has dynamic end colors

    OFF_COLOR_RGB = (MIN_VAL, MIN_VAL, MIN_VAL)

@dataclass(frozen=True)
class EmaConfig:
    # EMA for monitoring peaks
    FAST_SMOOTHING: float = 0.8
    SLOW_SMOOTHING: float = 0.05

@dataclass(frozen=True)
class BandsConfig:
    # Frequency bands converter
    MAX_FQ: int = 22050
    MIN_FQ: int = 0
    RANGE: list[tuple[int, int]] = field(init=False)

    # TODO: change from config to constants
    FAST: list[float] = field(init=False)   # fast EMA values
    SLOW: list[float] = field(init=False)   # slow EMA values

    def __post_init__(self):
        object.__setattr__(self, 'RANGE', [
                (0, 100),
                (100, 200),
                (200, 400),
                (400, 800),
                (800, 1600),
                (1600, 3200),
                (3200, 6400),
                (6400, 22050)
            ]
        )
        object.__setattr__(self, 'FAST', [0.0] * len(self.RANGE))
        object.__setattr__(self, 'SLOW', [0.0] * len(self.RANGE))

@dataclass(frozen=True)
class ThresholdConfig:
    # Threshold to trigger LED updates
    LEFT_SUB: float = 0.3
    RIGHT_BASS: float = 0.5
    TOP_BASS: float = 0.9
    TOP_SUB: float = 0.9
    BOTTOM_HIGH: float = 0.7
    BOTTOM_MID_HIGH: float = 0.7
    LOW_MID_HIGH: float = 0.7

    SIDE_HALF_THRESHOLD: list[float] = field(init=False)

    PAUSE_THRESHOLD_TO_RESET_STATE: timedelta = timedelta(seconds=0.25)

    def __post_init__(self):
        object.__setattr__(self, 'SIDE_HALF_THRESHOLD', [0.2, 0.3, 0.6, 0.7])


# =====================
# INITIALIZE CONFIG
# =====================
class Config:
    """Central config object returning initialized frozen dataclass instances"""

    @cached_property
    def pads(self) -> PadsConfig:
        return PadsConfig()

    @cached_property
    def colors(self) -> ColorConfig:
        return ColorConfig()

    @cached_property
    def ema(self) -> EmaConfig:
        return EmaConfig()

    @cached_property
    def bands(self) -> BandsConfig:
        return BandsConfig()

    @cached_property
    def threshold(self) -> ThresholdConfig:
        return ThresholdConfig()

    @cached_property
    def audio(self) -> AudioConfig:
        return AudioConfig()


# =====================
# SINGLETON INSTANCE
# =====================

CONFIG = Config()
