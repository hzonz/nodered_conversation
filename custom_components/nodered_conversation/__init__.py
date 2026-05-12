"""Node-RED Conversation 集成入口."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

# 定义支持的平台枚举
PLATFORMS: list[Platform] = [Platform.CONVERSATION]

# 如果你有需要共享的 Client 或 Coordinator，可以定义在这里
# type NodeRedConfigEntry = ConfigEntry[None] 

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """从配置条目设置集成."""
    
    # 2026 规范：直接使用 async_forward_entry_setups 加载平台
    # 这将触发 conversation.py 文件的加载
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载配置条目."""
    
    # 卸载平台实体
    # 只要在 conversation.py 中使用了 ConversationEntity，
    # HA 的基础组件会自动处理 Agent 的卸载逻辑，无需手动调用 async_unset_agent。
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
