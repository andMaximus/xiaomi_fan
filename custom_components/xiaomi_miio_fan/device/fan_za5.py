"""MIoT device classes for Xiaomi Fan ZA5 (zhimi.fan.za5)."""

from enum import Enum
from typing import Any

from miio.fan_common import FanException
from miio.fan_common import LedBrightness as FanLedBrightness
from miio.fan_common import MoveDirection as FanMoveDirection
from miio.fan_common import OperationMode as FanOperationMode
from miio.miot_device import DeviceStatus, MiotDevice

MODEL_FAN_ZA5 = "zhimi.fan.za5"


class OperationModeFanZA5(Enum):
    Nature = 0
    Normal = 1


class FanStatusZA5(DeviceStatus):
    """Container for status reports for FanZA5."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    @property
    def anion(self) -> bool:
        return self.data["anion"]

    @property
    def battery_supported(self) -> bool:
        return self.data["battery_supported"]

    @property
    def buttons_pressed(self) -> str:
        code = self.data["buttons_pressed"]
        if code == 0:
            return "None"
        if code == 1:
            return "Power"
        if code == 2:
            return "Swing"
        return "Unknown"

    @property
    def buzzer(self) -> bool:
        return self.data["buzzer"]

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
    def humidity(self) -> int:
        return self.data["humidity"]

    @property
    def light(self) -> int:
        return self.data["light"]

    @property
    def light_enum(self) -> str:
        if self.light == 1:
            brightness = 1
        elif self.light == 0:
            brightness = 2
        else:
            brightness = 0
        return FanLedBrightness(brightness).name

    @property
    def mode(self) -> str:
        return OperationModeFanZA5(self.data["mode"]).name

    @property
    def power(self) -> bool:
        return self.data["power"]

    @property
    def power_off_time(self) -> int:
        return self.data["power_off_time"]

    @property
    def powersupply_attached(self) -> bool:
        return self.data["powersupply_attached"]

    @property
    def speed_rpm(self) -> int:
        return self.data["speed_rpm"]

    @property
    def swing_mode(self) -> bool:
        return self.data["swing_mode"]

    @property
    def swing_mode_angle(self) -> int:
        return self.data["swing_mode_angle"]

    @property
    def temperature(self) -> Any:
        return self.data["temperature"]

    @property
    def led(self) -> bool | None:
        if self.light is None:
            return None
        return self.light > 0

    @property
    def battery_state(self) -> str:
        if self.powersupply_attached:
            return "Charging"
        return "Discharging"


class FanZA5(MiotDevice):
    mapping = {
        # https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:fan:0000A005:zhimi-za5:1
        "power": {"siid": 2, "piid": 1},
        "fan_level": {"siid": 2, "piid": 2},
        "swing_mode": {"siid": 2, "piid": 3},
        "swing_mode_angle": {"siid": 2, "piid": 5},
        "mode": {"siid": 2, "piid": 7},
        "power_off_time": {"siid": 2, "piid": 10},
        "anion": {"siid": 2, "piid": 11},
        "child_lock": {"siid": 3, "piid": 1},
        "light": {"siid": 4, "piid": 3},
        "buzzer": {"siid": 5, "piid": 1},
        "buttons_pressed": {"siid": 6, "piid": 1},
        "battery_supported": {"siid": 6, "piid": 2},
        "set_move": {"siid": 6, "piid": 3},
        "speed_rpm": {"siid": 6, "piid": 4},
        "powersupply_attached": {"siid": 6, "piid": 5},
        "fan_speed": {"siid": 6, "piid": 8},
        "humidity": {"siid": 7, "piid": 1},
        "temperature": {"siid": 7, "piid": 7},
    }

    def __init__(
        self,
        ip: str = None,
        token: str = None,
        start_id: int = 0,
        debug: int = 0,
        lazy_discover: bool = True,
        model: str = MODEL_FAN_ZA5,
    ) -> None:
        super().__init__(ip, token, start_id, debug, lazy_discover, model=model)

    def status(self):
        """Retrieve properties."""
        return FanStatusZA5(
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

    def set_anion(self, anion: bool):
        """Set anion on/off."""
        return self.set_property("anion", anion)

    def set_speed(self, speed: int):
        """Set fan speed."""
        if speed < 0 or speed > 100:
            raise FanException("Invalid speed: %s" % speed)
        return self.set_property("fan_speed", speed)

    def set_angle(self, angle: int):
        """Set the oscillation angle."""
        if angle not in [30, 60, 90, 120]:
            raise FanException(
                "Unsupported angle. Supported values: "
                + ", ".join("{0}".format(i) for i in [30, 60, 90, 120])
            )
        return self.set_property("swing_mode_angle", angle)

    def set_oscillate(self, oscillate: bool):
        """Set oscillate on/off."""
        if oscillate:
            return self.set_property("swing_mode", True)
        else:
            return self.set_property("swing_mode", False)

    def set_buzzer(self, buzzer: bool):
        """Set buzzer on/off."""
        if buzzer:
            return self.set_property("buzzer", True)
        else:
            return self.set_property("buzzer", False)

    def set_child_lock(self, lock: bool):
        """Set child lock on/off."""
        return self.set_property("child_lock", lock)

    def set_light(self, light: int):
        """Set indicator brightness."""
        if light < 0 or light > 100:
            raise FanException("Invalid light: %s" % light)
        return self.set_property("light", light)

    def set_mode(self, mode: FanOperationMode):
        """Set mode."""
        return self.set_property("mode", OperationModeFanZA5[mode.name].value)

    def delay_off(self, seconds: int):
        """Set delay off seconds."""
        if seconds < 0 or seconds > 10 * 60 * 60:
            raise FanException("Invalid value for a delayed turn off: %s" % seconds)
        return self.set_property("power_off_time", seconds)

    def set_rotate(self, direction: FanMoveDirection):
        """Rotate fan 7.5 degrees horizontally to given direction."""
        return self.set_property("set_move", direction.name.lower())
