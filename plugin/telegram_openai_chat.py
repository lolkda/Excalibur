from os import path
from plugin import BasePlugin
from telethon import events, TelegramClient
from telethon.tl.custom.message import Message
from adapters.telegram import TelegramAdapter
from function.PrintLog import PrintMethodClass
from module.openai_chat_manager import  OpenAiChatParam, OpenAiChatModels, ChatManager
from module.telethon_conversation_manager import TelegramConversationManager

class OpenAiChatManager(BasePlugin):

    plugin_method: str = "Telegram OpenAI 聊天\n\n"
    plugin_method += "使用方法：\n"
    plugin_method += "1. chat内发送 `/openchat` 指令\n"
    plugin_method += "2. 选择已适配的openAi\n"
    plugin_method += "3. 选择key可使用的模型\n"
    plugin_method += "4. 进行对话聊天\n"

    def __init__(self):
        self.log = PrintMethodClass()
        self.chat = ChatManager()
        self.client: TelegramAdapter = TelegramAdapter.obj
        self.bot:TelegramClient  = self.client.get_bot_client
        self.user: TelegramClient = self.client.get_user_client
        self.user.add_event_handler(self.handle_openai_chat_command, events.NewMessage(pattern=r'^\/openchat[\s]?(.+)?$', outgoing=True))

    async def handle_openai_chat_command(self, event: Message):
        """
        处理 /OpenChat 命令
        """
        reply = await event.get_reply_message()
        if reply:
            text = reply.text
        else:
            text = event.raw_text
        # 获取当前聊天的ID
        chat_id = event.chat_id

        try:
            opemai_chat_param = OpenAiChatParam()
            adapters = OpenAiChatModels.get_chat_adapters()

            Manager = TelegramConversationManager(self.user, event, 180)

            # 1. 发送适配器选择提示
            msg: Message = await self.user.send_message(chat_id, f"请输入要使用的适配器名称:\n{adapters}\n\n")
            async with Manager as conv:
                response = await conv.get_response()
                self.log.info(response)
                opemai_chat_param.adapter_name = response

            await msg.delete()

            models = OpenAiChatModels.get_chat_models(response)
            msg: Message = await self.user.send_message(chat_id, f"请输入要使用的模型:\n{models}\n\n")
            async with Manager as conv:
                response = await conv.get_response()
                opemai_chat_param.model_name = response

            await msg.delete()

            await self.user.send_message(chat_id, "输入消息内容，输入 [`exit`, `退出`, `结束`] 退出聊天。")
            async with Manager as conv:
                while True:
                    response = await conv.get_response()
                    if response in ["exit", "退出", "结束"]:
                        sender = await event.get_sender()
                        await self.user.send_message(chat_id, f"用户 {sender.first_name or ''} {sender.last_name or ''} 已退出聊天。")
                        break
                    opemai_chat_param.add_message("user", response)
                    await self.chat.send_message(opemai_chat_param)
                    await self.user.send_message(chat_id, opemai_chat_param.get_assistant_messages())
        except Exception as e:
            await self.user.send_message(chat_id, f"{e}")
            title = "【💥错误💥】"
            name = "文件名：" + path.split(__file__)[-1].split(".")[0]
            function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
            details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
            # await self.user.send_message(chat_id, f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}")
            self.log.warning(f"错误--->{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}")