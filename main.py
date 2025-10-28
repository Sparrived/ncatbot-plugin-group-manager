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
from .utils import require_subscription



class GroupManager(NcatBotPlugin):

    name = "GroupManager"
    version = "1.0.2-post3"
    description = "一个用于管理群组的插件，支持群组成员管理、入群申请处理等功能。"

    log = get_log(name)

    def init_config(self):
        """注册配置项"""
        self.register_config(
            "auto_approve",
            {
                "enabled": True,
                "min_qq_level": 5,
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
        # 构造消息
        message_array = MessageArray()
        message_array.add_text(f"有新人加入啦！欢迎你喵")
        message_array.add_at(user_info.user_id)
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
                text=f"用户 {user_info['nickname']} 多次发送入群请求，请其他管理员注意查看喵~管理员可以直接使用 /gm approve {event.user_id} <-d> 来处理该请求喵( -d 是拒绝喵)。"
            )
            return
        if user_info['qqLevel'] <= self.config["auto_approve"]["min_qq_level"]:
            await event.approve(
                approve=False,
                reason="疑似小号，如果是真人请联系管理员审核，或再次提交入群申请。"
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
            await event.reply(f"已拒绝 {user_id} 的入群申请。")
            return
        await request_event.approve(approve=True)
    

    @admin_group_filter
    @gm_group.command("mute", description="禁言群成员")
    @param("duration", default=10, help="禁言时长（分钟）")
    @require_subscription
    async def cmd_mute(self, event: GroupMessageEvent, user_id: str, duration: int):
        """禁言群成员"""
        if user_id.startswith("At"):
            user_id = user_id.split("=")[1].split('"')[1]
        
        if duration < 1 or duration > 1440:  # 最多24小时
            await event.reply("❌ 禁言时长必须在1分钟到24小时之间喵~")
            return
        await self.api.set_group_ban(
            group_id=event.group_id, # type: ignore
            user_id=user_id,
            duration=duration * 60
        )
        message_array = MessageArray()
        message_array.add_text(f" 已禁言 ")
        message_array.add_at(user_id)
        message_array.add_text(f" {duration} 分钟，注意你的言行喵！")
        await event.reply(rtf=message_array)

    
    @admin_group_filter
    @gm_group.command("prefix", description="设置群成员头衔")
    @require_subscription
    async def cmd_prefix(self, event: GroupMessageEvent, user_id: str, prefix: str):
        """设置群成员头衔"""
        if user_id.startswith("At"):
            user_id = user_id.split("=")[1].split('"')[1]
        
        await self.api.set_group_special_title(
            group_id=event.group_id, # type: ignore
            user_id=user_id,
            special_title=prefix
        )
        message_array = MessageArray()
        message_array.add_text(f" 鉴于 ")
        message_array.add_at(user_id)
        message_array.add_text(f" 最近的表现，为其授予 '{prefix}' 的头衔喵！")
        await event.reply(rtf=message_array)


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
    @require_subscription
    async def cmd_help(self, event: GroupMessageEvent):
        """获取群管理帮助信息"""
        help_generator = HelpGenerator()
        help_message = help_generator.generate_group_help(self.gm_group)
        await event.reply(help_message)