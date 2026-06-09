"""Node-RED Conversation 集成入口."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN, PLATFORMS
from .types import NodeRedConfigEntry, NodeRedRuntimeData

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: NodeRedConfigEntry) -> bool:
    """设置集成配置条目."""
    
    integration = await async_get_integration(hass, DOMAIN)

    entry.runtime_data = NodeRedRuntimeData(
        pending_requests={},
        version=str(integration.version or "1.0.0"),
        unsub_listener=None
    )

    # 注册选项更新监听器 (用于动态修改超时等设置)
    entry.async_on_unload(entry.add_update_listener(update_listener))

    # 加载平台 (如 conversation.py)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def update_listener(hass: HomeAssistant, entry: NodeRedConfigEntry) -> None:
    """处理选项更新（当用户在 UI 修改了超时时间等）。"""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: NodeRedConfigEntry) -> bool:
    """卸载集成."""
    # 卸载时清理监听器
    if entry.runtime_data.unsub_listener:
        entry.runtime_data.unsub_listener()
        
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)