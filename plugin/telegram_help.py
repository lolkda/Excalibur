from telethon import TelegramClient, events
from telethon.tl.custom.message import Message
from plugin import BasePlugin
from json import loads
from os import path
from function.PrintLog import PrintMethodClass
from function.AsyncMethod import ReqMethod
from adapters.telegram import TelegramAdapter

class PluginHelp(BasePlugin):

    plugin_method: str = 'Telegram帮助\n\n'
    plugin_method += "使用方法：\n"
    plugin_method += "1. chat内发送 `/help` 指令, 查询当前插件列表\n"
    plugin_method += "1. chat内发送 `/help 插件名` 指令, 查询插件使用说明\n"

    def __init__(self):
        self.client = TelegramAdapter.obj
        self.req = ReqMethod()
        self.log = PrintMethodClass()
        self.user: TelegramClient = self.client.get_user_client
        self.user.add_event_handler(self.handle_help_command, events.NewMessage(pattern=r'^help$', outgoing=True))
        self.user.add_event_handler(self.handle_help_plugin_command, events.NewMessage(pattern=r'^help .*$', outgoing=True))

    async def handle_help_command(self, event: Message):
        try:
            opt = {
                "method": "GET",
                "url": "http://localhost:80/plugins"
            }
            response = await self.req.async_requests(opt, "plugin_help")
            response: dict = loads(response.text)
            plugin_list = "\n".join([f"`{x}`" for x in response.keys()])
            await self.user.send_message(event.chat_id, f"插件列表: \n\n{plugin_list}\n发送 `help 插件名` 以查看特定插件说明帮助")
        except Exception as e:
            title = "【💥错误💥】"
            name = "文件名：" + path.split(__file__)[-1].split(".")[0]
            function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
            details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
            message = f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}"
            await self.user.send_message(self.userid, message)
            self.log.warning(f"错误--->{message}")

    async def handle_help_plugin_command(self, event: Message):
        message = event.raw_text.split(" ")
        if len(message) > 1:
            plugin_name = message[1]
            opt = {
                "method": "GET",
                "url": "http://localhost:80/plugins"
            }
            response = await self.req.async_requests(opt, "plugin_help")
            response = loads(response.text)
            if plugin_name in response.keys():
                await self.user.send_message(event.chat_id, f"插件使用说明: \n\n{response[plugin_name]}")