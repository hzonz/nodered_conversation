"""Node-Red 异步对话代理平台实现."""
from __future__ import annotations

import logging
import asyncio
import async_timeout
import re  # 导入正则库

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import intent
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# 配置超时时间
REQUEST_TIMEOUT = 30
# 预编译正则：匹配开头的 [任何内容|任何内容] 以及紧随其后的空格
IM_PREFIX_PATTERN = re.compile(r"^\[.*?\|.*?\]\s*")

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """初始化 Node-Red 对话实体并注册代理."""
    agent = NodeRedAsyncConversationEntity(config_entry)
    async_add_entities([agent])
    
    # 注册代理
    conversation.async_set_agent(hass, config_entry, agent)


class NodeRedAsyncConversationEntity(conversation.ConversationEntity):
    """基于事件驱动的异步对话代理."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}-async-agent"
        self.entity_id = "conversation.nodered"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Node-Red Async Agent",
            manufacturer="Node-Red Custom",
            model="Event-Based Bridge",
        )

    @property
    def supported_languages(self) -> list[str]:
        return ["zh-Hans", "zh-Hant", "en"]

    @property
    def agent_id(self) -> str:
        """返回 Agent ID，用于 cn_im_hub 配置."""
        return self.entity_id

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """对话处理主逻辑."""
        
        # 1. 提取 ID（直接使用微信 ID）
        request_id = user_input.conversation_id
        
        # 2. 【核心优化】：清洗文本，去掉微信插件注入的前缀
        raw_text = user_input.text
        clean_text = IM_PREFIX_PATTERN.sub("", raw_text)
        
        # 3. 创建 Future
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        @callback
        def handle_response_event(event):
            """监听回复事件."""
            if event.data.get("request_id") == request_id:
                response_text = event.data.get("response", "")
                if not future.done():
                    future.set_result(response_text)

        # 4. 注册监听器
        unsub = self.hass.bus.async_listen(
            "nodered_response_event", 
            handle_response_event
        )

        try:
            # 5. 触发请求事件 (字段名称完全保持不变)
            self.hass.bus.async_fire("nodered_request_event", {
                "request_id": request_id,      # 原始透传的微信 ID
                "text": clean_text,            # 这里发送清洗后的干净文本
                "conversation_id": user_input.conversation_id,
                "language": user_input.language
            })

            # 6. 等待回传
            async with async_timeout.timeout(REQUEST_TIMEOUT):
                final_response = await future

        except asyncio.TimeoutError:
            final_response = "Node-RED 响应超时。"
        except Exception as e:
            _LOGGER.error("异步对话发生错误: %s", e)
            final_response = f"发生错误: {str(e)}"
        finally:
            # 7. 销毁监听器
            unsub()

        # 8. 返回结果
        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(final_response)

        return conversation.ConversationResult(
            response=intent_response,
            conversation_id=user_input.conversation_id
        )
