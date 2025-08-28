from dataclasses import dataclass, field
from functools import cached_property

# =====================
# CONFIG DATACLASSES
# =====================

@dataclass(frozen=True)
class PadsConfig:
    # Pads layout
    PADS_IN_COLUMN: int = 8

@dataclass(frozen=True)
class ColorConfig:
    # Colors when audio will play
    MAX_VAL: int = 63  # max value
    MIN_VAL: int = 0   # min value

    RGB_LOW = (MIN_VAL, MIN_VAL, MAX_VAL)
    RGB_MID = (MAX_VAL, MAX_VAL, MAX_VAL)
    RGB_HIGH = (MAX_VAL, MIN_VAL, MIN_VAL)

@dataclass(frozen=True)
class EmaConfig:
    # EMA for monitoring peaks
    SMOOTHING: float = 0.1
    MIN_PEAK: float = 0.01

@dataclass(frozen=True)
class BandsConfig:
    # Frequency bands converter
    MAX_FQ: int = 22050
    MIN_FQ: int = 0
    RANGE: list[tuple[int, int]] = field(init=False)
    EMAS: list[float] = field(init=False)

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
        object.__setattr__(self, 'EMAS', [0.0] * len(self.RANGE))


@dataclass(frozen=True)
class ThresholdConfig:
    # Threshold to trigger LED updates
    VAL: float = 0.9


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


# =====================
# SINGLETON INSTANCE
# =====================

CONFIG = Config()