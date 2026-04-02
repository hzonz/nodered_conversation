"""Node-Red 异步对话代理平台实现."""
from __future__ import annotations

import logging
import asyncio
import uuid
import async_timeout

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import intent
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# 配置超时时间（建议给 AI 预留足够时间，比如 30 秒）
REQUEST_TIMEOUT = 30

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """初始化 Node-Red 对话实体."""
    agent = NodeRedAsyncConversationEntity(config_entry)
    async_add_entities([agent])


class NodeRedAsyncConversationEntity(conversation.ConversationEntity):
    """基于事件驱动的异步对话代理."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}-async-agent"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Node-Red Async Agent",
            manufacturer="Node-Red Custom",
            model="Event-Based Bridge",
        )

    @property
    def supported_languages(self) -> list[str]:
        return ["zh-Hans", "zh-Hant", "en"]

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """对话处理主逻辑."""
        
        # 1. 生成本次对话的唯一标识符
        request_id = str(uuid.uuid4())
        
        # 2. 创建一个 Future 对象，用于异步等待结果
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        # 3. 定义如何处理回传事件的回调函数
        @callback
        def handle_response_event(event):
            """当监听到 Node-RED 的回复事件时触发."""
            if event.data.get("request_id") == request_id:
                response_text = event.data.get("response", "")
                if not future.done():
                    future.set_result(response_text)

        # 4. 注册监听器：监听 'nodered_response_event'
        # 一旦 Node-RED 处理完，它需要向这个事件发送数据
        unsub = self.hass.bus.async_listen(
            "nodered_response_event", 
            handle_response_event
        )

        try:
            # 5. 触发请求事件：告诉 Node-RED 该干活了
            # Node-RED 只需要监听 'nodered_request_event'
            self.hass.bus.async_fire("nodered_request_event", {
                "request_id": request_id,
                "text": user_input.text,
                "conversation_id": user_input.conversation_id,
                "device_id": user_input.device_id,
                "language": user_input.language
            })

            # 6. 挂起等待！直到 Future 被 set_result 或超时
            async with async_timeout.timeout(REQUEST_TIMEOUT):
                final_response = await future

        except asyncio.TimeoutError:
            final_response = "Node-RED 响应超时，请检查后端流程。"
        except Exception as e:
            _LOGGER.error("异步对话发生错误: %s", e)
            final_response = f"发生错误: {str(e)}"
        finally:
            # 7. 无论结果如何，必须注销监听器，释放内存
            unsub()

        # 8. 构造并返回结果
        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(final_response)

        return conversation.ConversationResult(
            response=intent_response,
            conversation_id=user_input.conversation_id
        )