"""MIoT device classes for Xiaomi Fan P39 (dmaker.fan.p39)."""

from enum import Enum
from typing import Any

from miio.fan_common import FanException
from miio.fan_common import MoveDirection as FanMoveDirection
from miio.miot_device import DeviceStatus, MiotDevice

MODEL_FAN_P39 = "dmaker.fan.p39"


def _filter_request_fields(req):
    """Return only the parts that belong to the request."""
    return {k: v for k, v in req.items() if k in ["did", "siid", "piid"]}


class OperationModeFanP39(Enum):
    Normal = 0
    Nature = 1
    Sleep = 2


class FanStatusP39(DeviceStatus):
    """Container for status reports for FanP39."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    @property
    def child_lock(self) -> bool:
        return self.data["child_lock"]

    @property
    def fan_level(self) -> int:
        return self.data["fan_level"]

    @property
    def fan_speed(self) -> int:
        return self.data["fan_speed"]

    @property
    def mode(self) -> str:
        return OperationModeFanP39(self.data["mode"]).name

    @property
    def power(self) -> bool:
        return self.data["power"]

    @property
    def delay_off_countdown(self) -> int:
        return self.data["power_off_time"]

    @property
    def oscillate(self) -> bool:
        return self.data["swing_mode"]

    @property
    def angle(self) -> int:
        return self.data["swing_mode_angle"]


class FanP39(MiotDevice):
    mapping = {
        # https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:fan:0000A005:dmaker-p39:1
        "power": {"siid": 2, "piid": 1},
        "fan_level": {"siid": 2, "piid": 2},
        "mode": {"siid": 2, "piid": 4},
        "swing_mode": {"siid": 2, "piid": 5},
        "swing_mode_angle": {"siid": 2, "piid": 6},
        "power_off_time": {"siid": 2, "piid": 8},
        "set_move": {"siid": 2, "piid": 10, "access": ["write"]},
        "fan_speed": {"siid": 2, "piid": 11},
        "child_lock": {"siid": 3, "piid": 1},
    }

    def __init__(
        self,
        ip: str = None,
        token: str = None,
        start_id: int = 0,
        debug: int = 0,
        lazy_discover: bool = True,
        model: str = MODEL_FAN_P39,
    ) -> None:
        super().__init__(ip, token, start_id, debug, lazy_discover, model=model)

    # backported and adapted from current master
    def get_properties_for_mapping(self, *, max_properties=15) -> list:
        """Retrieve raw properties based on mapping."""
        mapping = self._get_mapping()

        # We send property key in "did" because it's sent back via response and we can identify the property.
        properties = [
            {"did": k, **_filter_request_fields(v)}
            for k, v in mapping.items()
            if "aiid" not in v and ("access" not in v or "read" in v["access"])
        ]

        return self.get_properties(
            properties, property_getter="get_properties", max_properties=max_properties
        )

    def status(self):
        """Retrieve properties."""
        return FanStatusP39(
            {
                prop["did"]: prop["value"] if prop["code"] == 0 else None
                for prop in self.get_properties_for_mapping()
            }
        )

    def on(self):
        """Power on."""
        return self.set_property("power", True)

    def off(self):
        """Power off."""
        return self.set_property("power", False)

    def set_speed(self, speed: int):
        """Set fan speed."""
        if speed < 0 or speed > 100:
            raise FanException("Invalid speed: %s" % speed)
        return self.set_property("fan_speed", speed)

    def set_angle(self, angle: int):
        """Set the oscillation angle."""
        if angle not in [30, 60, 90, 120, 140]:
            raise FanException(
                "Unsupported angle. Supported values: "
                + ", ".join("{0}".format(i) for i in [30, 60, 90, 120, 140])
            )
        return self.set_property("swing_mode_angle", angle)

    def set_oscillate(self, oscillate: bool):
        """Set oscillate on/off."""
        if oscillate:
            return self.set_property("swing_mode", True)
        else:
            return self.set_property("swing_mode", False)

    def set_child_lock(self, lock: bool):
        """Set child lock on/off."""
        self.status()
        return self.set_property("child_lock", lock)

    def set_mode(self, mode: OperationModeFanP39):
        """Set mode."""
        return self.set_property("mode", OperationModeFanP39[mode.name].value)

    def delay_off(self, minutes: int):
        """Set delay off minutes."""
        if minutes < 0 or minutes > 480:
            raise FanException("Invalid value for a delayed turn off: %s" % minutes)
        return self.set_property("power_off_time", minutes)

    def set_rotate(self, direction: FanMoveDirection):
        """Rotate fan 7.5 degrees horizontally to given direction."""
        # Values for P39
        # { "value": 0, "description": "None" },
        # { "value": 1, "description": "Left" },
        # { "value": 2, "description": "Right" }
        value = 0
        if direction == FanMoveDirection.Left:
            value = 1
        elif direction == FanMoveDirection.Right:
            value = 2
        return self.set_property("set_move", value)
