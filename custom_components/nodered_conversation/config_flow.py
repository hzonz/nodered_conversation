"""Node-Red 对话代理的配置流实现."""
from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol
import aiohttp

from homeassistant import config_entries
from homeassistant.const import CONF_URL
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# 定义 UI 架构
STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_URL, default="http://127.0.0.1:1880/ha-conversation"): TextSelector(
        TextSelectorConfig(type=TextSelectorType.URL)
    ),
})

class NodeRedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """处理 Node-Red 对话代理的 UI 配置."""

    VERSION = 1

    async def _test_connection(self, url: str) -> bool:
        """测试 Node-RED 终结点是否可以访问."""
        session = async_get_clientsession(self.hass)
        try:
            # 尝试发送一个 HEAD 或 GET 请求以验证 URL
            async with session.get(url, timeout=5) as response:
                # 只要返回了状态码（哪怕是 405），说明服务是存活的
                return response.status < 500
        except (aiohttp.ClientError, TimeoutError):
            return False

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """用户点击“添加集成”时调用的初始步骤."""
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input[CONF_URL]
            
            # 1. 唯一性检查
            await self.async_set_unique_id(url)
            self._abort_if_unique_id_configured()

            # 2. 验证连接
            success = await self._test_connection(url)
            if not success:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"Node-RED Agent ({url})", 
                    data=user_input
                )

        return self.async_show_form(
            step_id="user", 
            data_schema=STEP_USER_DATA_SCHEMA, 
            errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """处理重新配置流程（修改 URL）."""
        errors: dict[str, str] = {}
        # 获取当前的配置条目
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if user_input is not None:
            url = user_input[CONF_URL]
            if await self._test_connection(url):
                return self.async_update_reload_and_abort(
                    entry, data={**entry.data, **user_input}
                )
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, entry.data if entry else None
            ),
            errors=errors,
        )
