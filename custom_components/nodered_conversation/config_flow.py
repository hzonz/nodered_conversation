"""Node-Red 对话代理的配置流实现."""
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

# 从常量文件中导入。由于去掉了 Key，这里不再引用 CONF_API_KEY
from .const import DOMAIN, CONF_URL

class NodeRedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """处理 Node-Red 对话代理的 UI 配置."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """用户点击“添加集成”或提交表单时调用的函数."""
        errors = {}

        if user_input is not None:
            # 1. 唯一性检查：防止用户多次添加同一个 Node-Red URL
            await self.async_set_unique_id(user_input[CONF_URL])
            self._abort_if_unique_id_configured()

            # 2. 直接保存配置
            return self.async_create_entry(
                title="Node-Red Agent", 
                data=user_input
            )

        # 3. 定义 UI 显示的输入表单
        data_schema = vol.Schema({
            vol.Required(
                CONF_URL, 
                default="http://127.0.0.1:1880/ha-conversation"
            ): str,
        })

        # 返回表单界面
        return self.async_show_form(
            step_id="user", 
            data_schema=data_schema, 
            errors=errors
        )
