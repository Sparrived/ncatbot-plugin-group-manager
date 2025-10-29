from ncatbot.core import GroupMessageEvent, MessageArray
from ncatbot.core.api import BotAPI
from ncatbot.plugin_system import NcatBotPlugin
from .command_status import CommandStatus

MUTEALL_MAP = {}

async def list_user(api: BotAPI, event: GroupMessageEvent) -> CommandStatus:
    """列出当前被禁言的用户
    
    Args:
        api (BotAPI): 机器人API对象
        event (GroupMessageEvent): 群消息事件对象
    
    Returns:
        CommandStatus: 命令执行状态
    """
    muted_users = await api.get_group_shut_list(group_id=event.group_id)  # 获取禁言用户列表
    if muted_users.member_count == 0:
        await event.reply("当前没有被禁言的用户喵~")
        return CommandStatus.SUCCESS_AND_EXIT
    message_array = MessageArray()
    message_array.add_text(f" ❌ 当前被禁言的用户共有 {muted_users.member_count} 个：\n")
    for index, user in enumerate(muted_users.members):
        message_array.add_text(f"{index + 1}. ")
        message_array.add_at(user.user_id)
        message_array.add_text(f" - {user.user_id} - （{user.shut_up_timestamp // 60} 分钟）\n")
    await event.reply(rtf=message_array)
    return CommandStatus.SUCCESS_AND_EXIT


async def mute_all(plugin_instance: NcatBotPlugin, event: GroupMessageEvent, duration: float) -> CommandStatus:
    """全体禁言，可设定定时禁言时间
    
    Args:
        plugin_instance (NcatBotPlugin): 插件实例
        event (GroupMessageEvent): 群消息事件对象
        duration (float): 禁言时长（分钟）
    
    Returns:
        CommandStatus: 命令执行状态
    """
    group_info = await plugin_instance.api.get_group_info(group_id=event.group_id)
    if group_info.group_all_shut == 0:
        enabled = False
    try:
        enabled = MUTEALL_MAP.get(event.group_id, False)
        await plugin_instance.api.set_group_whole_ban(
            group_id=event.group_id,
            enable=not enabled,
        )
        if enabled:
            await event.reply(f"关闭了全体禁言喵~")
            MUTEALL_MAP[event.group_id] = False
        else:
            message_array = MessageArray()
            message_array.add_text(f" 已开启全体禁言喵！")
            MUTEALL_MAP[event.group_id] = True
            if duration > 0:
                plugin_instance.add_scheduled_task(
                    name=f"close_mute_all_{event.group_id}",
                    interval=f"{duration * 60}s",
                    job_func=_close_mute_all,
                    args=(plugin_instance.api, event),
                    max_runs=1
                )
                message_array.add_text(f"全体禁言将在 {duration} 分钟后解除~")
            await event.reply(rtf=message_array)
        return CommandStatus.SUCCESS_AND_EXIT
    except Exception as e:
        await event.reply(f"禁言全体成员失败了喵……错误信息：{str(e)}")
        return CommandStatus.FAILURE


async def _close_mute_all(api: BotAPI, event: GroupMessageEvent):
    """关闭全体禁言"""
    group_info = await api.get_group_info(group_id=event.group_id)
    enabled = MUTEALL_MAP.get(event.group_id, True)
    if group_info.group_all_shut == 0:
        enabled = False
    if enabled:
        await api.set_group_whole_ban(
                group_id=event.group_id,
                enable=False,
        )
        await event.reply(f"时间到了，大家可以说话了喵~")
        MUTEALL_MAP[event.group_id] = False


async def mute_member(api: BotAPI, event: GroupMessageEvent, user_id: str, duration: float) -> CommandStatus:
    message_array = MessageArray()
    self_info = await api.get_group_member_info(
        group_id=event.group_id, # type: ignore
        user_id=event.self_id
    )
    try:
        user_info = await api.get_group_member_info(
            group_id=event.group_id, # type: ignore
        )
    except Exception as e:
        message_array.add_text(f" 执行好像出了点问题，检查一下指令格式喵：\n /gm mute <user_id> [duration] [-u]\n错误信息：\n：{e}")
        await event.reply(rtf=message_array)
        return CommandStatus.FAILURE
    if self_info.role == "admin" and user_info.role == "admin":
        message_array.add_text(f" 我和 ")
        message_array.add_at(user_id)
        message_array.add_text(f" 同级，不能互相禁言喵~")
        await event.reply(rtf=message_array)
        return CommandStatus.FAILURE
    try:
        await api.set_group_ban(
            group_id=event.group_id, # type: ignore
            user_id=user_id,
            duration=int(duration * 60)
        )
        message_array.add_text(f" 已禁言 ")
        message_array.add_at(user_id)
        message_array.add_text(f" {duration} 分钟，注意你的言行喵！")
    except Exception:
        message_array.add_text(f" 禁言用户 ")
        message_array.add_at(user_id)
        message_array.add_text(f" 失败了，他的官似乎比我大喵……")
        await event.reply(rtf=message_array)
        return CommandStatus.FAILURE
    return CommandStatus.SUCCESS_AND_EXIT


async def unmute(api: BotAPI, event: GroupMessageEvent, user_id: str) -> CommandStatus:
    message_array = MessageArray()
    await api.set_group_ban(
        group_id=event.group_id, # type: ignore
        user_id=user_id,
        duration=0
    )
    message_array.add_text(f" 已解除 ")
    message_array.add_at(user_id)
    message_array.add_text(f" 的禁言喵。")
    await event.reply(rtf=message_array)
    return CommandStatus.SUCCESS_AND_EXIT