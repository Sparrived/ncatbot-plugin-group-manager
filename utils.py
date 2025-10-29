from functools import wraps
from ncatbot.plugin_system import NcatBotPlugin
from typing import Callable, Literal



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


def require_group_admin(role: Literal["admin", "owner"] = "admin", reply_message: str = "我不是该群的管理员，不能做这些喵……"):
    """群组管理员判断装饰器函数"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self: NcatBotPlugin, event, *args, **kwargs):
            group_id = getattr(event, "group_id", None)
            self_id = getattr(event, "self_id", None)
            if group_id is None or self_id is None:
                return await func(self, event, *args, **kwargs)
            self_info = await self.api.get_group_member_info(
                group_id=group_id, 
                user_id=self_id
            )
            if self_info.role == "owner":
                return await func(self, event, *args, **kwargs)
            if self_info.role != role:
                await event.reply(reply_message)
                return
            return await func(self, event, *args, **kwargs)

        return wrapper
    return decorator

def at_check_support(func: Callable):
    """支持 at 功能的装饰器函数"""
    @wraps(func)
    async def wrapper(self: NcatBotPlugin, event, *args, **kwargs):
        user_id = kwargs.get("user_id", None)
        if not user_id or not isinstance(user_id, str):
            return await func(self, event, *args, **kwargs)
        if user_id.startswith("At"):
            user_id = user_id.split("=")[1].split('"')[1]
            kwargs["user_id"] = user_id
        return await func(self, event, *args, **kwargs)
    return wrapper