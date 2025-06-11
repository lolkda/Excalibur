# -*- coding: utf-8 -*-
from os import path, system
from telethon import events, TelegramClient
from function.PrintLog import PrintMethod
from adapters.telegram import TelegramAdapter
from plugin import BasePlugin

class Restart(BasePlugin):

    plugin_method:str = "适配器重启\n\n"
    plugin_method += "使用方法：\n"
    plugin_method += "chat内发送 `reboot` 指令, 重启聊天适配器\n"

    def __init__(self):
        self.log = PrintMethod
        self.client = TelegramAdapter.obj
        self.user: TelegramClient = self.client.get_user_client
        self.bot: TelegramClient = self.client.get_bot_client
        self.user.add_event_handler(self.Handle_Restart_Command, events.NewMessage(pattern=r'^reboot$', outgoing=True))

    async def Handle_Restart_Command(self, event):
        try:
            await event.send_message(self.userid, "重启程序")
            system("pm2 restart NaiBot")
        except Exception as e:
            title = "【💥错误💥】"
            name = "文件名：" + path.split(__file__)[-1].split(".")[0]
            function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
            details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
            message = f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}"
            await self.bot.send_message(self.userid, message)
            self.log.warning(f"错误--->{message}")