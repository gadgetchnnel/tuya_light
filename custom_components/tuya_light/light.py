"""Support for the Tuya lights."""
import logging

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_HS_COLOR,
    ENTITY_ID_FORMAT,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    SUPPORT_COLOR_TEMP,
    Light,
)
from homeassistant.util import color as colorutil

from . import DATA_TUYA, TuyaDevice, DOMAIN

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up Tuya light platform."""
    if discovery_info is None:
        return
    tuya = hass.data[DATA_TUYA]
    dev_ids = discovery_info.get("dev_ids")
    devices = []
    for dev_id in dev_ids:
        device = tuya.get_device_by_id(dev_id)
        if device is None:
            continue
        devices.append(TuyaLight(device))
    add_entities(devices)


class TuyaLight(TuyaDevice, Light):
    """Tuya light device."""

    def __init__(self, tuya):
        """Init Tuya light device."""
        super().__init__(tuya)
        self.entity_id = ENTITY_ID_FORMAT.format(tuya.object_id())

    @property
    def brightness(self):
        """Return the brightness of the light."""
        if self.tuya.brightness() is None:
            return None
        brightness = int(self.map_brightness(self.tuya.brightness(), 29, 255, 1, 255))
        return brightness

    @property
    def hs_color(self):
        """Return the hs_color of the light."""
        if "entity_data" in self.hass.data[DOMAIN] and self.tuya.object_id() in self.hass.data[DOMAIN]["entity_data"]:
          return self.hass.data[DOMAIN]["entity_data"][self.tuya.object_id()]["color"]
        else:
          return tuple(map(int, self.tuya.hs_color()))

    @property
    def color_temp(self):
        """Return the color_temp of the light."""
        color_temp = int(self.tuya.color_temp())
        if color_temp is None:
            return None
        return colorutil.color_temperature_kelvin_to_mired(color_temp)

    @property
    def is_on(self):
        """Return true if light is on."""
        return self.tuya.state()

    @property
    def min_mireds(self):
        """Return color temperature min mireds."""
        return colorutil.color_temperature_kelvin_to_mired(self.tuya.min_color_temp())

    @property
    def max_mireds(self):
        """Return color temperature max mireds."""
        return colorutil.color_temperature_kelvin_to_mired(self.tuya.max_color_temp())

    def map_brightness(self, brightness, old_min_value, old_max_value, new_min_value, new_max_value):
        if brightness == new_max_value:
            return brightness
        else:
            slope = (float(new_max_value) - float(new_min_value)) / (float(old_max_value) - float(old_min_value))
            mapped_brightness = int(float(new_min_value) + slope * (float(brightness) - float(old_min_value)))
            if mapped_brightness < new_min_value:
                mapped_brightness = new_min_value
            return mapped_brightness

    def turn_on(self, **kwargs):
        """Turn on or control the light."""
        if (
            ATTR_BRIGHTNESS not in kwargs
            and ATTR_HS_COLOR not in kwargs
            and ATTR_COLOR_TEMP not in kwargs
        ):
            self.tuya.turn_on()
        if ATTR_BRIGHTNESS in kwargs:
            brightness = self.map_brightness(kwargs[ATTR_BRIGHTNESS], 1, 255, 29, 255)
            self.tuya.set_brightness(brightness)
        if ATTR_HS_COLOR in kwargs:
            self.tuya.set_color(kwargs[ATTR_HS_COLOR])
            if not "entity_data" in self.hass.data[DOMAIN]:
              self.hass.data[DOMAIN] = {"entity_data": {}}
            self.hass.data[DOMAIN]["entity_data"][self.tuya.object_id()] = {"color": kwargs[ATTR_HS_COLOR]}
        if ATTR_COLOR_TEMP in kwargs:
            color_temp = colorutil.color_temperature_mired_to_kelvin(
                kwargs[ATTR_COLOR_TEMP]
            )
            self.tuya.set_color_temp(color_temp)

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        self.tuya.turn_off()

    @property
    def supported_features(self):
        """Flag supported features."""
        supports = SUPPORT_BRIGHTNESS | SUPPORT_COLOR
        if self.tuya.support_color_temp():
            supports = supports | SUPPORT_COLOR_TEMP
        return supports
