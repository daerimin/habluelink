from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from .bluelink import BlueLink
from .const import DOMAIN


def setup_platform(hass: HomeAssistant, config: ConfigEntry, add_entities: AddEntitiesCallback,
                   discovery_info: DiscoveryInfoType | None = None) -> None:
    if config.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][config.entry_id] = {}
    if 'bluelink' not in hass.data[DOMAIN][config.entry_id]:
        bluelink = BlueLink(hass, config)
        bluelink.setup()
        hass.data[DOMAIN][config.entry_id]['bluelink'] = bluelink
    entities = []
    for vin in (hass.data[DOMAIN][config.entry_id]['bluelink']).vehicles:
        entities.append(FuelLevelSensor(hass, config, vin))
        entities.append(CarWindowsOpenSensor(hass, config, vin))
        entities.append(TirePressureWarningSensor(hass, config, vin))
        entities.append(CarDoorsLockedSensor(hass, config, vin))
        entities.append(VehicleLocationSensor(hass, config, vin))
        entities.append(VehicleOdometerSensor(hass, config, vin))
    return add_entities(entities)


async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry, async_add_entities) -> bool:
    if config.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][config.entry_id] = {}
    if 'bluelink' not in hass.data[DOMAIN][config.entry_id]:
        bluelink = BlueLink(hass, config)
        await bluelink.setup()
        hass.data[DOMAIN][config.entry_id]['bluelink'] = bluelink
    entities = []
    for vin in (hass.data[DOMAIN][config.entry_id]['bluelink']).vehicles:
        entities.append(FuelLevelSensor(hass, config, vin))
        entities.append(CarWindowsOpenSensor(hass, config, vin))
        entities.append(TirePressureWarningSensor(hass, config, vin))
        entities.append(CarDoorsLockedSensor(hass, config, vin))
        entities.append(VehicleLocationSensor(hass, config, vin))
        entities.append(VehicleOdometerSensor(hass, config, vin))
    async_add_entities(entities)


class CarDeviceEntity(SensorEntity):
    """Base class for a car device entity."""

    def __init__(self, hass: HomeAssistant, config: ConfigEntry, vin: str):
        self._hass = hass
        self._config = config
        self._vin = vin
        self._attr_unique_id = f"{vin}_vehicle"

    @property
    def device_info(self):
        vehicle = self._hass.data[DOMAIN][self._config.entry_id]['bluelink'].vehicles[self._vin]
        return {
            "identifiers": {(DOMAIN, self._vin)},
            "name": vehicle['vehicleDetails']['nickName'],
            "manufacturer": "Hyundai",
            "entry_type": DeviceEntryType.SERVICE,
            "model": vehicle['vehicleDetails']['nickName']
        }


class FuelLevelSensor(CarDeviceEntity):
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:gas-station"
    _attr_name = "Fuel Level"

    def __init__(self, hass: HomeAssistant, config: ConfigEntry, vin: str):
        super().__init__(hass, config, vin)
        self._attr_unique_id = f"{vin}_fuel_level"
        vehicle = hass.data[DOMAIN][config.entry_id]['bluelink'].vehicles[vin]
        self._attr_name = f"{vehicle['vehicleDetails']['nickName']} Fuel Level"

    def update(self) -> None:
        vehicle = self._hass.data[DOMAIN][self._config.entry_id]['vehicles'][self._vin]
        self._attr_native_value = int(vehicle['vehicleStatus']['fuelLevel'])


class CarWindowsOpenSensor(CarDeviceEntity):
    _attr_icon = "mdi:car-door"
    _attr_name = "Car Windows Open"

    def __init__(self, hass: HomeAssistant, config: ConfigEntry, vin: str):
        super().__init__(hass, config, vin)
        self._attr_unique_id = f"{vin}_car_windows_open"
        vehicle = hass.data[DOMAIN][config.entry_id]['bluelink'].vehicles[vin]
        self._attr_name = f"{vehicle['vehicleDetails']['nickName']} Windows Open"

    def update(self) -> None:
        vehicle = self._hass.data[DOMAIN][self._config.entry_id]['vehicles'][self._vin]
        all_windows_closed = all(value == 0 for value in vehicle['vehicleStatus']['windowOpen'].values())
        sunroof_closed = not vehicle['vehicleStatus']['sunroofOpen']
        trunk_closed = not vehicle['vehicleStatus']['trunkOpen']
        all_closed = all_windows_closed and sunroof_closed and trunk_closed
        self._attr_native_value = not all_closed


class TirePressureWarningSensor(CarDeviceEntity):
    _attr_icon = "mdi:car-tire-alert"
    _attr_name = "Tire Pressure Warning"

    def __init__(self, hass: HomeAssistant, config: ConfigEntry, vin: str):
        super().__init__(hass, config, vin)
        self._attr_unique_id = f"{vin}_tire_pressure_warning"
        vehicle = hass.data[DOMAIN][config.entry_id]['bluelink'].vehicles[vin]
        self._attr_name = f"{vehicle['vehicleDetails']['nickName']} Tire Pressure Warning"

    def update(self) -> None:
        vehicle = self._hass.data[DOMAIN][self._config.entry_id]['vehicles'][self._vin]
        self._attr_native_value = any(value != 0 for value in vehicle['vehicleStatus']['tirePressureLamp'].values())


class CarDoorsLockedSensor(CarDeviceEntity):
    _attr_icon = "mdi:car-key"
    _attr_name = "Car Doors Locked"

    def __init__(self, hass: HomeAssistant, config: ConfigEntry, vin: str):
        super().__init__(hass, config, vin)
        self._attr_unique_id = f"{vin}_car_doors_locked"
        vehicle = hass.data[DOMAIN][config.entry_id]['bluelink'].vehicles[vin]
        self._attr_name = f"{vehicle['vehicleDetails']['nickName']} Doors Locked"

    def update(self) -> None:
        vehicle = self._hass.data[DOMAIN][self._config.entry_id]['vehicles'][self._vin]
        self._attr_native_value = vehicle['vehicleStatus']['doorLock']


class VehicleLocationSensor(CarDeviceEntity):
    _attr_icon = "mdi:map-marker"
    _attr_name = "Vehicle Location"

    def __init__(self, hass: HomeAssistant, config: ConfigEntry, vin: str):
        super().__init__(hass, config, vin)
        self._attr_unique_id = f"{vin}_vehicle_location"
        vehicle = hass.data[DOMAIN][config.entry_id]['bluelink'].vehicles[vin]
        self._attr_name = f"{vehicle['vehicleDetails']['nickName']} Location"

    def update(self) -> None:
        vehicle = self._hass.data[DOMAIN][self._config.entry_id]['vehicles'][self._vin]
        lat = vehicle['vehicleStatus']['vehicleLocation']['coord']['lat']
        lon = vehicle['vehicleStatus']['vehicleLocation']['coord']['lon']
        self._attr_native_value = (lat, lon)


class VehicleOdometerSensor(CarDeviceEntity):
    _attr_icon = "mdi:counter"
    _attr_name = "Vehicle Odometer"

    def __init__(self, hass: HomeAssistant, config: ConfigEntry, vin: str):
        super().__init__(hass, config, vin)
        self._attr_unique_id = f"{vin}_vehicle_odometer"
        vehicle = hass.data[DOMAIN][config.entry_id]['bluelink'].vehicles[vin]
        self._attr_name = f"{vehicle['vehicleDetails']['nickName']} Odometer"

    def update(self) -> None:
        vehicle = self._hass.data[DOMAIN][self._config.entry_id]['vehicles'][self._vin]
        self._attr_native_value = int(vehicle['vehicleStatus']['odometer'])
