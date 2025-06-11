# -*- coding: utf-8 -*-
from os import path
from telethon import events, TelegramClient
from adapters.telegram import TelegramAdapter
from telethon.errors import MessageNotModifiedError
from plugin import BasePlugin
from function.PrintLog import PrintMethodClass

class ReplyMsg(BasePlugin):

    plugin_method:str = "Telegram消息转发\n\n"
    plugin_method += "使用方法：\n"
    plugin_method += "chat内发送 `re 数量` 指令, 转发指定数量消息\n"

    def __init__(self):
        self.log = PrintMethodClass()
        self.client = TelegramAdapter.obj
        self.user: TelegramClient = self.client.get_user_client
        self.bot: TelegramClient = self.client.get_bot_client
        self.user.add_event_handler(self.Handle_ReplyMsg_Command, events.NewMessage(pattern=r'^re [0-9]+|re$', outgoing=True))
    
    async def Handle_ReplyMsg_Command(self, event):
        try:
            # 检查消息是否有回复目标
            reply = await event.get_reply_message()
            if not reply:
                await event.reply("❌ 请回复需要被转发的消息")
                return

            # 解析转发次数
            parts = event.raw_text.split()
            repeat_count = 1 if len(parts) == 1 else int(parts[1])

            # 删除原命令消息
            await event.delete()

            # 执行消息转发
            for _ in range(repeat_count):
                await reply.forward_to(event.chat_id)

        except ValueError:
            await event.reply("⚠️ 参数错误，请使用格式：`re <次数>`")
        except MessageNotModifiedError:
            pass  # 忽略消息未修改的异常
        except Exception as e:
            title = "【💥错误💥】"
            name = "文件名：" + path.split(__file__)[-1].split(".")[0]
            function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
            details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
            message = f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}"
            await self.bot.send_message(self.userid, message)
            self.log.warning(f"错误--->{message}")