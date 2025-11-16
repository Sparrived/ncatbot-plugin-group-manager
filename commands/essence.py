from ncatbot.core import ForwardConstructor, GroupMessageEvent
from ncatbot.plugin_system import NcatBotPlugin
import time

async def cmd_essence_list(
        plugin_instance: NcatBotPlugin, 
        event: GroupMessageEvent, 
        all: bool = False, 
        page: int = 1
):
    """列出群内所有群精华消息，支持分页显示"""
    essence_messages = await plugin_instance.api.get_essence_msg_list(event.group_id)
    if len(essence_messages) == 0:
        await event.reply("本群暂无群精华消息喵，你们怎么不爆典喵？~")
        return
    self_info = await plugin_instance.api.get_stranger_info(user_id=event.self_id)
    forward_message = ForwardConstructor(
        user_id=event.self_id, 
        nickname=self_info["nickname"]
    )
    list_count = plugin_instance.config["essence_list_count"]
    show_essences = essence_messages if all else essence_messages[(page-1)*list_count:page*list_count]
    page_count = (len(essence_messages) + list_count - 1) // list_count
    forward_message.attach_text(f" 本群共有 {len(essence_messages)} 条群精华消息，{' 显示全部消息喵~' if all else f' 当前显示第 {page} / {page_count} 页喵~'}")
    for essence in show_essences:
        time_array = time.localtime(essence.operator_time)
        forward_message.attach_text(f"消息ID: {essence.message_id}\n时间: {time.strftime('%Y-%m-%d %H:%M:%S', time_array)}\n操作者: {essence.operator_nick}({essence.operator_id})\n↓↓↓↓↓ 消息内容 ↓↓↓↓↓\n")
        forward_message.attach(essence.content, essence.sender_id, essence.sender_nick)
    await plugin_instance.api.post_forward_msg(group_id=event.group_id, msg=forward_message.to_forward())