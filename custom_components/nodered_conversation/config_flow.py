"""Node-Red 对话代理的配置流实现."""
from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol
import aiohttp
import asyncio

from homeassistant import config_entries
from homeassistant.const import CONF_URL, CONF_TIMEOUT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import selector

from .const import DOMAIN, DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)

# 定义通用的数据架构
def get_config_schema(default_url: str = "http://127.0.0.1:1880/ha-conversation") -> vol.Schema:
    """生成配置架构."""
    return vol.Schema({

        vol.Required(CONF_URL, default=default_url): selector.TextSelector(
            selector.TextSelectorConfig(
                type=selector.TextSelectorType.URL  # 这里指定它是一个 URL 输入框
            )
        ),
    })

class NodeRedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """处理 Node-Red 对话代理的 UI 配置流."""

    VERSION = 1

    async def _test_connection(self, url: str) -> str | None:
        """验证连接性，返回错误键或 None。"""
        session = async_get_clientsession(self.hass)
        try:
            async with asyncio.timeout(5):
                async with session.get(url) as response:
                    if response.status < 500:
                        return None
                    return "server_error"
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            return "unknown"

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """初始添加集成步骤."""
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input[CONF_URL]
            
            # 设置唯一 ID 防止重复安装
            await self.async_set_unique_id(url)
            self._abort_if_unique_id_configured()

            # 测试连接
            error_code = await self._test_connection(url)
            if not error_code:
                return self.async_create_entry(
                    title=f"Node-RED Assist", 
                    data=user_input,
                    options={CONF_TIMEOUT: DEFAULT_TIMEOUT} # 初始化默认选项
                )
            errors["base"] = error_code

        return self.async_show_form(
            step_id="user", 
            data_schema=get_config_schema(), 
            errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """处理重新配置流程 (Reconfigure)。"""
        errors: dict[str, str] = {}
        
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            url = user_input[CONF_URL]
            
            # 验证新 URL 是否可用
            error_code = await self._test_connection(url)
            if not error_code:
                # 更新数据并自动重启集成，最后显示成功并关闭窗口
                return self.async_update_reload_and_abort(
                    entry, 
                    data={**entry.data, **user_input},
                    reason="reconfigure_successful"
                )
            errors["base"] = error_code

        # 使用 add_suggested_values_to_schema 自动填充当前已有的 URL
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                get_config_schema(), entry.data
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> NodeRedOptionsFlow:
        """定义选项流入口。"""
        return NodeRedOptionsFlow(config_entry)


class NodeRedOptionsFlow(config_entries.OptionsFlow):
    """处理已安装集成的动态选项修改。"""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        pass

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """选项流初始步骤。"""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # 选项架构：允许修改超时时间
        options_schema = vol.Schema({
            vol.Optional(
                CONF_TIMEOUT, 
                default=self.config_entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=5, max=180, step=1, unit_of_measurement="s",
                    mode=selector.NumberSelectorMode.BOX
                )
            ),
        })

        return self.async_show_form(step_id="init", data_schema=options_schema)