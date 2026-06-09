"""集成常量定义"""
from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "nodered_conversation"
CONF_URL = "url"
DEFAULT_TIMEOUT = 30
PLATFORMS: list[Platform] = [Platform.CONVERSATION]