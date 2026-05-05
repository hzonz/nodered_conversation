"""Node-RED Conversation 集成入口."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from homeassistant.components import conversation
from .const import DOMAIN

PLATFORMS: list[str] = ["conversation"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """从配置条目设置集成."""

    # 加载 ConversationEntity
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载配置条目."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    conversation.async_unset_agent(hass, entry)

    return unload_ok
