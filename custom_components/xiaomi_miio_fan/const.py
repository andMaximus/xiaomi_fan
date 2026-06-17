"""Constants for the Xiaomi Mi Smart Pedestal Fan integration."""

from homeassistant.const import Platform

DOMAIN = "xiaomi_miio_fan"
PLATFORMS = [Platform.FAN]

DEFAULT_NAME = "Xiaomi Miio Fan"
DEFAULT_RETRIES = 3

CONF_MODEL = "model"
CONF_RETRIES = "retries"
CONF_PRESET_MODES_OVERRIDE = "preset_modes_override"
CONF_MAC = "mac"
CONF_FIRMWARE_VERSION = "firmware_version"
CONF_HARDWARE_VERSION = "hardware_version"

MODEL_FAN_V2 = "zhimi.fan.v2"
MODEL_FAN_V3 = "zhimi.fan.v3"
MODEL_FAN_SA1 = "zhimi.fan.sa1"
MODEL_FAN_ZA1 = "zhimi.fan.za1"
MODEL_FAN_ZA3 = "zhimi.fan.za3"
MODEL_FAN_ZA4 = "zhimi.fan.za4"
MODEL_FAN_ZA5 = "zhimi.fan.za5"
MODEL_FAN_P5 = "dmaker.fan.p5"
MODEL_FAN_P8 = "dmaker.fan.p8"
MODEL_FAN_P9 = "dmaker.fan.p9"
MODEL_FAN_P10 = "dmaker.fan.p10"
MODEL_FAN_P11 = "dmaker.fan.p11"
MODEL_FAN_P15 = "dmaker.fan.p15"
MODEL_FAN_P18 = "dmaker.fan.p18"
MODEL_FAN_P30 = "dmaker.fan.p30"
MODEL_FAN_P33 = "dmaker.fan.p33"
MODEL_FAN_P39 = "dmaker.fan.p39"
MODEL_FAN_P76 = "xiaomi.fan.p76"
MODEL_FAN_P70 = "xiaomi.fan.p70"
MODEL_FAN_LESHOW_SS4 = "leshow.fan.ss4"
MODEL_FAN_1C = "dmaker.fan.1c"
