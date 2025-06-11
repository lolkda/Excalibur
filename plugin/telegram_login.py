from os import path
from function import pjt_path
from function.PrintLog import PrintMethodClass
from function.AsyncMethod import EnvMethod
from asyncio.exceptions import TimeoutError
from telethon import TelegramClient, events, Button
from adapters.telegram import TelegramAdapter
from adapters import AdapterProvider
from plugin import BasePlugin

class Telegramlogin(BasePlugin):

    plugin_method:str = "Telegram登录\n\n"
    plugin_method += "使用方法：\n"
    plugin_method += "bot内发送 `/login` 按照操作进行登录\n\n"

    def __init__(self):
        self.log = PrintMethodClass
        self.client = TelegramAdapter.obj
        self.bot: TelegramClient = self.client.get_bot_client
        self.user: TelegramClient = self.client.get_user_client
        self.userid: int = self.client.get_user_id
        self.bot.add_event_handler(self.user_login, events.NewMessage(from_users=self.userid, pattern=r'^/login$'))

    def press_event(self, userid):
        return events.CallbackQuery(func=lambda e: e.sender_id == userid)

    def split_list(self, data, number: int = 2):
        return [data[x:x+number] for x in range(0, len(data), number)]

    async def user_login(self, event):
        try:
            login = False
            sender = event.sender_id
            session = path.join(pjt_path, "bot", "sessions", "user.session")
            async with self.bot.conversation(sender, timeout=120) as conv:
                msg = await conv.send_message("请做出你的选择")
                buttons = [
                    Button.inline("重新登录", data="relogin") if path.exists(session) else Button.inline("我要登录", data="login"),
                   #  Button.inline("关闭user", data="close") if EnvMethod.readEnv("Telethon_StartUser", False) else Button.inline("开启user", data="start"),
                    Button.inline('取消会话', data='cancel')
                ]
                msg = await self.bot.edit_message(msg, '请做出你的选择：', buttons=self.split_list(buttons, 3))
                convdata = await conv.wait_event(self.press_event(sender))
                res = bytes.decode(convdata.data)
                if res == 'cancel':
                    await self.bot.edit_message(msg, '对话已取消')
                elif res == 'close':
                    await self.bot.edit_message(msg, "关闭成功, 准备重启机器人！")
                elif res == 'start':
                    await self.bot.edit_message(msg, "开启成功, 请确保session可用，否则请进入容器sessions文件夹并删除user.session! \n现准备重启机器人! ")
                else:
                    await self.bot.delete_messages(self.userid, msg)
                    login = True
            if login:
                await self.user.connect()
                async with self.bot.conversation(sender, timeout=100) as conv:
                    msg = await conv.send_message('请输入手机号：\n例如：+8618888888888')
                    phone = await conv.get_response()
                    await self.user.send_code_request(phone.raw_text, force_sms=False)
                    msg = await conv.send_message('请输入手机验证码:\n例如`code12345code`\n两边的**code**必须有！')
                    code = await conv.get_response()
                    await self.user.sign_in(phone.raw_text, code.raw_text.replace('code', ''))
                    await self.bot.send_message(self.userid, '恭喜您已登录成功！\n自动重启中！')
        except TimeoutError:
            await self.bot.edit_message(msg, '登录已超时，对话已停止')
        except Exception as e:
            title = "【💥错误💥】"
            name = "文件名：" + path.split(__file__)[-1].split(".")[0]
            function = "函数名：" + e.__traceback__.tb_frame.f_code.co_name
            details = "错误详情：第 " + str(e.__traceback__.tb_lineno) + " 行"
            message = f"{title}\n\n{name}\n{function}\n错误原因：{str(e)}\n{details}"
            await self.bot.send_message(self.userid, message)
            self.log.warning(f"错误--->{message}")