from ncatbot.plugin_system import (
    NcatBotPlugin, 
    on_group_increase, 
    on_group_decrease, 
    on_group_request, 
    command_registry, 
    option, 
    admin_group_filter, 
    param
)
from ncatbot.plugin_system.builtin_plugin.unified_registry.command_system.registry.help_system import HelpGenerator
from ncatbot.utils import get_log
from ncatbot.core import RequestEvent, NoticeEvent, GroupMessageEvent, MessageArray
from typing import Optional
from .utils import require_subscription, require_group_admin, at_check_support
from .commands import *


class GroupManager(NcatBotPlugin):

    name = "GroupManager"
    version = "1.1.0"
    author = "Sparrived"
    description = "一个用于管理群组的插件，支持群组成员管理、入群申请处理等功能。"

    log = get_log(name)

    def init_config(self):
        """注册配置项"""
        self.register_config(
            "auto_approve",
            {
                "enabled": True,
                "min_qq_level": 5,
                "custom_qq_level": {"123456789": 100}
            },
            "自动批准入群请求的配置项",
            dict
        )  # 是否自动批准入群请求
        self.register_config(
            "welcome_message",
            True,
            "是否发送欢迎消息",
            bool
        )
        self.register_config(
            "leave_message",
            True,
            "是否发送离开消息",
            bool
        )
        self.register_config(
            "subscribed_groups",
            ["123456789"],  # 示例群号
            "需要订阅的群组列表",
            list
        )


    # ======== 初始化插件 ========
    async def on_load(self):
        self._twice_requests = {}
        self.init_config()
        self.log.info("GroupManager插件已加载。")


    # ======== 事件处理器 ========
    @on_group_increase
    @require_subscription
    async def handle_group_increase(self, event: NoticeEvent):
        """处理群成员增加事件"""
        if not self.config["welcome_message"]:
            return
        user_info = await self.api.get_group_member_info(
            group_id=event.group_id, # type: ignore
            user_id=event.user_id # type: ignore
        )
        if event.user_id in self._twice_requests.keys():
            # 如果用户在二次请求列表中，移除该记录
            self._twice_requests.pop(event.user_id)
        # 构造消息
        message_array = MessageArray()
        message_array.add_at(user_info.user_id)
        message_array.add_text(f"有新人加入啦！欢迎你喵！")
        # 邀请额外添加消息
        if event.sub_type == "invite":
            operator_info = await self.api.get_group_member_info(
                group_id=event.group_id, # type: ignore
                user_id=event.operator_id # type: ignore
            )
            message_array.add_text(f"\n邀请者是：")
            message_array.add_at(operator_info.user_id)
        # 发送消息
        await self.api.post_group_msg(
            group_id=event.group_id, # type: ignore
            rtf=message_array
        )


    @on_group_decrease
    @require_subscription
    async def handle_group_decrease(self, event: NoticeEvent):
        """处理群成员减少事件"""
        if not self.config["leave_message"]:
            return
        user_info = await self.api.get_stranger_info(
            user_id=event.user_id # type: ignore
        )
        # 构建消息链
        message_array = MessageArray()
        if event.sub_type == "leave":
            message_array.add_text(f"{user_info['nickname']} 离开了群组喵...")
        else:
            operator_info = await self.api.get_group_member_info(
                group_id=event.group_id, # type: ignore
                user_id=event.operator_id # type: ignore
            )
            if operator_info.user_id == event.self_id:
                # 不处理由指令导致的踢出
                return
            message_array.add_text(f"{user_info['nickname']} 被 ")
            message_array.add_at(operator_info.user_id)
            message_array.add_text(f" 无情地踢出了群组喵?!发生什么事了喵？")
        await self.api.post_group_msg(
            group_id=event.group_id, # type: ignore
            rtf=message_array
        )


    @on_group_request
    @require_subscription
    async def handle_group_request(self, event: RequestEvent):
        """处理群请求事件"""
        if not self.config["auto_approve"]["enabled"]:
            return
        user_info = await self.api.get_stranger_info(
            user_id=event.user_id # type: ignore
        )
        if event.user_id in self._twice_requests.keys():
            # 如果用户在二次请求列表中，留存该请求等待其他管理员审核
            self._twice_requests[event.user_id] = event
            await self.api.post_group_msg(
                group_id=event.group_id, # type: ignore
                text=f"用户 {user_info['nickname']} 多次发送入群请求，请其他管理员注意查看喵~管理员可以直接使用 /gm approve {event.user_id} [-d] 来处理该请求喵( -d 是拒绝喵)。"
            )
            return
        if event.group_id in self.config["auto_approve"]["custom_qq_level"].keys():
            min_qq_level = self.config["auto_approve"]["custom_qq_level"][event.group_id]
        else:
            min_qq_level = self.config["auto_approve"]["min_qq_level"]
        if user_info['qqLevel'] <= min_qq_level:
            await event.approve(
                approve=False,
                reason="疑似小号，如果是真人请联系其它群管理员审核，或再次提交入群申请。"
            )
            self._twice_requests[event.user_id] = event
            self.log.info(f"拒绝了 {user_info['nickname']} 的入群请求，理由：QQ等级不足。")
        else:
            await event.approve(
                approve=True
            )
            self.log.info(f"通过了 {user_info['nickname']} 的入群请求。")



    # ======== 注册指令 ========
    gm_group = command_registry.group("gm", "群管理根级命令")
    
    @admin_group_filter
    @gm_group.command("approve", description="同意/拒绝申请入群")
    @option("d", "deny", "拒绝入群申请") # -d --deny
    @require_subscription
    @require_group_admin(role="admin", reply_message="我不是该群的管理员，不能处理入群申请喵……")
    async def cmd_approve(self, event: GroupMessageEvent, user_id: str, deny: bool = False):
        """同意/拒绝申请入群"""
        request_event: Optional[RequestEvent] = self._twice_requests.get(user_id, None)
        if not request_event:
            await event.reply("未找到该用户的入群申请喵，请确认用户ID是否正确喵~")
            return
        if deny:
            """ 处理拒绝指令 """
            await request_event.approve(
                approve=False,
                reason="管理员拒绝了你的加群申请。"
                )
            await event.reply(f"已拒绝 {user_id} 的入群申请喵。")
            return
        await request_event.approve(approve=True)
    

    @admin_group_filter
    @gm_group.command("mute", description="禁言群成员")
    @param("user_id", help="要禁言的用户ID", required=False)
    @param("duration", default=10, help="禁言时长（分钟）", required=False)
    @option("u", "undo", help="解除禁言")  # -u --undo
    @option("l", "list_user", help="列出目前被禁言的用户")  # -l --list
    @require_subscription
    @at_check_support
    @require_group_admin(role="admin", reply_message="我不是该群的管理员，不能禁言喵……")
    async def cmd_mute(
        self,
        event: GroupMessageEvent, 
        user_id: str = "", 
        duration: float = -1, 
        undo: bool = False, 
        list_user: bool = False
    ):
        """禁言群成员"""
        # list user
        if list_user and await mute.list_user(api=self.api, event=event):
            return
        if undo and await mute.unmute(api=self.api, event=event, user_id=user_id):
            return
        if duration < 1 or duration > 1440:  # 最多24小时
            await event.reply("❌ 禁言时长必须在1分钟到24小时之间喵~")
            return
        await mute.mute_member(api=self.api, event=event, user_id=user_id, duration=duration)



    @admin_group_filter
    @gm_group.command("mute_all", description="全体禁言")
    @param("duration", default=-1, help="禁言时长（分钟）", required=False)
    @require_subscription
    @require_group_admin(role="admin", reply_message="我不是该群的管理员，不能全体禁言喵……")
    async def cmd_mute_all(self, event: GroupMessageEvent, duration: float = -1):
        """全体禁言"""
        await mute.mute_all(self, event, duration)


    @admin_group_filter
    @gm_group.command("prefix", description="设置群成员头衔（仅Bot为群主）")
    @param("prefix", default="头衔", help="群成员头衔内容", required=False)
    @option("c", "clear", "清除群成员头衔")  # -c --clear
    @require_subscription
    @at_check_support
    @require_group_admin(role="owner", reply_message="我不是该群的群主，不能设置成员头衔喵……")
    async def cmd_prefix(self, event: GroupMessageEvent, user_id: str, prefix: str, clear: bool = False):
        """设置群成员头衔"""
        if clear:
            prefix = ""
        message_array = MessageArray()
        try:
            await self.api.set_group_special_title(
                group_id=event.group_id, # type: ignore
                user_id=user_id,
                special_title=prefix
            )
            message_array.add_text(f" 鉴于 ")
            message_array.add_at(user_id)
            if prefix:
                message_array.add_text(f" 最近的表现，为其授予 '{prefix}' 的头衔喵！")
            else:
                message_array.add_text(f" 最近的表现，已清除 ")
                message_array.add_at(user_id)
                message_array.add_text(f" 的头衔喵！")
        except Exception as e:
            message_array.add_text(f" 执行好像出了点问题，检查一下指令格式喵：\n /gm prefix <user_id> [头衔] [-c]\n错误信息：\n：{e}")
        await event.reply(rtf=message_array)


    @admin_group_filter
    @gm_group.command("kick", description="踢出群成员")
    @param("user_id", help="要踢出的用户ID", required=True)
    @option("b", "ban", "踢出并禁止再次加入")  # -b --ban
    @require_subscription
    @at_check_support
    @require_group_admin(role="admin", reply_message="我不是该群的管理员，不能踢人喵……")
    async def cmd_kick(self, event: GroupMessageEvent, user_id: str, ban: bool = False):
        """踢出群成员"""
        message_array = MessageArray()
        user_info = await self.api.get_group_member_info(
            group_id=event.group_id, # type: ignore
            user_id=user_id
        )
        self_info = await self.api.get_group_member_info(
            group_id=event.group_id, # type: ignore
            user_id=event.self_id
        )
        if user_info.role == "owner":
            await event.reply("我不能踢出群主喵……")
            return
        if user_info.role == self_info.role:
            await event.reply("我不能踢出和我同级的群员喵……")
            return
        try:
            await self.api.set_group_kick(
                group_id=event.group_id, # type: ignore
                user_id=user_id,
                reject_add_request=ban
            )
            message_array.add_text(f" 成功踢出 ")
            message_array.add_at(user_id)
            message_array.add_text(f" 这个家伙喵！")
            if ban:
                message_array.add_text(f" 以后不要再见了喵！")
        except Exception as e:
            message_array.add_text(f" 执行好像出了点问题，检查一下指令格式喵：\n /gm kick <user_id> [-b]\n错误信息：\n：{e}")
        await event.reply(rtf=message_array)


    @admin_group_filter
    @gm_group.command("custom_level", description="设置自定义自动批准QQ等级")
    @param("level", help="自定义QQ等级", required=False)
    @option("r", "reset", "重置为全局默认QQ等级")  # -r --reset
    @option("s", "show", "显示当前群组的自定义QQ等级")  # -s --show
    @require_subscription
    async def cmd_custom_level(self, event: GroupMessageEvent, level: int = 5, reset: bool = False, show: bool = False):
        """设置自定义自动批准QQ等级"""
        if reset:
            self.config["auto_approve"]["custom_qq_level"].pop(event.group_id, None)
            await event.reply("已将本群组的自定义自动批准QQ等级重置为全局默认值喵。")
        elif show:
            custom_level = self.config["auto_approve"]["custom_qq_level"].get(event.group_id, None)
            if custom_level is None:
                level = self.config["auto_approve"]["min_qq_level"]
                await event.reply(f"本群组未设置自定义自动批准QQ等级，当前使用全局默认值 {level} 喵。")
                return
            await event.reply(f"当前群组的自定义自动批准QQ等级为 {custom_level} 喵。")
        else:
            self.config["auto_approve"]["custom_qq_level"][event.group_id] = level
            await event.reply(f"已将本群组的自定义自动批准QQ等级设置为 {level} 喵。")

    

    @admin_group_filter
    @gm_group.command("admin", description="设置群管理员（仅限Bot为群主）")
    @param("user_id", help="用户ID", required=True)
    @require_subscription
    @at_check_support
    @require_group_admin(role="owner", reply_message="我不是群主，不能设置管理员喵……")
    async def cmd_admin(self, event: GroupMessageEvent, user_id: str):
        """设置群管理员（仅限Bot为群主）"""
        enable = True
        message_array = MessageArray()
        try:
            user_info = await self.api.get_group_member_info(
                group_id=event.group_id,
                user_id=user_id
            )
            if user_info.role == "admin":
                enable = False
            await self.api.set_group_admin(group_id=event.group_id, user_id=user_id, enable=enable)
            if enable:
                message_array.add_text(f" 恭喜 ")
                message_array.add_at(user_id)
                message_array.add_text(f" 大人高升喵！")
            else:
                message_array.add_text(f" 怎么回事喵？")
                message_array.add_at(user_id)
                message_array.add_text(f" 被革职了喵！")
            await event.reply(rtf=message_array)
        except Exception as e:
            await event.reply(f"设置管理员时出错了，检查一下指令格式喵：\n /gm admin <user_id>\n错误信息：\n{e}")


    # ======== 订阅功能 ========
    @admin_group_filter
    @gm_group.command("subscribe", description="订阅群组管理功能")
    async def cmd_subscribe(self, event: GroupMessageEvent):
        """订阅群组管理功能"""
        subscribed_groups = self.config["subscribed_groups"]
        if str(event.group_id) in subscribed_groups:
            await event.reply("本群组已订阅群组管理功能喵~")
            return
        self.config["subscribed_groups"].append(str(event.group_id))
        await event.reply("订阅了群组管理功能喵~")


    @admin_group_filter
    @gm_group.command("unsubscribe", description="取消订阅群组管理功能")
    async def cmd_unsubscribe(self, event: GroupMessageEvent):
        """取消订阅群组管理功能"""
        subscribed_groups = self.config["subscribed_groups"]
        if str(event.group_id) not in subscribed_groups:
            await event.reply("本群组未订阅群组管理功能喵~")
            return
        self.config["subscribed_groups"].remove(str(event.group_id))
        await event.reply("取消订阅了群组管理功能喵~")


    @admin_group_filter
    @gm_group.command("help", description="获取群管理帮助信息")
    @param("command", default="", help="指令名称", required=False)
    @require_subscription
    async def cmd_help(self, event: GroupMessageEvent, command: str = ""):
        """获取群管理帮助信息"""
        help_generator = HelpGenerator()
        try:
            if not command:
                help_message = help_generator.generate_group_help(self.gm_group)
            else:
                command_obj = self.gm_group.commands.get(command, None) # type: ignore
                if not command_obj:
                    await event.reply("未找到该指令喵，请确认指令名称是否正确喵~")
                    return
                help_message = help_generator.generate_command_help(command_obj)
            await event.reply(help_message)
        except Exception as e:
            await event.reply(f"生成帮助信息时出错喵：\n{e}")