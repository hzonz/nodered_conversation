"""Node-Red 异步对话代理."""
from __future__ import annotations

import asyncio
import logging
import re

from homeassistant.components import conversation
from homeassistant.const import CONF_TIMEOUT, MATCH_ALL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import intent
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .types import NodeRedConfigEntry
from .const import DOMAIN, DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)

# 预编译正则
IM_PREFIX_PATTERN = re.compile(r"^\[.*?\|.*?\]\s*")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NodeRedConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """初始化集成."""
    # 初始化运行时数据容器
    async_add_entities([NodeRedAsyncConversationEntity(entry)])

class NodeRedAsyncConversationEntity(conversation.ConversationEntity):
    """基于 Future 注册表和动态配置的 Node-RED 代理."""

    _attr_has_entity_name = True
    _attr_translation_key = "nodered_agent"
    _attr_should_poll = False

    def __init__(self, entry: NodeRedConfigEntry) -> None:
        """初始化."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}-async-agent"
        runtime = entry.runtime_data
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Node-RED Bridge",
            manufacturer="Node-RED Community",
            model="Reactive-v3",
            sw_version=runtime.version,
        )

    async def async_added_to_hass(self) -> None:
        """注册监听器，并把取消函数存入 runtime_data."""
        
        @callback
        def _handle_msg(event):
            """处理来自 Node-RED 的异步响应."""
            data = event.data
            # 兼容 conversation_id 和 request_id
            cid = data.get("conversation_id") or data.get("request_id")
            
            # 获取注册表
            pending = self._entry.runtime_data.pending_requests
            
            if cid in pending:
                future = pending[cid]
                if not future.done():
                    # 将整个 payload 传回给 async_process
                    future.set_result(data)

        if self._entry.runtime_data.unsub_listener:
            self._entry.runtime_data.unsub_listener()

        # 存入 runtime_data 供全局管理
        self._entry.runtime_data.unsub_listener = self.hass.bus.async_listen(
            "nodered_response_event", _handle_msg
        )

    async def async_will_remove_from_hass(self) -> None:
        """销毁前清理。"""
        if self._entry.runtime_data.unsub_listener:
            self._entry.runtime_data.unsub_listener()

    @property
    def supported_languages(self) -> list[str] | str:
        return MATCH_ALL

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """
        处理对话核心流程。
        支持：1. 动态超时  2. 对话保持  3. 异常安全
        """
        # 确保有 Conversation ID（如果是外部平台接入，必须保持该 ID）
        conv_id = user_input.conversation_id or f"direct_{asyncio.get_event_loop().time()}"
        
        # 文本清洗
        clean_text = IM_PREFIX_PATTERN.sub("", user_input.text)
        
        # 在注册表中创建 Future
        future = self.hass.loop.create_future()
        self._entry.runtime_data.pending_requests[conv_id] = future

        # 默认 30 秒，如果用户在“集成选项”里改了，实时生效
        timeout_val = self._entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

        try:
            # 使用统一的 conversation_id 字段
            self.hass.bus.async_fire("nodered_request_event", {
                "conversation_id": conv_id,
                "text": clean_text,
                "language": user_input.language,
                "device_id": user_input.device_id,
                "user_id": user_input.context.user_id if user_input.context else None,
                "platform": "external_relay" # 标记来源方便 Node-RED 针对性处理
            })

            # 6. 等待结果
            async with asyncio.timeout(timeout_val):
                payload = await future
                
            response_text = payload.get("response", "Node-RED 流程未提供有效回复")
            # 关键：对话保持标志
            should_continue = payload.get("continue_conversation", False)

        except TimeoutError:
            _LOGGER.error("Node-RED 在 %ss 内未响应会话 %s", timeout_val, conv_id)
            response_text = "对话引擎响应超时，请检查后端的 Node-RED 流程。"
            should_continue = False
        except Exception as err:
            _LOGGER.exception("会话处理发生严重错误: %s", err)
            response_text = f"助手内部错误: {err}"
            should_continue = False
        finally:
            # 无论如何，移除注册表，防止内存堆积
            self._entry.runtime_data.pending_requests.pop(conv_id, None)

        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(response_text)

        return conversation.ConversationResult(
            response=intent_response,
            conversation_id=conv_id,
            continue_conversation=should_continue
        )