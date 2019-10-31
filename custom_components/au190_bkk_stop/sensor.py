import asyncio
from datetime import timedelta
import logging
import aiohttp
import async_timeout
import voluptuous as vol
import sys

from random import randrange
from homeassistant.exceptions import PlatformNotReady
from datetime import datetime
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_ATTRIBUTION, CONF_NAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_call_later

_LOGGER = logging.getLogger(__name__)

BKK_URI="https://futar.bkk.hu/api/query/v1/ws/otp/api/where/arrivals-and-departures-for-stop.json?key=apaiary-test&version=3&appVersion=apiary-1.0&onlyDepartures=true&stopId={stopId}&minutesAfter={minutesAfter}"
SCAN_INTERVAL = timedelta(seconds = 120)
REQUEST_TIMEOUT = 3


CONF_ATTRIBUTES = ("Information provided by: https://futar.bkk.hu/")
CONF_STOPID = 'stopId'
CONF_MINSAFTER = 'minsAfter'
CONF_WHEELCHAIR = 'wheelchair'
CONF_BIKES = 'bikes'
CONF_IGNORENOW = 'ignoreNow'

DEFAULT_NAME = 'BKK Futar'
DEFAULT_ICON = 'mdi:bus'
DEFAULT_UNIT = 'min'


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_STOPID): cv.string,
    vol.Optional(CONF_MINSAFTER, default=20): cv.string,
    vol.Optional(CONF_WHEELCHAIR, default=False): cv.boolean,
    vol.Optional(CONF_BIKES, default=False): cv.boolean,
    vol.Optional(CONF_IGNORENOW, default='false'): cv.boolean,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    _LOGGER.debug("[" + sys._getframe().f_code.co_name + "]--> %s", config.get(CONF_NAME))

    name = config.get(CONF_NAME)
    stopid = config.get(CONF_STOPID)
    minsafter = config.get(CONF_MINSAFTER)
    wheelchair = config.get(CONF_WHEELCHAIR)
    bikes = config.get(CONF_BIKES)
    ignorenow = config.get(CONF_IGNORENOW)

    #api_sensor = BKKPublicTransportSensor(name, stopid, minsafter, wheelchair, bikes, ignorenow)
    #async_add_entities([api_sensor], update_before_add=False)


    dev = []
    api = CallAPI(hass, config)

    #data = await api.get_json()
    #_LOGGER.debug("[" + sys._getframe().f_code.co_name + "] %s", data)

    dev.append(BKKPublicTransportSensor(api, name, stopid, minsafter, wheelchair, bikes, ignorenow))
    async_add_entities(dev, True)


class myRequestError(Exception):
    """Error to indicate a API request has failed."""

    pass

class BKKPublicTransportSensor(Entity):
    """BKKPublicTransportSensor API Sensor."""

    def __init__(self, api, name, stopid, minsafter, wheelchair, bikes, ignorenow):
        """Initialize the sensor."""

        self._api = api
        self._name = name
        self._stopid = stopid
        self._minsafter = minsafter
        self._wheelchair = wheelchair
        self._bikes = bikes
        self._ignorenow = ignorenow
        self._state = None
        self._attributes = {}

    async def async_update(self):
        """Update station state."""
        try:
            _LOGGER.debug("[" + sys._getframe().f_code.co_name + "]--> %s", self.name)

            json_response = await self._api.get_json()

            if json_response["status"] == "OK" and len(json_response["data"]["entry"]["stopTimes"]) > 0:

                bkkdata = json_response
                attr = {}
                attr["stationName"] = bkkdata["data"]["references"]["stops"][self._stopid]["name"]
                attr["items"] = len(bkkdata["data"]["entry"]["stopTimes"])
                attr["updated"] =  str(datetime.now().strftime("%H:%M"))
                failedNode = 0
                if attr["items"] != 0:
                    currenttime = int(bkkdata["currentTime"] / 1000)
                    i = 0
                    while i < len(bkkdata["data"]["entry"]["stopTimes"]) - failedNode:
                        if 'departureTime' not in bkkdata["data"]["entry"]["stopTimes"][i + failedNode]:
                            failedNode += 1
                            continue

                        diff = 0
                        diff = int((bkkdata["data"]["entry"]["stopTimes"][i + failedNode]["departureTime"] - currenttime) / 60)
                        if diff < 0:
                            diff = 0
                        if self._ignorenow and diff == 0:
                            failedNode += 1
                            continue

                        attr['in' + str(i)] = diff
                        tripid = bkkdata["data"]["entry"]["stopTimes"][i + failedNode]["tripId"]
                        routeid = bkkdata["data"]["references"]["trips"][tripid]["routeId"]
                        attr['type' + str(i)] = bkkdata["data"]["references"]["routes"][routeid]["type"]
                        attr['routeid' + str(i)] = bkkdata["data"]["references"]["routes"][routeid]["iconDisplayText"]
                        attr['headsign' + str(i)] = bkkdata["data"]["entry"]["stopTimes"][i + failedNode]["stopHeadsign"]

                        if self._wheelchair:
                            if 'wheelchairAccessible' in bkkdata["data"]["references"]["trips"][tripid]:
                                attr['wheelchair' + str(i)] = str(
                                    bkkdata["data"]["references"]["trips"][tripid]["wheelchairAccessible"])

                        if self._bikes:
                            if 'bikesAllowed' in bkkdata["data"]["references"]["trips"][tripid]:
                                attr['bikesallowed' + str(i)] = bkkdata["data"]["references"]["trips"][tripid]["bikesAllowed"]

                        i += 1
                attr["items"] = len(bkkdata["data"]["entry"]["stopTimes"]) - failedNode

                self._attributes = attr
                self._state = "[" + datetime.now().strftime("%H:%M") + "] " + str(self._minsafter)

                if 'in0' in self._attributes.keys():
                    self._state = "[" + datetime.now().strftime("%H:%M") + "] " + str(self._attributes['in0'])
                #_LOGGER.debug("async_updatex: %s", self._state)

        except Exception as e:
            pass
            #_LOGGER.error("[" + sys._getframe().f_code.co_name + "] Exception: " + str(e))

    @property
    def state(self):
        """Return the state of the sensor."""
        #_LOGGER.debug("[" + sys._getframe().f_code.co_name + "]--> %s %s", self.name, self._state)
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        #_LOGGER.debug("[" + sys._getframe().f_code.co_name + "]--> %s", self.name)

        if self._attributes:
            return self._attributes
        return {ATTR_ATTRIBUTION: CONF_ATTRIBUTES}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Return the icon."""
        return DEFAULT_ICON

    @property
    def unit_of_measurement(self):
        return DEFAULT_UNIT



class CallAPI:
    """Call API."""

    def __init__(self, hass, config):
        """Initialize."""

        self.hass = hass
        self.session = async_get_clientsession(hass)
        self.loop = hass.loop
        self.name = config.get(CONF_NAME)
        self.stopid = config.get(CONF_STOPID)
        self.minsafter = config.get(CONF_MINSAFTER)

    async def get_json(self):
        """Get json from API endpoint."""
        _LOGGER.debug("[" + sys._getframe().f_code.co_name + "]--> %s", self.name)

        value = None
        url = BKK_URI.format(stopId=self.stopid, minutesAfter=self.minsafter)

        #Hacking in rassbery pi it is not allowed to retreive only 2 query at once
        queryTry = 3
        while queryTry >= 1:

            queryTry = queryTry - 1

            try:
                async with async_timeout.timeout(REQUEST_TIMEOUT, loop=self.loop):
                    response = await self.session.get(url)
                    value = await response.json()
                    queryTry = 0

            except (asyncio.TimeoutError) as err:
                #_LOGGER.error("[" + sys._getframe().f_code.co_name + "] %s TimeoutError: %s", self.name, err)
                pass
            except (aiohttp.ClientError) as err:
                _LOGGER.error("[" + sys._getframe().f_code.co_name + "] %s aiohttp.ClientError %s", self.name, err)
                pass
            except Exception as err:
                _LOGGER.error("[" + sys._getframe().f_code.co_name + "] %s Exception: %s", self.name, err)
                pass


        _LOGGER.debug("[" + sys._getframe().f_code.co_name + "]<-- %s", self.name)
        return value
