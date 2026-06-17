"""MIoT device classes for Xiaomi Fan P76 (xiaomi.fan.p76)."""

from enum import Enum
from typing import Any

from miio.fan_common import FanException
from miio.miot_device import DeviceStatus, MiotDevice

MODEL_FAN_P76 = "xiaomi.fan.p76"


def _filter_request_fields(req):
    """Return only the parts that belong to the request."""
    return {k: v for k, v in req.items() if k in ["did", "siid", "piid"]}


class OperationModeFanP76(Enum):
    Straight = 0
    Natural = 1


class FanStatusP76(DeviceStatus):
    """Container for status reports for FanP76."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    @property
    def power(self) -> bool:
        return self.data["power"]

    @property
    def fault(self) -> int:
        return self.data["fault"]

    @property
    def mode(self) -> str:
        return OperationModeFanP76(self.data["mode"]).name

    @property
    def fan_level(self) -> int:
        return self.data["fan_level"]

    @property
    def fan_speed(self) -> int:
        return self.data["fan_speed"]

    @property
    def horizontal_swing(self) -> bool:
        return self.data["horizontal_swing"]

    @property
    def horizontal_swing_angle(self) -> int:
        return self.data["horizontal_swing_angle"]

    @property
    def vertical_swing(self) -> bool:
        return self.data["vertical_swing"]

    @property
    def vertical_swing_angle(self) -> int:
        return self.data["vertical_swing_angle"]

    @property
    def child_lock(self) -> bool:
        return self.data["child_lock"]

    @property
    def led(self) -> bool:
        return self.data["led"]

    @property
    def buzzer(self) -> bool:
        return self.data["buzzer"]

    @property
    def delay_time(self) -> int:
        return self.data["delay_time"]

    @property
    def delay_remain_time(self) -> int:
        return self.data["delay_remain_time"]


class FanP76(MiotDevice):
    """Main class representing the Xiaomi Fan P76 (xiaomi.fan.p76)."""

    mapping = {
        # urn:miot-spec-v2:device:fan:0000A005:xiaomi-p76:1
        "power": {"siid": 2, "piid": 1},
        "fan_level": {"siid": 2, "piid": 4},
        "child_lock": {"siid": 8, "piid": 1},
        "fan_speed": {"siid": 2, "piid": 5},
        "fault": {"siid": 2, "piid": 2},
        "mode": {"siid": 2, "piid": 3},
        "horizontal_swing": {"siid": 2, "piid": 6},
        "horizontal_swing_angle": {"siid": 2, "piid": 7},
        "vertical_swing": {"siid": 2, "piid": 8},
        "vertical_swing_angle": {"siid": 2, "piid": 9},
        "led": {"siid": 5, "piid": 1},
        "buzzer": {"siid": 7, "piid": 1},
        "delay": {"siid": 9, "piid": 1},
        "delay_time": {"siid": 9, "piid": 2},
        "delay_remain_time": {"siid": 9, "piid": 4},
        "turn_left": {"siid": 2, "aiid": 4},
        "turn_right": {"siid": 2, "aiid": 5},
        "turn_up": {"siid": 2, "aiid": 6},
        "turn_down": {"siid": 2, "aiid": 7},
    }

    def __init__(
        self,
        ip: str = None,
        token: str = None,
        start_id: int = 0,
        debug: int = 0,
        lazy_discover: bool = True,
        timeout: int = 5,
        model: str = MODEL_FAN_P76,
    ):
        super().__init__(ip, token, start_id, debug, lazy_discover, timeout, model=model)

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
        return FanStatusP76(
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
        """Set fan speed (1-100)."""
        return self.set_property("fan_speed", speed)

    def set_fan_level(self, fan_level: int):
        """Set fan level (0-3)."""
        return self.set_property("fan_level", fan_level)

    def set_oscillate(self, oscillate: bool):
        """Set horizontal oscillation on/off."""
        return self.set_property("horizontal_swing", oscillate)

    def set_vertical_oscillate(self, oscillate: bool):
        """Set vertical oscillation on/off."""
        return self.set_property("vertical_swing", oscillate)

    def set_buzzer(self, buzzer: bool):
        """Set buzzer on/off."""
        if buzzer:
            return self.set_property("buzzer", True)
        else:
            return self.set_property("buzzer", False)

    def set_child_lock(self, lock: bool):
        """Set child lock on/off."""
        self.status()
        return self.set_property("child_lock", lock)

    def set_angle(self, angle: int):
        """Set the horizontal oscillation angle."""
        if angle not in [30, 60, 90, 120]:
            raise FanException(
                "Unsupported angle. Supported values: "
                + ", ".join("{0}".format(i) for i in [30, 60, 90, 120])
            )
        return self.set_property("horizontal_swing_angle", angle)

    def set_vertical_angle(self, angle: int):
        """Set vertical oscillation angle."""
        if angle not in [30, 60, 90, 100]:
            raise FanException(
                "Unsupported angle. Supported values: "
                + ", ".join(str(i) for i in [30, 60, 90, 100])
            )
        return self.set_property("vertical_swing_angle", angle)

    def set_light(self, light: bool):
        """Set indicator state."""
        return self.set_property("led", light)

    def set_mode(self, mode: OperationModeFanP76):
        """Set mode."""
        return self.set_property("mode", mode.value)

    def delay_off(self, minutes: int):
        """Set delay off in minutes (0-480)."""
        if minutes < 0 or minutes > 480:
            raise FanException("Invalid value for a delayed turn off: %s" % minutes)
        return self.set_property("delay_time", minutes)

    def turn(self, direction: str):
        """Turn to the given direction."""
        if direction == "left":
            return self.call_action("turn_left")
        elif direction == "right":
            return self.call_action("turn_right")
        elif direction == "up":
            return self.call_action("turn_up")
        elif direction == "down":
            return self.call_action("turn_down")
        else:
            raise FanException(
                "Unsupported direction. Supported values: "
                + ", ".join(["left", "right", "up", "down"])
            )
