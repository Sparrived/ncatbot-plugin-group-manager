from functools import wraps
from ncatbot.plugin_system import NcatBotPlugin
from typing import Callable



def subscribed_check(subscribed_groups: list, group_id: str) -> bool:
    """配置项基础检测"""
    if group_id not in subscribed_groups:
        return False
    return True

def require_subscription(func: Callable):
    """群组订阅判断装饰器函数"""
    @wraps(func)
    async def wrapper(self: NcatBotPlugin, event, *args, **kwargs):
        group_id = getattr(event, "group_id", None)
        if group_id is None:
            return await func(self, event, *args, **kwargs)
        if not subscribed_check(self.config["subscribed_groups"], str(group_id)):
            return None
        return await func(self, event, *args, **kwargs)

    return wrapper