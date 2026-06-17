"""Device submodule — exports all custom MIoT device/status classes."""

from .fan_p33 import FanP33, FanStatusP33, OperationModeFanP33
from .fan_p39 import FanP39, FanStatusP39, OperationModeFanP39
from .fan_p70 import FanP70, FanStatusP70, OperationModeFanP70
from .fan_p76 import FanP76, FanStatusP76, OperationModeFanP76
from .fan_za5 import FanStatusZA5, FanZA5, OperationModeFanZA5

__all__ = [
    "OperationModeFanZA5",
    "FanStatusZA5",
    "FanZA5",
    "OperationModeFanP33",
    "FanStatusP33",
    "FanP33",
    "OperationModeFanP39",
    "FanStatusP39",
    "FanP39",
    "OperationModeFanP76",
    "FanStatusP76",
    "FanP76",
    "OperationModeFanP70",
    "FanStatusP70",
    "FanP70",
]
