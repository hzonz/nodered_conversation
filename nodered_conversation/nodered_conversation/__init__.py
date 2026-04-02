# custom_components/nodered_agent/__init__.py 完整版

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

PLATFORMS = ["conversation"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """加载集成实例."""
    # 转发加载请求给 conversation 平台
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载集成实例."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)