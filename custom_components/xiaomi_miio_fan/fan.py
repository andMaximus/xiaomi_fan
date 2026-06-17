"""
Support for Xiaomi Mi Smart Pedestal Fan.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/fan.xiaomi_miio/
"""

import asyncio
import logging
from enum import Enum
from functools import partial
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.fan import PLATFORM_SCHEMA, FanEntity, FanEntityFeature
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_MODE,
    CONF_HOST,
    CONF_NAME,
    CONF_TOKEN,
    Platform,
)
from homeassistant.exceptions import ConfigEntryNotReady, PlatformNotReady
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)
from miio import Device, DeviceException, Fan, Fan1C, FanLeshow, FanMiot, FanP5
from miio.fan_common import FanException
from miio.fan_common import LedBrightness as FanLedBrightness
from miio.fan_common import MoveDirection as FanMoveDirection
from miio.fan_common import OperationMode as FanOperationMode
from miio.integrations.fan.leshow.fan_leshow import (
    OperationMode as FanLeshowOperationMode,
)
from miio.miot_device import DeviceStatus, MiotDevice

from .const import (
    CONF_FIRMWARE_VERSION,
    CONF_HARDWARE_VERSION,
    CONF_MAC,
    CONF_MODEL,
    CONF_PRESET_MODES_OVERRIDE,
    CONF_RETRIES,
    DEFAULT_NAME,
    DEFAULT_RETRIES,
    DOMAIN,
    MODEL_FAN_1C,
    MODEL_FAN_LESHOW_SS4,
    MODEL_FAN_P10,
    MODEL_FAN_P11,
    MODEL_FAN_P15,
    MODEL_FAN_P18,
    MODEL_FAN_P30,
    MODEL_FAN_P33,
    MODEL_FAN_P39,
    MODEL_FAN_P5,
    MODEL_FAN_P70,
    MODEL_FAN_P76,
    MODEL_FAN_P8,
    MODEL_FAN_P9,
    MODEL_FAN_SA1,
    MODEL_FAN_V2,
    MODEL_FAN_V3,
    MODEL_FAN_ZA1,
    MODEL_FAN_ZA3,
    MODEL_FAN_ZA4,
    MODEL_FAN_ZA5,
)
from .device import (
    FanP33,
    FanP39,
    FanP70,
    FanP76,
    FanStatusP33,
    FanStatusP39,
    FanStatusP70,
    FanStatusP76,
    FanStatusZA5,
    FanZA5,
    OperationModeFanP33,
    OperationModeFanP39,
    OperationModeFanP70,
    OperationModeFanP76,
    OperationModeFanZA5,
)

_LOGGER = logging.getLogger(__name__)

# Keep DATA_KEY for YAML backward-compatibility
DATA_KEY = "fan.xiaomi_miio_fan"

SPEED_OFF = "off"

ATTR_MODEL = "model"
ATTR_BRIGHTNESS = "brightness"
ATTR_DIRECTION = "direction"
ATTR_ENABLED = "enabled"

ATTR_TEMPERATURE = "temperature"
ATTR_HUMIDITY = "humidity"
ATTR_LED = "led"
ATTR_LED_BRIGHTNESS = "led_brightness"
ATTR_RAW_LED_BRIGHTNESS = "raw_led_brightness"
ATTR_BUZZER = "buzzer"
ATTR_CHILD_LOCK = "child_lock"
ATTR_NATURAL_SPEED = "natural_speed"
ATTR_OSCILLATE = "oscillate"
ATTR_BATTERY = "battery"
ATTR_BATTERY_CHARGE = "battery_charge"
ATTR_BATTERY_STATE = "battery_state"
ATTR_AC_POWER = "ac_power"
ATTR_DELAY_OFF_COUNTDOWN = "delay_off_countdown"
ATTR_ANGLE = "angle"
ATTR_DIRECT_SPEED = "direct_speed"
ATTR_USE_TIME = "use_time"
ATTR_BUTTON_PRESSED = "button_pressed"
ATTR_RAW_SPEED = "raw_speed"
ATTR_IONIZER = "anion"
ATTR_VERTICAL_OSCILLATE = "vertical_oscillate"
ATTR_VERTICAL_ANGLE = "vertical_angle"

# Fan Leshow SS4
ATTR_ERROR_DETECTED = "error_detected"

AVAILABLE_ATTRIBUTES_FAN = {
    ATTR_ANGLE: "angle",
    ATTR_RAW_SPEED: "speed",
    ATTR_DELAY_OFF_COUNTDOWN: "delay_off_countdown",
    ATTR_AC_POWER: "ac_power",
    ATTR_OSCILLATE: "oscillate",
    ATTR_DIRECT_SPEED: "direct_speed",
    ATTR_NATURAL_SPEED: "natural_speed",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_BUZZER: "buzzer",
    ATTR_LED_BRIGHTNESS: "led_brightness",
    ATTR_USE_TIME: "use_time",
    # Additional properties of version 2 and 3
    ATTR_TEMPERATURE: "temperature",
    ATTR_HUMIDITY: "humidity",
    ATTR_BATTERY: "battery",
    ATTR_BATTERY_CHARGE: "battery_charge",
    ATTR_BUTTON_PRESSED: "button_pressed",
    # Additional properties of version 2
    ATTR_LED: "led",
    ATTR_BATTERY_STATE: "battery_state",
}

AVAILABLE_ATTRIBUTES_FAN_P5 = {
    ATTR_MODE: "mode",
    ATTR_OSCILLATE: "oscillate",
    ATTR_ANGLE: "angle",
    ATTR_DELAY_OFF_COUNTDOWN: "delay_off_countdown",
    ATTR_LED: "led",
    ATTR_BUZZER: "buzzer",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_RAW_SPEED: "speed",
}


AVAILABLE_ATTRIBUTES_FAN_P33 = {
    ATTR_MODE: "mode",
    ATTR_OSCILLATE: "oscillate",
    ATTR_ANGLE: "angle",
    ATTR_DELAY_OFF_COUNTDOWN: "delay_off_countdown",
    ATTR_LED: "led",
    ATTR_BUZZER: "buzzer",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_RAW_SPEED: "speed",
}

AVAILABLE_ATTRIBUTES_FAN_P39 = {
    ATTR_MODE: "mode",
    ATTR_OSCILLATE: "oscillate",
    ATTR_ANGLE: "angle",
    ATTR_DELAY_OFF_COUNTDOWN: "delay_off_countdown",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_RAW_SPEED: "speed",
}

AVAILABLE_ATTRIBUTES_FAN_P76 = {
    ATTR_MODE: "mode",
    ATTR_OSCILLATE: "horizontal_swing",
    ATTR_ANGLE: "horizontal_swing_angle",
    ATTR_VERTICAL_OSCILLATE: "vertical_swing",
    ATTR_VERTICAL_ANGLE: "vertical_swing_angle",
    ATTR_DELAY_OFF_COUNTDOWN: "delay_time",
    ATTR_LED: "led",
    ATTR_BUZZER: "buzzer",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_RAW_SPEED: "fan_speed",
}

AVAILABLE_ATTRIBUTES_FAN_P70 = {
    ATTR_MODE: "mode",
    ATTR_OSCILLATE: "horizontal_swing",
    ATTR_ANGLE: "horizontal_swing_angle",
    ATTR_VERTICAL_OSCILLATE: "vertical_swing",
    ATTR_VERTICAL_ANGLE: "vertical_swing_angle",
    ATTR_DELAY_OFF_COUNTDOWN: "delay_time",
    ATTR_LED: "led",
    ATTR_BUZZER: "buzzer",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_RAW_SPEED: "fan_speed",
}

AVAILABLE_ATTRIBUTES_FAN_LESHOW_SS4 = {
    ATTR_MODE: "mode",
    ATTR_RAW_SPEED: "speed",
    ATTR_BUZZER: "buzzer",
    ATTR_OSCILLATE: "oscillate",
    ATTR_DELAY_OFF_COUNTDOWN: "delay_off_countdown",
    ATTR_ERROR_DETECTED: "error_detected",
}

AVAILABLE_ATTRIBUTES_FAN_1C = {
    ATTR_MODE: "mode",
    ATTR_RAW_SPEED: "speed",
    ATTR_BUZZER: "buzzer",
    ATTR_OSCILLATE: "oscillate",
    ATTR_DELAY_OFF_COUNTDOWN: "delay_off_countdown",
    ATTR_LED: "led",
    ATTR_CHILD_LOCK: "child_lock",
}

AVAILABLE_ATTRIBUTES_FAN_ZA5 = {
    ATTR_ANGLE: "swing_mode_angle",
    ATTR_DIRECT_SPEED: "fan_speed",
    ATTR_NATURAL_SPEED: "fan_speed",
    ATTR_DELAY_OFF_COUNTDOWN: "power_off_time",
    ATTR_AC_POWER: "powersupply_attached",
    ATTR_OSCILLATE: "swing_mode",
    ATTR_MODE: "mode",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_BUZZER: "buzzer",
    ATTR_RAW_LED_BRIGHTNESS: "light",
    ATTR_LED_BRIGHTNESS: "light_enum",
    ATTR_TEMPERATURE: "temperature",
    ATTR_HUMIDITY: "humidity",
    ATTR_BUTTON_PRESSED: "buttons_pressed",
    # Fixed attributes
    ATTR_LED: "led",
    ATTR_RAW_SPEED: "speed_rpm",
    ATTR_BATTERY: "battery_supported",
    ATTR_BATTERY_STATE: "battery_state",
    ATTR_IONIZER: "anion",
}

FAN_SPEED_LEVEL1 = "Level 1"
FAN_SPEED_LEVEL2 = "Level 2"
FAN_SPEED_LEVEL3 = "Level 3"
FAN_SPEED_LEVEL4 = "Level 4"

FAN_SPEED_NATURAL1 = "Natural 1"
FAN_SPEED_NATURAL2 = "Natural 2"
FAN_SPEED_NATURAL3 = "Natural 3"
FAN_SPEED_NATURAL4 = "Natural 4"

FAN_PRESET_MODES = {
    SPEED_OFF: range(0, 1),
    FAN_SPEED_LEVEL1: range(1, 26),
    FAN_SPEED_LEVEL2: range(26, 51),
    FAN_SPEED_LEVEL3: range(51, 76),
    FAN_SPEED_LEVEL4: range(76, 101),
}

FAN_PRESET_MODE_VALUES = {
    SPEED_OFF: 0,
    FAN_SPEED_LEVEL1: 1,
    FAN_SPEED_LEVEL2: 35,
    FAN_SPEED_LEVEL3: 74,
    FAN_SPEED_LEVEL4: 100,
}

FAN_PRESET_MODE_VALUES_P5 = {
    SPEED_OFF: 0,
    FAN_SPEED_LEVEL1: 1,
    FAN_SPEED_LEVEL2: 35,
    FAN_SPEED_LEVEL3: 70,
    FAN_SPEED_LEVEL4: 100,
}

FAN_PRESET_MODES_1C = {
    SPEED_OFF: 0,
    FAN_SPEED_LEVEL1: 1,
    FAN_SPEED_LEVEL2: 2,
    FAN_SPEED_LEVEL3: 3,
}

FAN_PRESET_MODES_ZA5 = {
    SPEED_OFF: 0,
    FAN_SPEED_LEVEL1: 25,
    FAN_SPEED_LEVEL2: 50,
    FAN_SPEED_LEVEL3: 75,
    FAN_SPEED_LEVEL4: 100,
}

FAN_PRESET_MODES_P33 = {
    SPEED_OFF: 0,
    FAN_SPEED_LEVEL1: 1,
    FAN_SPEED_LEVEL2: 35,
    FAN_SPEED_LEVEL3: 70,
    FAN_SPEED_LEVEL4: 100,
}

FAN_PRESET_MODES_P39 = {
    SPEED_OFF: 0,
    FAN_SPEED_LEVEL1: 1,
    FAN_SPEED_LEVEL2: 35,
    FAN_SPEED_LEVEL3: 70,
    FAN_SPEED_LEVEL4: 100,
}

FAN_SPEEDS_1C = list(FAN_PRESET_MODES_1C)
FAN_SPEEDS_1C.remove(SPEED_OFF)

# FIXME: Add speed level 4
FAN_SPEEDS_ZA5 = list(FAN_PRESET_MODES_ZA5)
FAN_SPEEDS_ZA5.remove(SPEED_OFF)

FAN_SPEEDS_P33 = list(FAN_PRESET_MODES_P33)
FAN_SPEEDS_P33.remove(SPEED_OFF)

FAN_SPEEDS_P39 = list(FAN_PRESET_MODES_P39)
FAN_SPEEDS_P39.remove(SPEED_OFF)

FAN_PRESET_MODES_P76 = {
    SPEED_OFF: -1,
    FAN_SPEED_LEVEL1: 0,
    FAN_SPEED_LEVEL2: 1,
    FAN_SPEED_LEVEL3: 2,
    FAN_SPEED_LEVEL4: 3,
    FAN_SPEED_NATURAL1: 0,
    FAN_SPEED_NATURAL2: 1,
    FAN_SPEED_NATURAL3: 2,
    FAN_SPEED_NATURAL4: 3,
}

FAN_SPEEDS_P76 = [FAN_SPEED_LEVEL1, FAN_SPEED_LEVEL2, FAN_SPEED_LEVEL3, FAN_SPEED_LEVEL4, FAN_SPEED_NATURAL1, FAN_SPEED_NATURAL2, FAN_SPEED_NATURAL3, FAN_SPEED_NATURAL4]

FAN_PRESET_MODES_P70 = {
    SPEED_OFF: -1,
    FAN_SPEED_LEVEL1: 0,
    FAN_SPEED_LEVEL2: 1,
    FAN_SPEED_LEVEL3: 2,
    FAN_SPEED_LEVEL4: 3,
}

FAN_SPEEDS_P70 = [FAN_SPEED_LEVEL1, FAN_SPEED_LEVEL2, FAN_SPEED_LEVEL3, FAN_SPEED_LEVEL4]

SUCCESS = ["ok"]

FEATURE_SET_BUZZER = 1
FEATURE_SET_LED = 2
FEATURE_SET_CHILD_LOCK = 4
FEATURE_SET_LED_BRIGHTNESS = 8
FEATURE_SET_OSCILLATION_ANGLE = 16
FEATURE_SET_NATURAL_MODE = 32
FEATURE_SET_ANION = 64
FEATURE_SET_VERTICAL_OSCILLATION = 128
FEATURE_TURN = 256
FEATURE_SET_VERTICAL_OSCILLATION_ANGLE = 512

FEATURE_FLAGS_FAN = (
    FEATURE_SET_BUZZER
    | FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_LED_BRIGHTNESS
    | FEATURE_SET_OSCILLATION_ANGLE
    | FEATURE_SET_NATURAL_MODE
)

FEATURE_FLAGS_FAN_P5 = (
    FEATURE_SET_BUZZER
    | FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_NATURAL_MODE
    | FEATURE_SET_OSCILLATION_ANGLE
    | FEATURE_SET_LED
)

FEATURE_FLAGS_FAN_LESHOW_SS4 = FEATURE_SET_BUZZER
FEATURE_FLAGS_FAN_1C = FEATURE_FLAGS_FAN

FEATURE_FLAGS_FAN_ZA5 = (
    FEATURE_SET_BUZZER
    | FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_LED_BRIGHTNESS
    | FEATURE_SET_OSCILLATION_ANGLE
    | FEATURE_SET_NATURAL_MODE
    | FEATURE_SET_ANION
)

FEATURE_FLAGS_FAN_P33 = (
    FEATURE_SET_BUZZER
    | FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_LED
    | FEATURE_SET_OSCILLATION_ANGLE
    | FEATURE_SET_NATURAL_MODE
)

FEATURE_FLAGS_FAN_P39 = (
    FEATURE_SET_CHILD_LOCK | FEATURE_SET_OSCILLATION_ANGLE | FEATURE_SET_NATURAL_MODE
)

FEATURE_FLAGS_FAN_P76 = (
    FEATURE_SET_BUZZER
    | FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_LED
    | FEATURE_SET_OSCILLATION_ANGLE
    | FEATURE_SET_NATURAL_MODE
    | FEATURE_SET_VERTICAL_OSCILLATION
    | FEATURE_TURN
    | FEATURE_SET_VERTICAL_OSCILLATION_ANGLE
)

FEATURE_FLAGS_FAN_P70 = (
    FEATURE_SET_BUZZER
    | FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_LED
    | FEATURE_SET_OSCILLATION_ANGLE
    | FEATURE_SET_NATURAL_MODE
    | FEATURE_SET_VERTICAL_OSCILLATION
    | FEATURE_SET_VERTICAL_OSCILLATION_ANGLE
)

# Collapsed boolean services (replacing on/off pairs)
SERVICE_SET_BUZZER = "fan_set_buzzer"
SERVICE_SET_CHILD_LOCK = "fan_set_child_lock"
SERVICE_SET_NATURAL_MODE = "fan_set_natural_mode"
SERVICE_SET_VERTICAL_OSCILLATION = "fan_set_vertical_oscillation"
SERVICE_SET_ANION = "fan_set_anion"

# Unchanged services
SERVICE_SET_LED_BRIGHTNESS = "fan_set_led_brightness"
SERVICE_SET_RAW_LED_BRIGHTNESS = "fan_set_raw_led_brightness"
SERVICE_SET_OSCILLATION_ANGLE = "fan_set_oscillation_angle"
SERVICE_SET_DELAY_OFF = "fan_set_delay_off"
SERVICE_TURN = "fan_turn"
SERVICE_SET_VERTICAL_OSCILLATION_ANGLE = "fan_set_vertical_oscillation_angle"

AIRPURIFIER_SERVICE_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTITY_ID): cv.entity_ids})

SERVICE_SCHEMA_BOOLEAN = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_ENABLED): cv.boolean}
)

SERVICE_SCHEMA_LED_BRIGHTNESS = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_BRIGHTNESS): vol.All(vol.Coerce(int), vol.Clamp(min=0, max=2))}
)

SERVICE_SCHEMA_RAW_LED_BRIGHTNESS = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_BRIGHTNESS): vol.Coerce(int)}
)

SERVICE_SCHEMA_OSCILLATION_ANGLE = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_ANGLE): cv.positive_int}
)

SERVICE_SCHEMA_DELAY_OFF = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_DELAY_OFF_COUNTDOWN): cv.positive_int}
)

SERVICE_SCHEMA_TURN = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_DIRECTION): vol.All(vol.Coerce(str), vol.In(["left", "right", "up", "down"]))}
)

SERVICE_SCHEMA_VERTICAL_OSCILLATION_ANGLE = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_VERTICAL_ANGLE): cv.positive_int}
)

SERVICE_TO_METHOD = {
    SERVICE_SET_BUZZER: {
        "method": "async_set_buzzer",
        "schema": SERVICE_SCHEMA_BOOLEAN,
    },
    SERVICE_SET_CHILD_LOCK: {
        "method": "async_set_child_lock",
        "schema": SERVICE_SCHEMA_BOOLEAN,
    },
    SERVICE_SET_NATURAL_MODE: {
        "method": "async_set_natural_mode",
        "schema": SERVICE_SCHEMA_BOOLEAN,
    },
    SERVICE_SET_VERTICAL_OSCILLATION: {
        "method": "async_set_vertical_oscillation",
        "schema": SERVICE_SCHEMA_BOOLEAN,
    },
    SERVICE_SET_ANION: {
        "method": "async_set_anion",
        "schema": SERVICE_SCHEMA_BOOLEAN,
    },
    SERVICE_SET_LED_BRIGHTNESS: {
        "method": "async_set_led_brightness",
        "schema": SERVICE_SCHEMA_LED_BRIGHTNESS,
    },
    SERVICE_SET_RAW_LED_BRIGHTNESS: {
        "method": "async_set_raw_led_brightness",
        "schema": SERVICE_SCHEMA_RAW_LED_BRIGHTNESS,
    },
    SERVICE_SET_OSCILLATION_ANGLE: {
        "method": "async_set_oscillation_angle",
        "schema": SERVICE_SCHEMA_OSCILLATION_ANGLE,
    },
    SERVICE_SET_DELAY_OFF: {
        "method": "async_set_delay_off",
        "schema": SERVICE_SCHEMA_DELAY_OFF,
    },
    SERVICE_TURN: {
        "method": "async_turn",
        "schema": SERVICE_SCHEMA_TURN,
    },
    SERVICE_SET_VERTICAL_OSCILLATION_ANGLE: {
        "method": "async_set_vertical_oscillation_angle",
        "schema": SERVICE_SCHEMA_VERTICAL_OSCILLATION_ANGLE,
    },
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): vol.All(cv.string, vol.Length(min=32, max=32)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_MODEL): vol.In(
            [
                MODEL_FAN_V2,
                MODEL_FAN_V3,
                MODEL_FAN_SA1,
                MODEL_FAN_ZA1,
                MODEL_FAN_ZA3,
                MODEL_FAN_ZA4,
                MODEL_FAN_ZA5,
                MODEL_FAN_P5,
                MODEL_FAN_P8,
                MODEL_FAN_P9,
                MODEL_FAN_P10,
                MODEL_FAN_P11,
                MODEL_FAN_P15,
                MODEL_FAN_P18,
                MODEL_FAN_P30,
                MODEL_FAN_P33,
                MODEL_FAN_P39,
                MODEL_FAN_P76,
                MODEL_FAN_P70,
                MODEL_FAN_LESHOW_SS4,
                MODEL_FAN_1C,
            ]
        ),
        vol.Optional(CONF_RETRIES, default=DEFAULT_RETRIES): cv.positive_int,
        vol.Optional(CONF_PRESET_MODES_OVERRIDE, default=None): vol.Any(
            None, [cv.string]
        ),
    }
)


# pylint: disable=unused-argument
async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the miio fan device from config (YAML, backwards-compatible)."""
    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = {}

    host = config[CONF_HOST]
    token = config[CONF_TOKEN]
    name = config[CONF_NAME]
    model = config.get(CONF_MODEL)
    retries = config[CONF_RETRIES]
    preset_modes_override = config.get(CONF_PRESET_MODES_OVERRIDE)

    _LOGGER.info("Initializing with host %s (token %s...)", host, token[:5])
    unique_id = None

    if model is None:
        try:
            miio_device = Device(host, token)
            device_info = await hass.async_add_executor_job(miio_device.info)
            model = device_info.model
            unique_id = f"{model}-{device_info.mac_address}"
            _LOGGER.info(
                "%s %s %s detected",
                model,
                device_info.firmware_version,
                device_info.hardware_version,
            )
        except DeviceException as ex:
            raise PlatformNotReady from ex

    device = _async_setup_device(
        name, host, token, model, unique_id, retries, preset_modes_override,
        is_config_entry=False,
    )
    if device is None:
        return False

    hass.data[DATA_KEY][host] = device
    async_add_entities([device], update_before_add=True)

    async def async_service_handler(service):
        """Map services to methods on XiaomiFan."""
        method = SERVICE_TO_METHOD.get(service.service)
        params = {
            key: value for key, value in service.data.items() if key != ATTR_ENTITY_ID
        }
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        if entity_ids:
            devices = [
                device
                for device in hass.data[DATA_KEY].values()
                if device.entity_id in entity_ids
            ]
        else:
            devices = hass.data[DATA_KEY].values()

        update_tasks = []
        for device in devices:
            if not hasattr(device, method["method"]):
                continue
            await getattr(device, method["method"])(**params)
            update_tasks.append(asyncio.create_task(device.async_update_ha_state(True)))

        if update_tasks:
            await asyncio.wait(update_tasks)

    for air_purifier_service in SERVICE_TO_METHOD:
        schema = SERVICE_TO_METHOD[air_purifier_service].get(
            "schema", AIRPURIFIER_SERVICE_SCHEMA
        )
        hass.services.async_register(
            DOMAIN, air_purifier_service, async_service_handler, schema=schema
        )


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Xiaomi Fan from a config entry."""
    host = entry.data[CONF_HOST]
    token = entry.data[CONF_TOKEN]
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    model = entry.data.get(CONF_MODEL)
    retries = entry.data.get(CONF_RETRIES, DEFAULT_RETRIES)
    mac = entry.data.get(CONF_MAC)
    firmware_version = entry.data.get(CONF_FIRMWARE_VERSION)
    hardware_version = entry.data.get(CONF_HARDWARE_VERSION)

    # Options override data
    preset_modes_override = entry.options.get(CONF_PRESET_MODES_OVERRIDE)
    # Treat empty list as None (no override)
    if isinstance(preset_modes_override, list) and len(preset_modes_override) == 0:
        preset_modes_override = None

    unique_id = f"{model}-{mac}" if mac else (f"{model}-{host}" if model else host)

    if model is None:
        try:
            miio_device = Device(host, token)
            device_info = await hass.async_add_executor_job(miio_device.info)
            model = device_info.model
            if not mac:
                unique_id = f"{model}-{device_info.mac_address}"
        except DeviceException as ex:
            raise ConfigEntryNotReady from ex

    try:
        device = _async_setup_device(
            name, host, token, model, unique_id, retries, preset_modes_override,
            is_config_entry=True,
            firmware_version=firmware_version,
            hardware_version=hardware_version,
        )
    except ConfigEntryNotReady:
        raise

    if device is None:
        return False

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = device
    async_add_entities([device], update_before_add=True)

    async def async_service_handler(service):
        """Map services to methods on XiaomiFan (config entry path)."""
        method = SERVICE_TO_METHOD.get(service.service)
        params = {
            key: value for key, value in service.data.items() if key != ATTR_ENTITY_ID
        }
        entity_ids = service.data.get(ATTR_ENTITY_ID)

        all_devices = list(hass.data.get(DOMAIN, {}).values())

        if entity_ids:
            target_devices = [d for d in all_devices if d.entity_id in entity_ids]
        else:
            target_devices = all_devices

        update_tasks = []
        for dev in target_devices:
            if not hasattr(dev, method["method"]):
                continue
            await getattr(dev, method["method"])(**params)
            update_tasks.append(asyncio.create_task(dev.async_update_ha_state(True)))

        if update_tasks:
            await asyncio.wait(update_tasks)

    for svc_name in SERVICE_TO_METHOD:
        if not hass.services.has_service(DOMAIN, svc_name):
            schema = SERVICE_TO_METHOD[svc_name].get("schema", AIRPURIFIER_SERVICE_SCHEMA)
            hass.services.async_register(
                DOMAIN, svc_name, async_service_handler, schema=schema
            )


def _async_setup_device(
    name,
    host,
    token,
    model,
    unique_id,
    retries,
    preset_modes_override,
    is_config_entry: bool = False,
    firmware_version: str | None = None,
    hardware_version: str | None = None,
):
    """Instantiate the correct entity class for the given model."""
    if model in [
        MODEL_FAN_V2,
        MODEL_FAN_V3,
        MODEL_FAN_SA1,
        MODEL_FAN_ZA1,
        MODEL_FAN_ZA3,
        MODEL_FAN_ZA4,
    ]:
        fan = Fan(host, token, model=model)
        return XiaomiFan(
            name, fan, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )
    elif model == MODEL_FAN_P5:
        fan = FanP5(host, token, model=model)
        return XiaomiFanP5(
            name, fan, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )
    elif model == MODEL_FAN_P9:
        fan = FanMiot(host, token, model=model)
        return XiaomiFanMiot(
            name, fan, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )
    elif model in [MODEL_FAN_P10, MODEL_FAN_P18, MODEL_FAN_P30]:
        fan = FanMiot(host, token, model=MODEL_FAN_P10)
        return XiaomiFanMiot(
            name, fan, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )
    elif model in [MODEL_FAN_P11, MODEL_FAN_P15]:
        fan = FanMiot(host, token, model=MODEL_FAN_P11)
        return XiaomiFanMiot(
            name, fan, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )
    elif model == MODEL_FAN_LESHOW_SS4:
        fan = FanLeshow(host, token, model=model)
        return XiaomiFanLeshow(
            name, fan, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )
    elif model in [MODEL_FAN_1C, MODEL_FAN_P8]:
        fan = Fan1C(host, token, model=model)
        return XiaomiFan1C(
            name, fan, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )
    elif model == MODEL_FAN_ZA5:
        fan = FanZA5(host, token, model=model)
        return XiaomiFanZA5(
            name, fan, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )
    elif model == MODEL_FAN_P33:
        fan = FanP33(host, token, model=model)
        return XiaomiFanP33(
            name, fan, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )
    elif model == MODEL_FAN_P39:
        fan = FanP39(host, token, model=model)
        return XiaomiFanP39(
            name, fan, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )
    elif model == MODEL_FAN_P76:
        fan = FanP76(host, token, model=model)
        return XiaomiFanP76(
            name, fan, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )
    elif model == MODEL_FAN_P70:
        fan = FanP70(host, token, model=model)
        return XiaomiFanP70(
            name, fan, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )
    else:
        _LOGGER.error(
            "Unsupported device found! Please create an issue at "
            "https://github.com/syssi/xiaomi_fan/issues "
            "and provide the following data: %s",
            model,
        )
        if is_config_entry:
            raise ConfigEntryNotReady(f"Unsupported model: {model}")
        return None


class XiaomiGenericDevice(FanEntity):
    """Representation of a generic Xiaomi device."""

    _enable_turn_on_off_backwards_compatibility = False

    def __init__(
        self,
        name,
        device,
        model,
        unique_id,
        retries,
        preset_modes_override,
        firmware_version: str | None = None,
        hardware_version: str | None = None,
    ):
        """Initialize the generic Xiaomi device."""
        self._name = name
        self._device = device
        self._model = model
        self._unique_id = unique_id
        self._retry = 0
        self._retries = retries
        self._preset_modes_override = preset_modes_override
        self._firmware_version = firmware_version
        self._hardware_version = hardware_version

        self._available = False
        self._state = None
        self._state_attrs = {ATTR_MODEL: self._model}
        self._device_features = FEATURE_SET_BUZZER
        self._skip_update = False

    @property
    def supported_features(self):
        """Flag supported features."""
        return 0

    @property
    def unique_id(self):
        """Return an unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def available(self):
        """Return true when state is known."""
        return self._available

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes of the device."""
        return self._state_attrs

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    @property
    def device_info(self):
        """Return device information."""
        info = {
            "identifiers": {(DOMAIN, self._unique_id)},
            "name": self._name,
            "manufacturer": "Xiaomi",
            "model": self._model,
        }
        if self._firmware_version:
            info["sw_version"] = self._firmware_version
        if self._hardware_version:
            info["hw_version"] = self._hardware_version
        return info

    @staticmethod
    def _extract_value_from_attribute(state, attribute):
        value = getattr(state, attribute, None)
        if isinstance(value, Enum):
            return value.value
        return value

    async def _try_command(self, mask_error, func, *args, **kwargs):
        """Call a miio device command handling error messages."""
        try:
            result = await self.hass.async_add_executor_job(
                partial(func, *args, **kwargs)
            )
            _LOGGER.debug("Response received from miio device: %s", result)
            return result == SUCCESS
        except DeviceException as exc:
            _LOGGER.error(mask_error, exc)
            self._available = False
            return False

    async def async_turn_on(
        self, speed: str = None, mode: str = None, **kwargs
    ) -> None:
        """Turn the device on."""
        result = await self._try_command(
            "Turning the miio device on failed.", self._device.on
        )
        if speed:
            result = await self.async_set_speed(speed)

        if result:
            self._state = True
            self._skip_update = True

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the device off."""
        result = await self._try_command(
            "Turning the miio device off failed.", self._device.off
        )
        if result:
            self._state = False
            self._skip_update = True

    async def async_set_buzzer(self, enabled: bool):
        """Turn the buzzer on or off."""
        if self._device_features & FEATURE_SET_BUZZER == 0:
            return
        await self._try_command(
            "Setting the buzzer of the miio device failed.",
            self._device.set_buzzer,
            enabled,
        )

    async def async_set_child_lock(self, enabled: bool):
        """Turn the child lock on or off."""
        if self._device_features & FEATURE_SET_CHILD_LOCK == 0:
            return
        await self._try_command(
            "Setting the child lock of the miio device failed.",
            self._device.set_child_lock,
            enabled,
        )


class XiaomiFan(XiaomiGenericDevice):
    """Representation of a Xiaomi Pedestal Fan."""

    def __init__(
        self,
        name,
        device,
        model,
        unique_id,
        retries,
        preset_modes_override,
        firmware_version: str | None = None,
        hardware_version: str | None = None,
    ):
        """Initialize the fan entity."""
        super().__init__(
            name, device, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )

        self._device_features = FEATURE_FLAGS_FAN
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN
        self._percentage = None
        self._preset_modes = list(FAN_PRESET_MODES)
        if preset_modes_override is not None:
            self._preset_modes = preset_modes_override

        self._preset_mode = None
        self._oscillate = None
        self._natural_mode = False

        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )

    @property
    def supported_features(self) -> int:
        """Supported features."""
        return (
            FanEntityFeature.SET_SPEED
            | FanEntityFeature.PRESET_MODE
            | FanEntityFeature.OSCILLATE
            | FanEntityFeature.DIRECTION
            | FanEntityFeature.TURN_OFF
            | FanEntityFeature.TURN_ON
        )

    async def async_update(self):
        """Fetch state from the device."""
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._oscillate = state.oscillate
            self._natural_mode = state.natural_speed != 0
            self._state = state.is_on

            if self._natural_mode:
                for preset_mode, r in FAN_PRESET_MODES.items():
                    if state.natural_speed in r:
                        self._preset_mode = preset_mode
                        self._percentage = state.natural_speed
                        break
            else:
                for preset_mode, r in FAN_PRESET_MODES.items():
                    if state.direct_speed in r:
                        self._preset_mode = preset_mode
                        self._percentage = state.direct_speed
                        break

            self._state_attrs.update(
                {
                    key: self._extract_value_from_attribute(state, value)
                    for key, value in self._available_attributes.items()
                }
            )
            self._retry = 0

        except DeviceException as ex:
            self._retry = self._retry + 1
            if self._retry < self._retries:
                _LOGGER.info(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )

    @property
    def percentage(self):
        """Return the current speed."""
        return self._percentage

    @property
    def preset_modes(self):
        """Get the list of available preset modes."""
        return self._preset_modes

    @property
    def preset_mode(self):
        """Get the current preset mode."""
        return self._preset_mode

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        _LOGGER.debug("Setting the preset mode to: %s", preset_mode)

        if preset_mode == SPEED_OFF:
            await self.async_turn_off()
            return

        if self._natural_mode:
            await self._try_command(
                "Setting fan speed of the miio device failed.",
                self._device.set_natural_speed,
                FAN_PRESET_MODE_VALUES[preset_mode],
            )
        else:
            await self._try_command(
                "Setting fan speed of the miio device failed.",
                self._device.set_direct_speed,
                FAN_PRESET_MODE_VALUES[preset_mode],
            )

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        _LOGGER.debug("Setting the fan speed percentage to: %s", percentage)

        if percentage == 0:
            await self.async_turn_off()
            return

        if self._natural_mode:
            await self._try_command(
                "Setting fan speed percentage of the miio device failed.",
                self._device.set_natural_speed,
                percentage,
            )
        else:
            await self._try_command(
                "Setting fan speed percentage of the miio device failed.",
                self._device.set_direct_speed,
                percentage,
            )

    async def async_set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""
        if direction == "forward":
            direction = "right"

        if direction == "reverse":
            direction = "left"

        if self._oscillate:
            await self._try_command(
                "Setting oscillate off of the miio device failed.",
                self._device.set_oscillate,
                False,
            )

        await self._try_command(
            "Setting move direction of the miio device failed.",
            self._device.set_rotate,
            FanMoveDirection(direction),
        )

    @property
    def oscillating(self):
        """Return the oscillation state."""
        return self._oscillate

    async def async_oscillate(self, oscillating: bool) -> None:
        """Set oscillation."""
        if oscillating:
            await self._try_command(
                "Setting oscillate on of the miio device failed.",
                self._device.set_oscillate,
                True,
            )
        else:
            await self._try_command(
                "Setting oscillate off of the miio device failed.",
                self._device.set_oscillate,
                False,
            )

    async def async_set_oscillation_angle(self, angle: int) -> None:
        """Set oscillation angle."""
        if self._device_features & FEATURE_SET_OSCILLATION_ANGLE == 0:
            return

        await self._try_command(
            "Setting angle of the miio device failed.", self._device.set_angle, angle
        )

    async def async_set_delay_off(self, delay_off_countdown: int) -> None:
        """Set scheduled off timer in minutes."""
        await self._try_command(
            "Setting delay off miio device failed.",
            self._device.delay_off,
            delay_off_countdown * 60,
        )

    async def async_set_led_brightness(self, brightness: int = 2):
        """Set the led brightness."""
        if self._device_features & FEATURE_SET_LED_BRIGHTNESS == 0:
            return

        await self._try_command(
            "Setting the led brightness of the miio device failed.",
            self._device.set_led_brightness,
            FanLedBrightness(brightness),
        )

    async def async_set_natural_mode(self, enabled: bool):
        """Turn the natural mode on or off."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        self._natural_mode = enabled
        await self.async_set_percentage(self._percentage)

    async def async_set_vertical_oscillation_angle(self, vertical_angle: int) -> None:
        """Set vertical oscillation angle."""
        if self._device_features & FEATURE_SET_VERTICAL_OSCILLATION_ANGLE == 0:
            return

        await self._try_command(
            "Setting vertical oscillation angle of the miio device failed.",
            self._device.set_vertical_angle,
            vertical_angle,
        )


class XiaomiFanP5(XiaomiFan):
    """Representation of a Xiaomi Pedestal Fan P5."""

    def __init__(
        self,
        name,
        device,
        model,
        unique_id,
        retries,
        preset_modes_override,
        firmware_version: str | None = None,
        hardware_version: str | None = None,
    ):
        """Initialize the fan entity."""
        super().__init__(
            name, device, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )

        self._device_features = FEATURE_FLAGS_FAN_P5
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN_P5
        self._percentage = None
        self._preset_modes = list(FAN_PRESET_MODES)
        if preset_modes_override is not None:
            self._preset_modes = preset_modes_override

        self._preset_mode = None
        self._oscillate = None
        self._natural_mode = False

        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )

    async def async_update(self):
        """Fetch state from the device."""
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._percentage = state.speed
            self._oscillate = state.oscillate
            self._natural_mode = state.mode == FanOperationMode.Nature
            self._state = state.is_on

            for preset_mode, r in FAN_PRESET_MODES.items():
                if state.speed in r:
                    self._preset_mode = preset_mode
                    break

            self._state_attrs.update(
                {
                    key: self._extract_value_from_attribute(state, value)
                    for key, value in self._available_attributes.items()
                }
            )

            self._retry = 0

        except DeviceException as ex:
            self._retry = self._retry + 1
            if self._retry < self._retries:
                _LOGGER.info(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        _LOGGER.debug("Setting the preset mode to: %s", preset_mode)

        if preset_mode == SPEED_OFF:
            await self.async_turn_off()
            return

        if not self._state:
            await self._try_command(
                "Turning the miio device on failed.", self._device.on
            )
        await self._try_command(
            "Setting fan speed of the miio device failed.",
            self._device.set_speed,
            FAN_PRESET_MODE_VALUES_P5[preset_mode],
        )

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        _LOGGER.debug("Setting the fan speed percentage to: %s", percentage)

        if percentage == 0:
            await self.async_turn_off()
            return

        if not self._state:
            await self._try_command(
                "Turning the miio device on failed.", self._device.on
            )
        await self._try_command(
            "Setting fan speed percentage of the miio device failed.",
            self._device.set_speed,
            percentage,
        )

    async def async_set_natural_mode(self, enabled: bool):
        """Turn the natural mode on or off."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Turning on natural mode of the miio device failed.",
            self._device.set_mode,
            FanOperationMode.Nature if enabled else FanOperationMode.Normal,
        )

    async def async_set_delay_off(self, delay_off_countdown: int) -> None:
        """Set scheduled off timer in minutes."""
        await self._try_command(
            "Setting delay off miio device failed.",
            self._device.delay_off,
            delay_off_countdown,
        )


class XiaomiFanMiot(XiaomiFanP5):
    """Representation of a Xiaomi Pedestal Fan P9, P10, P11, P18, P30."""

    pass


class XiaomiFanLeshow(XiaomiGenericDevice):
    """Representation of a Xiaomi Fan Leshow SS4."""

    def __init__(
        self,
        name,
        device,
        model,
        unique_id,
        retries,
        preset_modes_override,
        firmware_version: str | None = None,
        hardware_version: str | None = None,
    ):
        """Initialize the fan entity."""
        super().__init__(
            name, device, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )

        self._device_features = FEATURE_FLAGS_FAN_LESHOW_SS4
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN_LESHOW_SS4
        self._percentage = None
        self._preset_modes = [mode.name for mode in FanLeshowOperationMode]
        if preset_modes_override is not None:
            self._preset_modes = preset_modes_override
        self._oscillate = None

        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )

    @property
    def supported_features(self) -> int:
        """Supported features."""
        return (
            FanEntityFeature.SET_SPEED
            | FanEntityFeature.PRESET_MODE
            | FanEntityFeature.OSCILLATE
            | FanEntityFeature.TURN_OFF
            | FanEntityFeature.TURN_ON
        )

    async def async_update(self):
        """Fetch state from the device."""
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._percentage = state.speed
            self._oscillate = state.oscillate
            self._state = state.is_on

            self._state_attrs.update(
                {
                    key: self._extract_value_from_attribute(state, value)
                    for key, value in self._available_attributes.items()
                }
            )
            self._retry = 0

        except DeviceException as ex:
            self._retry = self._retry + 1
            if self._retry < self._retries:
                _LOGGER.info(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )

    @property
    def percentage(self):
        """Return the current speed."""
        return self._percentage

    @property
    def preset_modes(self):
        """Get the list of available preset modes."""
        return self._preset_modes

    @property
    def preset_mode(self):
        """Get the current preset mode."""
        if self._state:
            return FanLeshowOperationMode(self._state_attrs[ATTR_MODE]).name
        return None

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        _LOGGER.debug("Setting the preset mode to: %s", preset_mode)

        await self._try_command(
            "Setting preset mode of the miio device failed.",
            self._device.set_mode,
            FanLeshowOperationMode[preset_mode.title()],
        )

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        _LOGGER.debug("Setting the fan speed percentage to: %s", percentage)

        if percentage == 0:
            await self.async_turn_off()
            return

        await self._try_command(
            "Setting fan speed percentage of the miio device failed.",
            self._device.set_speed,
            percentage,
        )

    @property
    def oscillating(self):
        """Return the oscillation state."""
        return self._oscillate

    async def async_oscillate(self, oscillating: bool) -> None:
        """Set oscillation."""
        if oscillating:
            await self._try_command(
                "Setting oscillate on of the miio device failed.",
                self._device.set_oscillate,
                True,
            )
        else:
            await self._try_command(
                "Setting oscillate off of the miio device failed.",
                self._device.set_oscillate,
                False,
            )

    async def async_set_delay_off(self, delay_off_countdown: int) -> None:
        """Set scheduled off timer in minutes."""
        await self._try_command(
            "Setting delay off miio device failed.",
            self._device.delay_off,
            delay_off_countdown,
        )


class XiaomiFan1C(XiaomiFan):
    """Representation of a Xiaomi Fan 1C."""

    def __init__(
        self,
        name,
        device,
        model,
        unique_id,
        retries,
        preset_modes_override,
        firmware_version: str | None = None,
        hardware_version: str | None = None,
    ):
        """Initialize the fan entity."""
        super().__init__(
            name, device, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )

        self._device_features = FEATURE_FLAGS_FAN_1C
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN_1C
        self._preset_modes = list(FAN_PRESET_MODES_1C)
        if preset_modes_override is not None:
            self._preset_modes = preset_modes_override

        self._oscillate = None

        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )

    @property
    def supported_features(self) -> int:
        """Supported features."""
        return (
            FanEntityFeature.SET_SPEED
            | FanEntityFeature.PRESET_MODE
            | FanEntityFeature.OSCILLATE
            | FanEntityFeature.TURN_OFF
            | FanEntityFeature.TURN_ON
        )

    async def async_update(self):
        """Fetch state from the device."""
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._oscillate = state.oscillate
            self._state = state.is_on

            for preset_mode, value in FAN_PRESET_MODES_1C.items():
                if state.speed == value:
                    self._preset_mode = preset_mode

            self._state_attrs.update(
                {
                    key: self._extract_value_from_attribute(state, value)
                    for key, value in self._available_attributes.items()
                }
            )
            self._retry = 0

        except DeviceException as ex:
            self._retry = self._retry + 1
            if self._retry < self._retries:
                _LOGGER.info(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        return ordered_list_item_to_percentage(FAN_SPEEDS_1C, self._preset_mode)

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return len(FAN_SPEEDS_1C)

    @property
    def preset_modes(self):
        """Get the list of available preset modes."""
        return self._preset_modes

    @property
    def preset_mode(self):
        """Get the current preset mode."""
        if self._state:
            return self._preset_mode
        return None

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        _LOGGER.debug("Setting the preset mode to: %s", preset_mode)

        if not self._state:
            await self._try_command(
                "Turning the miio device on failed.", self._device.on
            )
        await self._try_command(
            "Setting preset mode of the miio device failed.",
            self._device.set_speed,
            FAN_PRESET_MODES_1C[preset_mode],
        )

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        _LOGGER.debug("Setting the fan speed percentage to: %s", percentage)

        if percentage == 0:
            await self.async_turn_off()
            return

        if not self._state:
            await self._try_command(
                "Turning the miio device on failed.", self._device.on
            )
        await self._try_command(
            "Setting preset mode of the miio device failed.",
            self._device.set_speed,
            FAN_PRESET_MODES_1C[
                percentage_to_ordered_list_item(FAN_SPEEDS_1C, percentage)
            ],
        )

    @property
    def oscillating(self):
        """Return the oscillation state."""
        return self._oscillate

    async def async_oscillate(self, oscillating: bool) -> None:
        """Set oscillation."""
        if oscillating:
            await self._try_command(
                "Setting oscillate on of the miio device failed.",
                self._device.set_oscillate,
                True,
            )
        else:
            await self._try_command(
                "Setting oscillate off of the miio device failed.",
                self._device.set_oscillate,
                False,
            )

    async def async_set_delay_off(self, delay_off_countdown: int) -> None:
        """Set scheduled off timer in minutes."""
        await self._try_command(
            "Setting delay off miio device failed.",
            self._device.delay_off,
            delay_off_countdown,
        )

    async def async_set_natural_mode(self, enabled: bool):
        """Turn the natural mode on or off."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Setting fan natural mode of the miio device failed.",
            self._device.set_mode,
            FanOperationMode.Nature if enabled else FanOperationMode.Normal,
        )


class XiaomiFanZA5(XiaomiFan):
    """Representation of a Xiaomi Fan ZA5."""

    def __init__(
        self,
        name,
        device,
        model,
        unique_id,
        retries,
        preset_modes_override,
        firmware_version: str | None = None,
        hardware_version: str | None = None,
    ):
        """Initialize the fan entity."""
        super().__init__(
            name, device, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )

        self._device_features = FEATURE_FLAGS_FAN_ZA5
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN_ZA5
        self._preset_modes = list(FAN_PRESET_MODES_ZA5)
        if preset_modes_override is not None:
            self._preset_modes = preset_modes_override

        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )

    @property
    def supported_features(self) -> int:
        return (
            FanEntityFeature.DIRECTION
            | FanEntityFeature.OSCILLATE
            | FanEntityFeature.PRESET_MODE
            | FanEntityFeature.SET_SPEED
            | FanEntityFeature.TURN_OFF
            | FanEntityFeature.TURN_ON
        )

    async def async_update(self):
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._percentage = state.fan_speed
            self._oscillate = state.swing_mode
            self._natural_mode = state.mode == FanOperationMode.Nature
            self._state = state.power

            for preset_mode, value in FAN_PRESET_MODES_ZA5.items():
                if state.fan_level == value:
                    self._preset_mode = preset_mode

            self._state_attrs.update(
                {
                    key: self._extract_value_from_attribute(state, value)
                    for key, value in self._available_attributes.items()
                    if hasattr(state, value)
                }
            )
            self._retry = 0
        except DeviceException as ex:
            self._retry = self._retry + 1
            if self._retry < self._retries:
                _LOGGER.info(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )

    @property
    def percentage(self) -> int | None:
        return self._percentage

    @property
    def speed_count(self) -> int:
        return 100

    @property
    def preset_modes(self):
        return self._preset_modes

    @property
    def preset_mode(self):
        if self._state:
            return self._preset_mode
        return None

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        _LOGGER.debug("Setting the preset mode to: %s", preset_mode)

        if not self._state:
            await self._try_command(
                "Turning the miio device on failed.", self._device.on
            )
        await self._try_command(
            "Setting preset mode of the miio device failed.",
            self._device.set_speed,
            FAN_PRESET_MODE_VALUES[preset_mode],
        )

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        _LOGGER.debug("Setting the fan speed percentage to: %s", percentage)

        if percentage == 0:
            await self.async_turn_off()
            return

        if not self._state:
            await self._try_command(
                "Turning the miio device on failed.", self._device.on
            )
        await self._try_command(
            "Setting preset mode of the miio device failed.",
            self._device.set_speed,
            percentage,
        )

    async def async_oscillate(self, oscillating: bool) -> None:
        """Set oscillation."""
        if oscillating:
            await self._try_command(
                "Setting oscillate on of the miio device failed.",
                self._device.set_oscillate,
                True,
            )
        else:
            await self._try_command(
                "Setting oscillate off of the miio device failed.",
                self._device.set_oscillate,
                False,
            )

    async def async_set_delay_off(self, delay_off_countdown: int) -> None:
        """Set scheduled off timer in minutes."""
        await self._try_command(
            "Setting delay off miio device failed.",
            self._device.delay_off,
            delay_off_countdown * 60,
        )

    async def async_set_natural_mode(self, enabled: bool):
        """Turn the natural mode on or off."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Setting fan natural mode of the miio device failed.",
            self._device.set_mode,
            FanOperationMode.Nature if enabled else FanOperationMode.Normal,
        )

    async def async_set_led_brightness(self, brightness: int = 2):
        """Set the led brightness."""
        brightness_enum = FanLedBrightness(brightness)
        if brightness_enum == FanLedBrightness.Bright:
            raw = 100
        elif brightness_enum == FanLedBrightness.Dim:
            raw = 1
        else:
            raw = 0
        await self.async_set_raw_led_brightness(raw)

    async def async_set_raw_led_brightness(self, brightness: int):
        """Set the raw led brightness."""
        if self._device_features & FEATURE_SET_LED_BRIGHTNESS == 0:
            return

        await self._try_command(
            "Setting the led brightness of the miio device failed.",
            self._device.set_light,
            brightness,
        )

    async def async_set_anion(self, enabled: bool):
        """Turn anion on or off."""
        if self._device_features & FEATURE_SET_ANION == 0:
            return

        await self._try_command(
            "Setting anion of the miio device failed.",
            self._device.set_anion,
            enabled,
        )


class XiaomiFanP33(XiaomiFanMiot):
    """Representation of a Xiaomi Fan P33."""

    def __init__(
        self,
        name,
        device,
        model,
        unique_id,
        retries,
        preset_modes_override,
        firmware_version: str | None = None,
        hardware_version: str | None = None,
    ):
        """Initialize the fan entity."""
        super().__init__(
            name, device, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )

        self._device_features = FEATURE_FLAGS_FAN_P33
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN_P33
        self._percentage = None
        self._preset_modes = list(FAN_PRESET_MODES_P33)
        if preset_modes_override is not None:
            self._preset_modes = preset_modes_override

        self._preset_mode = None
        self._oscillate = None
        self._natural_mode = False

        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )

    @property
    def supported_features(self) -> int:
        return (
            FanEntityFeature.DIRECTION
            | FanEntityFeature.OSCILLATE
            | FanEntityFeature.PRESET_MODE
            | FanEntityFeature.SET_SPEED
            | FanEntityFeature.TURN_OFF
            | FanEntityFeature.TURN_ON
        )

    """
    TODO:
    - setting child lock works, but HA always reads the value as null
    """

    async def async_update(self):
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._percentage = state.percentage
            self._oscillate = state.oscillate
            self._natural_mode = state.mode == OperationModeFanP33.Nature
            self._state = state.power

            for preset_mode, value in FAN_PRESET_MODES_P33.items():
                if state.fan_level == value:
                    self._preset_mode = preset_mode
                    break

            self._state_attrs.update(
                {
                    key: self._extract_value_from_attribute(state, value)
                    for key, value in self._available_attributes.items()
                    if hasattr(state, value)
                }
            )
            self._retry = 0

        except DeviceException as ex:
            self._retry = self._retry + 1
            if self._retry < self._retries:
                _LOGGER.info(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )

    @property
    def percentage(self) -> int | None:
        return self._percentage

    @property
    def preset_modes(self):
        return self._preset_modes

    @property
    def preset_mode(self):
        if self._state:
            return self._preset_mode
        return None

    async def async_set_natural_mode(self, enabled: bool):
        """Turn the natural mode on or off."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Setting fan natural mode of the miio device failed.",
            self._device.set_mode,
            OperationModeFanP33.Nature if enabled else OperationModeFanP33.Normal,
        )


class XiaomiFanP39(XiaomiFanMiot):
    """Representation of a Xiaomi Fan P39."""

    def __init__(
        self,
        name,
        device,
        model,
        unique_id,
        retries,
        preset_modes_override,
        firmware_version: str | None = None,
        hardware_version: str | None = None,
    ):
        """Initialize the fan entity."""
        super().__init__(
            name, device, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )

        self._device_features = FEATURE_FLAGS_FAN_P39
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN_P39
        self._percentage = None
        self._preset_modes = list(FAN_PRESET_MODES_P39)
        if preset_modes_override is not None:
            self._preset_modes = preset_modes_override

        self._preset_mode = None
        self._oscillate = None
        self._natural_mode = False

        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )

    @property
    def supported_features(self) -> int:
        return (
            FanEntityFeature.DIRECTION
            | FanEntityFeature.OSCILLATE
            | FanEntityFeature.PRESET_MODE
            | FanEntityFeature.SET_SPEED
            | FanEntityFeature.TURN_OFF
            | FanEntityFeature.TURN_ON
        )

    async def async_update(self):
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._percentage = state.fan_speed
            self._oscillate = state.oscillate
            self._natural_mode = state.mode == OperationModeFanP39.Nature
            self._state = state.power

            for preset_mode, value in FAN_PRESET_MODES_P39.items():
                if state.fan_level == value:
                    self._preset_mode = preset_mode
                    break

            self._state_attrs.update(
                {
                    key: self._extract_value_from_attribute(state, value)
                    for key, value in self._available_attributes.items()
                    if hasattr(state, value)
                }
            )
            self._retry = 0

        except DeviceException as ex:
            self._retry = self._retry + 1
            if self._retry < self._retries:
                _LOGGER.info(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )

    @property
    def percentage(self) -> int | None:
        return self._percentage

    @property
    def preset_modes(self):
        return self._preset_modes

    @property
    def preset_mode(self):
        if self._state:
            return self._preset_mode
        return None

    async def async_set_natural_mode(self, enabled: bool):
        """Turn the natural mode on or off."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Setting fan natural mode of the miio device failed.",
            self._device.set_mode,
            OperationModeFanP39.Nature if enabled else OperationModeFanP39.Normal,
        )


class XiaomiFanP76(XiaomiFanP33):
    """Representation of a Xiaomi Fan P76."""

    def __init__(
        self,
        name,
        device,
        model,
        unique_id,
        retries,
        preset_modes_override,
        firmware_version: str | None = None,
        hardware_version: str | None = None,
    ):
        super().__init__(
            name, device, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )

        self._device_features = FEATURE_FLAGS_FAN_P76
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN_P76
        self._percentage = None
        self._preset_modes = list(FAN_PRESET_MODES_P76)
        if preset_modes_override is not None:
            self._preset_modes = preset_modes_override

        self._preset_mode = None
        self._oscillate = None
        self._vertical_oscillate = None
        self._natural_mode = False

        self._state_attrs = {
            ATTR_MODEL: self._model,
            **{attribute: None for attribute in self._available_attributes},
        }

    @property
    def supported_features(self) -> int:
        return (
            FanEntityFeature.OSCILLATE
            | FanEntityFeature.PRESET_MODE
            | FanEntityFeature.SET_SPEED
            | FanEntityFeature.DIRECTION
            | FanEntityFeature.TURN_OFF
            | FanEntityFeature.TURN_ON
        )

    @property
    def current_direction(self) -> str:
        if self._vertical_oscillate is None:
            return None
        return "forward" if self._vertical_oscillate else "reverse"

    async def async_set_direction(self, direction: str) -> None:
        if direction == "forward":
            await self.async_set_vertical_oscillation(enabled=True)
            self._vertical_oscillate = True
        else:
            await self.async_set_vertical_oscillation(enabled=False)
            self._vertical_oscillate = False
        self.async_write_ha_state()

    async def async_update(self):
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._percentage = state.fan_speed
            self._oscillate = state.horizontal_swing
            self._vertical_oscillate = state.vertical_swing
            self._natural_mode = state.mode == OperationModeFanP76.Natural.name
            self._state = state.power

            for preset_mode, value in FAN_PRESET_MODES_P76.items():
                if preset_mode == SPEED_OFF:
                    continue
                is_natural = preset_mode.startswith("Natural")
                if state.fan_level == value and is_natural == self._natural_mode:
                    self._preset_mode = preset_mode
                    break

            self._state_attrs.update(
                {
                    key: self._extract_value_from_attribute(state, value)
                    for key, value in self._available_attributes.items()
                    if hasattr(state, value)
                }
            )
            self._retry = 0

        except DeviceException as ex:
            self._retry = self._retry + 1
            if self._retry < self._retries:
                _LOGGER.info(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        _LOGGER.debug("Setting the preset mode to: %s", preset_mode)

        if preset_mode == SPEED_OFF:
            await self.async_turn_off()
            return

        if not self._state:
            await self._try_command(
                "Turning the miio device on failed.", self._device.on
            )

        natural = preset_mode.startswith("Natural")
        await self._try_command(
            "Setting fan mode failed.",
            self._device.set_mode,
            OperationModeFanP76.Natural if natural else OperationModeFanP76.Straight,
        )
        await self._try_command(
            "Setting fan level of the miio device failed.",
            self._device.set_fan_level,
            FAN_PRESET_MODES_P76[preset_mode],
        )

    async def async_set_percentage(self, percentage: int) -> None:
        _LOGGER.debug("Setting the fan speed percentage to: %s", percentage)

        if percentage == 0:
            await self.async_turn_off()
            return

        if not self._state:
            await self._try_command(
                "Turning the miio device on failed.", self._device.on
            )
        await self._try_command(
            "Setting fan speed percentage of the miio device failed.",
            self._device.set_speed,
            percentage,
        )

    async def async_set_natural_mode(self, enabled: bool):
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return
        await self._try_command(
            "Setting fan natural mode of the miio device failed.",
            self._device.set_mode,
            OperationModeFanP76.Natural if enabled else OperationModeFanP76.Straight,
        )

    async def async_set_led_brightness(self, brightness: int = 1):
        """Set LED on (brightness > 0) or off (brightness == 0)."""
        if self._device_features & FEATURE_SET_LED == 0:
            return
        await self._try_command(
            "Setting LED of the miio device failed.",
            self._device.set_light,
            brightness > 0,
        )

    async def async_set_vertical_oscillation(self, enabled: bool):
        if self._device_features & FEATURE_SET_VERTICAL_OSCILLATION == 0:
            return
        await self._try_command(
            "Setting vertical oscillation of the miio device failed.",
            self._device.set_vertical_oscillate,
            enabled,
        )

    async def async_turn(self, direction: str):
        if self._device_features & FEATURE_TURN == 0:
            return
        await self._try_command(
            "Turning the miio device failed.",
            self._device.turn,
            direction,
        )


class XiaomiFanP70(XiaomiFanP33):
    """Representation of a Xiaomi Smart Desktop Air Circulation Fan P70."""

    def __init__(
        self,
        name,
        device,
        model,
        unique_id,
        retries,
        preset_modes_override,
        firmware_version: str | None = None,
        hardware_version: str | None = None,
    ):
        super().__init__(
            name, device, model, unique_id, retries, preset_modes_override,
            firmware_version=firmware_version, hardware_version=hardware_version,
        )

        self._device_features = FEATURE_FLAGS_FAN_P70
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN_P70
        self._percentage = None
        self._preset_modes = list(FAN_PRESET_MODES_P70)
        if preset_modes_override is not None:
            self._preset_modes = preset_modes_override

        self._preset_mode = None
        self._oscillate = None
        self._vertical_oscillate = None
        self._natural_mode = False

        self._state_attrs = {
            ATTR_MODEL: self._model,
            **{attribute: None for attribute in self._available_attributes},
        }

    @property
    def supported_features(self) -> int:
        return (
            FanEntityFeature.OSCILLATE
            | FanEntityFeature.PRESET_MODE
            | FanEntityFeature.SET_SPEED
            | FanEntityFeature.TURN_OFF
            | FanEntityFeature.TURN_ON
            | FanEntityFeature.DIRECTION
        )

    @property
    def current_direction(self) -> str:
        if self._vertical_oscillate is None:
            return None
        return "forward" if self._vertical_oscillate else "reverse"

    async def async_set_direction(self, direction: str) -> None:
        if direction == "forward":
            await self.async_set_vertical_oscillation(enabled=True)
            self._vertical_oscillate = True
        else:
            await self.async_set_vertical_oscillation(enabled=False)
            self._vertical_oscillate = False
        self.async_write_ha_state()

    async def async_update(self):
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._percentage = state.fan_speed
            self._oscillate = state.horizontal_swing
            self._vertical_oscillate = state.vertical_swing
            self._natural_mode = state.mode == OperationModeFanP70.Natural.name
            self._state = state.power

            for preset_mode, value in FAN_PRESET_MODES_P70.items():
                if state.fan_level == value:
                    self._preset_mode = preset_mode
                    break

            self._state_attrs.update(
                {
                    key: self._extract_value_from_attribute(state, value)
                    for key, value in self._available_attributes.items()
                    if hasattr(state, value)
                }
            )
            self._retry = 0

        except DeviceException as ex:
            self._retry = self._retry + 1
            if self._retry < self._retries:
                _LOGGER.info(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        _LOGGER.debug("Setting the preset mode to: %s", preset_mode)

        if preset_mode == SPEED_OFF:
            await self.async_turn_off()
            return

        if not self._state:
            await self._try_command(
                "Turning the miio device on failed.", self._device.on
            )
        await self._try_command(
            "Setting fan level of the miio device failed.",
            self._device.set_fan_level,
            FAN_PRESET_MODES_P70[preset_mode],
        )

    async def async_set_percentage(self, percentage: int) -> None:
        _LOGGER.debug("Setting the fan speed percentage to: %s", percentage)

        if percentage == 0:
            await self.async_turn_off()
            return

        if not self._state:
            await self._try_command(
                "Turning the miio device on failed.", self._device.on
            )
        await self._try_command(
            "Setting fan speed percentage of the miio device failed.",
            self._device.set_speed,
            percentage,
        )

    async def async_set_natural_mode(self, enabled: bool):
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return
        await self._try_command(
            "Setting fan natural mode of the miio device failed.",
            self._device.set_mode,
            OperationModeFanP70.Natural if enabled else OperationModeFanP70.Straight,
        )

    async def async_set_vertical_oscillation(self, enabled: bool):
        if self._device_features & FEATURE_SET_VERTICAL_OSCILLATION == 0:
            return
        await self._try_command(
            "Setting vertical oscillation of the miio device failed.",
            self._device.set_vertical_oscillate,
            enabled,
        )
