# -*- coding: utf-8 -*-
from asyncio import sleep
from os import path
from plugin import BasePlugin
from telethon import events, TelegramClient
from adapters.telegram import TelegramAdapter
from function.PrintLog import PrintMethodClass

class DelMsg(BasePlugin):

    plugin_method:str = "Telegram聊天记录删除\n\n"
    plugin_method += "使用方法：\n"
    plugin_method += "chat内发送 `del 数量` 指令, 删除指定数量聊天记录\n"

    def __init__(self):
        self.log = PrintMethodClass()
        self.client = TelegramAdapter.obj
        self.user: TelegramClient = self.client.get_user_client
        self.user.add_event_handler(self.Handle_DelMsg_Command, events.NewMessage(pattern=r'^del [0-9]+$', outgoing=True))

    async def Handle_DelMsg_Command(self, event):
        try:
            num = event.raw_text.split(' ')
            if isinstance(num, list) and len(num) == 2:
                count = int(num[1])
            else:
                await self.user.send_message(event.chat_id, f'请输出正确格式 `del 数字`')
                return
            await event.delete()
            count_buffer = 0
            async for message in self.user.iter_messages(event.chat_id, from_user="me"):
                if count_buffer == count:
                    break
                print(message)
                await message.delete()
                count_buffer += 1
            notification = await self.user.send_message(event.chat_id, f'已删除{count_buffer}/{count}')
            await sleep(1)
            await notification.delete()
        except Exception as e:
            title = "【💥错误💥】"
            name = "文件名：" + path.split(__file__)[-1].split(".")[0]
            function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
            details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
            message = f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}"
            await self.user.send_message(self.userid, message)
            self.log.warning(f"错误--->{message}")