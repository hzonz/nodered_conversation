"""定义集成通用的数据类型."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from homeassistant.core import CALLBACK_TYPE

@dataclass
class NodeRedRuntimeData:
    """存放集成运行时的内存数据容器 (2026.6 归一版)."""
    # 注册表：{conversation_id: Future}
    pending_requests: dict[str, asyncio.Future[dict[str, Any]]]
    # 从 manifest 获取的版本号
    version: str
    # 全局事件监听器的取消函数
    unsub_listener: CALLBACK_TYPE | None = None

# 定义类型别名
type NodeRedConfigEntry = ConfigEntry[NodeRedRuntimeData]