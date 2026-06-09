"""Node-RED Conversation 集成入口."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# 定义支持的平台
PLATFORMS: list[Platform] = [Platform.CONVERSATION]

@dataclass
class NodeRedRuntimeData:
    """存放集成运行时的内存数据容器。"""
    # 注册表：用于匹配异步响应 {conversation_id: Future}
    pending_requests: dict[str, Any] 
    # 也可以在这里存放全局 API 客户端等
    # client: NodeRedClient

type NodeRedConfigEntry = ConfigEntry[NodeRedRuntimeData]

async def async_setup_entry(hass: HomeAssistant, entry: NodeRedConfigEntry) -> bool:
    """设置集成配置条目."""
    
    # 初始化运行时数据
    # 这解决了“谁来持有注册表”的问题，使其在整个集成生命周期内可用
    entry.runtime_data = NodeRedRuntimeData(
        pending_requests={}
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
    """卸载配置条目."""
    
    # 卸载平台实体
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok