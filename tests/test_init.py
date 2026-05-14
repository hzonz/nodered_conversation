"""基础占位测试."""
from custom_components.nodered_conversation.const import DOMAIN

def test_setup():
    """测试域名是否正确."""
    assert DOMAIN == "nodered_conversation"
