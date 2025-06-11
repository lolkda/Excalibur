from telethon import events, TelegramClient
from telethon.tl.custom.message import Message
from adapters.telegram import TelegramClientProvider
from adapters.telegram import TelegramAdapter
from plugin import BasePlugin

class ChatId(BasePlugin):

    plugin_method: str = "Telegram聊天ID查询\n\n"
    plugin_method += "使用方法：\n"
    plugin_method += "1. chat对指定消息发送 `/id` 指令, 查询当前chat信息\n"

    def __init__(self):
        self.client = TelegramAdapter.obj
        self.user: TelegramClient = self.client.get_user_client
        self.user.add_event_handler(self.Handle_CheckId_Command, events.NewMessage(pattern=r'^id$', outgoing=True))

    async def Handle_CheckId_Command(self, event: Message):
        message = await event.get_reply_message()
        text = f"此消息ID：`{str(event.message.id)}`\n\n"
        text += f"**群组信息**\nid:`{str(event.chat_id)}\n`"
        msg_from = event.chat if event.chat else (await event.get_chat())
        if event.is_group or event.is_channel:
            text += f"群组名称：`{msg_from.title}`\n"
            try:
                if msg_from.username:
                    text += f"群组用户名：`@{msg_from.username}`\n"
            except AttributeError:
                return
        if message:
            text += f"\n**查询的消息**：\n消息id：`{str(message.id)}`\n用户id：`{str(message.sender_id)}`"
            try:
                if message.sender.bot:
                    text += f"\n机器人：`是`"
                if message.sender.last_name:
                    text += f"\n姓：`{message.sender.last_name}`"
                try:
                    text += f"\n名：`{message.sender.first_name}`"
                except TypeError:
                    pass
                if message.sender.username:
                    text += f"\n用户名：@{message.sender.username}"
            except AttributeError:
                pass
            await event.edit(text)
        else:
            await event.delete()