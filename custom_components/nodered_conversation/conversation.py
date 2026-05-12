"""Node-Red 异步对话代理平台实现."""
from __future__ import annotations

import logging
import asyncio
import re
from typing import Any

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import intent
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# 2026 规范：直接使用 asyncio 自带的 timeout (Python 3.11+)
REQUEST_TIMEOUT = 30
# 预编译正则：匹配开头的 [任何内容|任何内容] 以及紧随其后的空格
IM_PREFIX_PATTERN = re.compile(r"^\[.*?\|.*?\]\s*")

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """初始化 Node-Red 对话实体."""
    # 直接添加实体即可。在现代 HA 中，继承了 ConversationEntity 的实体
    # 会被系统自动识别为对话代理，无需再手动调用 async_set_agent。
    async_add_entities([NodeRedAsyncConversationEntity(config_entry)])


class NodeRedAsyncConversationEntity(conversation.ConversationEntity):
    """基于事件驱动的 Node-RED 异步对话实体."""

    # 使用翻译键，以便在 strings.json 中定义名称
    _attr_has_entity_name = True
    _attr_translation_key = "nodered_agent" 

    def __init__(self, entry: ConfigEntry) -> None:
        """初始化."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}-async-agent"
        
        # 2026 规范：不要手动设置 entity_id，让 HA 根据 unique_id 和名称自动生成
        # 如果必须固定，建议在配置流中处理
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Node-RED Bridge",
            manufacturer="Node-RED Custom",
            model="Event-Based v2",
            sw_version=entry.version,
        )

    @property
    def supported_languages(self) -> list[str] | str:
        """支持的语言。返回 MATCH_ALL 表示支持所有 HA 配置的语言。"""
        return ["zh-Hans", "zh-Hant", "en"]

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """处理对话逻辑."""
        
        request_id = user_input.conversation_id or "default"
        raw_text = user_input.text
        
        # 1. 清洗文本
        clean_text = IM_PREFIX_PATTERN.sub("", raw_text)
        
        # 2. 创建异步 Future 对象
        future: asyncio.Future[str] = asyncio.get_running_loop().create_future()

        @callback
        def handle_response_event(event):
            """监听 Node-RED 回传的事件."""
            # 增加对 event.data 的安全性检查
            if event.data.get("request_id") == request_id:
                response_text = event.data.get("response", "无响应内容")
                if not future.done():
                    future.set_result(str(response_text))

        # 3. 注册监听器（确保在 fire 事件之前注册）
        unsub = self.hass.bus.async_listen(
            "nodered_response_event", 
            handle_response_event
        )

        try:
            # 4. 触发请求事件
            self.hass.bus.async_fire("nodered_request_event", {
                "request_id": request_id,
                "text": clean_text,
                "conversation_id": user_input.conversation_id,
                "language": user_input.language,
                "device_id": user_input.device_id, # 2026 新增：透传设备 ID 方便溯源
            })

            # 5. 使用原生 asyncio 任务管理和超时
            async with asyncio.timeout(REQUEST_TIMEOUT):
                final_response = await future

        except TimeoutError:
            _LOGGER.warning("Node-RED 对话请求超时: %s", request_id)
            final_response = "抱歉，Node-RED 响应超时，请稍后再试。"
        except Exception as err:
            _LOGGER.error("处理对话时发生未知错误: %s", err)
            final_response = f"抱歉，发生了系统错误：{err}"
        finally:
            # 6. 务必销毁监听器，防止内存泄漏
            unsub()

        # 7. 构建响应
        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(final_response)

        return conversation.ConversationResult(
            response=intent_response,
            conversation_id=user_input.conversation_id
        )
