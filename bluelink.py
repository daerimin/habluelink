import ssl
import aiohttp
import json
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN
from .functions import proper_case


def create_ssl_context():
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    # Allow unsafe SSL renegotiation
    context.options |= ssl.OP_LEGACY_SERVER_CONNECT

    return context


class BlueLink:
    HOST = "api.telematics.hyundaiusa.com"
    CLIENTID = "m66129Bb-em93-SPAHYN-bZ91-am4540zp19920"
    SECRET = "v558o935-6nne-423i-baa8"

    hass: HomeAssistant = None
    config: ConfigEntry = None

    token: str = ""
    refreshToken: str = ""
    tokenExpires: int = 0

    vehicles = {}

    def __init__(self, hass: HomeAssistant, config: ConfigEntry):
        self.hass = hass
        self.config = config

    async def setup(self, force: bool = False):

        if force:
            self.token = ""
            self.tokenExpires = 0
            self.refreshToken = ""
            self.vehicles = {}

        if not self.token:
            await self.get_token()
        if self.tokenExpires < time.time():
            await self.refresh_token()
        if not self.vehicles:
            await self.get_vehicles()

        self.hass.data[DOMAIN][self.config.entry_id]['vehicles'] = {}

        for vin in self.vehicles:
            status = await self.get_status(vin)
            self.hass.data[DOMAIN][self.config.entry_id]['vehicles'][vin] = status
            print(f"Received status for vehicle {vin}")

    async def get_token(self):
        url = f"https://{self.HOST}/v2/ac/oauth/token"
        headers = {
            'User-Agent': 'PostmanRuntime/7.26.10',
            'client_secret': self.SECRET,
            'client_id': self.CLIENTID
        }
        params = {'username': self.config.data['username'], 'password': self.config.data['password']}

        ssl_context = create_ssl_context()
        async with async_get_clientsession(self.hass).post(url, headers=headers, json=params,
                                                           ssl=ssl_context) as response:
            response.raise_for_status()
            json_response = await response.json()

            self.token = json_response['access_token']
            self.refreshToken = json_response['refresh_token']
            self.tokenExpires = time.time() + int(json_response['expires_in'])
            print("Token retrieved.")

    async def refresh_token(self):
        url = f"https://{self.HOST}/v2/ac/oauth/token/refresh"
        headers = {
            'User-Agent': 'PostmanRuntime/7.26.10',
            'client_secret': self.SECRET,
            'client_id': self.CLIENTID
        }
        params = {'refresh_token': self.refreshToken}

        ssl_context = create_ssl_context()
        async with async_get_clientsession(self.hass).post(url, headers=headers, json=params,
                                                           ssl=ssl_context) as response:
            response.raise_for_status()
            json_response = await response.json()

            if 'access_token' not in json_response:
                await self.get_token()
                return

            self.token = json_response['access_token']
            self.refreshToken = json_response['refresh_token']
            self.tokenExpires = time.time() + int(json_response['expires_in'])
            print("Token refreshed.")

    async def get_vehicles(self):
        url = f"https://{self.HOST}/ac/v2/enrollment/details/{self.config.data['username']}"
        headers = {
            'access_token': self.token,
            'client_id': self.CLIENTID,
            'Host': self.HOST,
            'User-Agent': 'okhttp/3.12.0',
            'payloadGenerated': '20200226171938',
            'includeNonConnectedVehicles': 'N'
        }

        ssl_context = create_ssl_context()
        async with async_get_clientsession(self.hass).get(url, headers=headers, ssl=ssl_context) as response:
            response.raise_for_status()
            json_response = await response.json()

            for vehicle in json_response['enrolledVehicleDetails']:
                vin = vehicle['vehicleDetails']['vin']
                vehicle['vehicleDetails']['nickName'] = proper_case(vehicle['vehicleDetails']['nickName'])
                self.vehicles[vin] = vehicle
            print("Vehicles updated.")

    def get_headers(self, vin: str):
        veh = self.vehicles[vin]['vehicleDetails']
        return {
            'access_token': self.token,
            'client_id': self.CLIENTID,
            'Host': self.HOST,
            'User-Agent': 'okhttp/3.12.0',
            'registrationId': veh['regid'],
            'gen': veh['vehicleGeneration'],
            'username': self.config.data['username'],
            'vin': veh['vin'],
            'APPCLOUD-VIN': veh['vin'],
            'Language': '0',
            'to': 'ISS',
            'encryptFlag': 'false',
            'from': 'SPA',
            'brandIndicator': 'hyundai',
            'bluelinkservicepin': self.config.data['pin'],
            'offset': '-4'
        }

    async def get_status(self, vin: str):
        url = f"https://{self.HOST}/ac/v2/rcs/rvs/vehicleStatus"
        headers = self.get_headers(vin=vin)
        headers['REFRESH'] = 'true'
        ssl_context = create_ssl_context()
        async with async_get_clientsession(self.hass).get(url, headers=headers, ssl=ssl_context) as response:
            response.raise_for_status()
            return await response.json()

    async def lock_vehicle(self, vin: str):
        url = f"https://{self.HOST}/ac/v2/rcs/rdo/off"
        headers = self.get_headers(vin=vin)
        body = {'userName': self.config.data['username'], 'vin': vin}
        ssl_context = create_ssl_context()
        async with async_get_clientsession(self.hass).post(url, headers=headers, json=body,
                                                           ssl=ssl_context) as response:
            response.raise_for_status()
            return response.status == 200

    async def unlock_vehicle(self, vin: str):
        url = f"https://{self.HOST}/ac/v2/rcs/rdo/on"
        headers = self.get_headers(vin=vin)
        body = {'userName': self.config.data['username'], 'vin': vin}

        ssl_context = create_ssl_context()
        async with async_get_clientsession(self.hass).post(url, headers=headers, json=body,
                                                           ssl=ssl_context) as response:
            response.raise_for_status()
            return response.status == 200

    async def start_vehicle(self, vin: str):
        url = f"https://{self.HOST}/ac/v2/rcs/rsc/start"
        headers = self.get_headers(vin=vin)
        body = {
            'Ims': '0',
            'airCtrl': '1',
            'airTemp': {
                'unit': '1',
                'value': '70'
            },
            'defrost': 'false',
            'heating1': '0',
            'igniOnDuration': '10',
            'seatHeaterVentInfo': None,
            'username': self.config.data['username'],
            'vin': vin
        }

        ssl_context = create_ssl_context()
        async with async_get_clientsession(self.hass).post(url, headers=headers, json=body,
                                                           ssl=ssl_context) as response:
            response.raise_for_status()
            return response.status == 200
