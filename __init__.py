from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError

from .const import DOMAIN


def setup(hass: HomeAssistant, config: ConfigEntry) -> bool:

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    async def handle_update_sensors(call: ServiceCall) -> bool:
        success = False
        for entry_id in hass.data[DOMAIN]:
            this_config = hass.data[DOMAIN][entry_id]
            if "vin" in call.data:
                found = False
                vehicles = this_config['vehicles']
                for vin in vehicles:
                    if vin == call.data['vin']:
                        found = True
                if not found:
                    continue
            this_bluelink = this_config['bluelink']
            await this_bluelink.setup(force=True)
            success = True
        return success

    async def handle_lock_vehicle(call: ServiceCall) -> bool:
        if "vin" not in call.data:
            raise ServiceValidationError("Missing VIN")
        for entry_id in hass.data[DOMAIN]:
            this_config = hass.data[DOMAIN][entry_id]
            vehicles = this_config['vehicles']
            if call.data['vin'] in vehicles:
                print(f"Locking vehicle {call.data['vin']}")
                this_bluelink = this_config['bluelink']
                success = await this_bluelink.lock_vehicle(vin=call.data['vin'])
                print(f"Success: {success}")
                return success
        return False

    async def handle_unlock_vehicle(call) -> bool:
        if "vin" not in call.data:
            raise ServiceValidationError("Missing VIN")
        for entry_id in hass.data[DOMAIN]:
            this_config = hass.data[DOMAIN][entry_id]
            vehicles = this_config['vehicles']
            if call.data['vin'] in vehicles:
                print(f"Unlocking vehicle {call.data['vin']}")
                this_bluelink = this_config['bluelink']
                success = await this_bluelink.unlock_vehicle(vin=call.data['vin'])
                print(f"Success: {success}")
                return success
        return False

    async def handle_start_vehicle(call) -> bool:
        if "vin" not in call.data:
            raise ServiceValidationError("Missing VIN")
        for entry_id in hass.data[DOMAIN]:
            this_config = hass.data[DOMAIN][entry_id]
            vehicles = this_config['vehicles']
            if call.data['vin'] in vehicles:
                print(f"Starting vehicle {call.data['vin']}")
                this_bluelink = this_config['bluelink']
                success = await this_bluelink.start_vehicle(vin=call.data['vin'])
                print(f"Success: {success}")
                return success
        return False

    hass.services.register(DOMAIN, "update_sensors", handle_update_sensors)
    hass.services.register(DOMAIN, "lock_vehicle", handle_lock_vehicle)
    hass.services.register(DOMAIN, "unlock_vehicle", handle_unlock_vehicle)
    hass.services.register(DOMAIN, "start_vehicle", handle_start_vehicle)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    success = await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    if success:
        hass.data[DOMAIN].push(entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    success = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if success:
        hass.data[DOMAIN].pop(entry.entry_id)
    return success
