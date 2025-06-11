import asyncio
from json import loads
from os import path
from typing import Optional, ClassVar
from aiocron import crontab
from abc import ABC, abstractmethod
from function import pjt_path, env_path
from function.PrintLog import PrintMethodClass
from function.AsyncMethod import EnvMethod, ReqMethod
from adapters import BaseAdapter
from dotenv import load_dotenv, dotenv_values
from telethon import TelegramClient, connection, events, Button
from fastapi import APIRouter, Request, Depends, HTTPException
from telethon.errors import ApiIdInvalidError, ApiIdPublishedFloodError, AuthKeyError, AuthKeyUnregisteredError, AuthKeyPermEmptyError, PhoneNumberInvalidError, SessionPasswordNeededError, PhoneNumberUnoccupiedError, PhoneCodeInvalidError, PhoneCodeExpiredError, UserDeactivatedBanError, UserDeactivatedError, UserMigrateError, PhoneNumberBannedError, FloodWaitError # 导入一些常见的 Telethon 异常

class TelegramClientProvider(ABC):
    """
    Telegram 客户端提供者的接口。

    这个接口定义了外部代码如何获取 Bot 和 User 客户端实例，
    而不关心客户端在实现类内部是如何存储或管理的。
    """
    @property
    @abstractmethod
    def get_bot_client(self) -> Optional[TelegramClient]: ...

    @property
    @abstractmethod
    def get_user_client(self) -> Optional[TelegramClient]: ...

    @property
    @abstractmethod
    def get_user_id(self) -> int: ...

    @property
    @abstractmethod
    def get_bot_id(self) -> int: ...


class TelegramAdapter(BaseAdapter['TelegramAdapter'], TelegramClientProvider):
    """
    Telegram 聊天适配器
    """
    obj: ClassVar['TelegramAdapter'] = None
    name: ClassVar[str]  = "telegram_adapter"
    
    def __init__(self):
        self.router = APIRouter()
        self.req = ReqMethod()
        self.log = PrintMethodClass()
        self._bot_client: Optional[TelegramClient] = None
        self._user_client: Optional[TelegramClient] = None
        self.user_id: Optional[int] = None
        self.token: Optional[str] = None
        self.api_id: Optional[int] = None
        self.api_hash: Optional[str] = None
        self.proxy_type: Optional[str] = None
        self.host: Optional[str] = None
        self.port: Optional[int] = None # load_config 会尝试转 int
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        # self.router.add_api_route("/")

    @property
    def get_bot_client(self) -> Optional[TelegramClient]:
        """
        实现接口方法：获取 Bot 客户端。
        """
        # 返回存储在实例属性中的 Bot 客户端
        return self._bot_client

    @property
    def get_user_client(self) -> Optional[TelegramClient]:
        """
        实现接口方法：获取 User 客户端。
        """
        # 返回存储在实例属性中的 User 客户端
        return self._user_client
    
    @property
    def get_bot_id(self) -> Optional[str]:
        """
        实现接口方法：获取 Bot id。
        """
        return int(self.token.split(":")[0])
    @property
    def get_user_id(self) -> Optional[int]:
        """
        实现接口方法：获取 User id。
        """
        return self.user_id

    def _load_config(self):
        create = False
        env_config = [
            ("user_id", 'Telethon_user_id', None, {"codeInt": True}),
            ('token', 'Telethon_bot_token', None),
            ('api_id', 'Telethon_api_id', None), 
            ('api_hash', 'Telethon_api_hash', None),
            ('proxy_type', 'Telethon_proxy_type', None),
            ('host', 'Telethon_proxy_host', None),
            ('port', 'Telethon_proxy_port', None),
            ('username', 'Telethon_proxy_username', None),
            ('password', 'Telethon_proxy_password', None),
        ]

        missing = EnvMethod.checkEnv(self, env_config, exit=False)
        must = {'Telethon_user_id', 'Telethon_bot_token', 'Telethon_api_id', 'api_hash'}

        missing_and_must_vars = must.intersection(set(missing)) # 返回两个set中相同元素

        if missing_and_must_vars:
            self.log.warning(f"[Telethon] 适配器启动失败：必须的环境变量缺失或无效 {list(missing_and_must_vars)}。")
            return False
        self.log.info("[Telethon] 核心配置已加载")
        return True

    def proxy_method(self):
        if self.username and self.proxy_type != "MTProxy":  # 需要认证信息的http或者socks5
            return {
                "proxy_type": self.proxy_type,
                "addr": self.host,
                "port": self.port,
                "username": self.username,
                "password": self.password
            }
        elif self.proxy_type == "MTProxy":  # MTProxy
            return (self.host, self.port, self.password)
        elif self.proxy_type != "MTProxy":  # 无需认证信息的http或者socks5
            return (self.proxy_type, self.host, self.port)
        return None
    
    def client_config(self):
        connection_type = connection.ConnectionTcpFull
        if self.proxy_type == "MTProxy":
            connection_type = connection.ConnectionTcpMTProxyRandomizedIntermediate
        elif self.proxy_type == "http":
            connection_type = connection.ConnectionTcpAbridged

        return {
            'api_id': self.api_id,
            'api_hash': self.api_hash,
            'connection': connection_type,
            'proxy': self.proxy_method(),
            'connection_retries': None,
            'auto_reconnect': True,
            'timeout': 30
        }

    async def _create_client(self):
        bot_creation_successful = False # 用于 BOT 客户端的状态
        user_creation_successful = False # 用于 USER 客户端的状态

        self.log.info("[Telethon] 开始初始化客户端...")
        bot_token = self.token

        # --- 初始化 BOT 客户端 ---
        self.log.info("[Telethon] 准备初始化 BOT 客户端...")
        session_path_bot = path.join(pjt_path, "cache", "bot")
        bot_client = TelegramClient(session_path_bot, **self.client_config())
        self.log.info("[Telethon] BOT 客户端实例创建成功。")

        try:
            self.log.info("[Telethon] 正在连接 BOT 客户端...")
            await bot_client.connect()
            if bot_client.is_connected():
                self.log.info("[Telethon] BOT 客户端连接成功")
            else:
                # 这种情况比较少见，connect() 通常要么成功要么抛异常
                self.log.warning("[Telethon] BOT 客户端 connect() 调用后仍未连接")

            self.log.info("[Telethon] 正在启动 BOT 客户端 (使用 token)...")
            # client.start(bot_token=...) 会尝试登录
            # 如果 token 无效或有问题，这里会抛出异常
            await bot_client.start(bot_token=bot_token)
            # 检查是否真的以 bot 身份登录成功
            if await bot_client.is_bot():
                self._bot_client = bot_client
                self.log.info("[Telethon] BOT 客户端启动并认证成功！")
                bot_creation_successful = True # 标记 BOT 客户端创建成功
            else:
                self.log.warning("[Telethon] BOT 客户端启动后未能确认为 Bot，可能 Token 有误或登录失败")
                await bot_client.disconnect()
        except (ApiIdInvalidError, AuthKeyError, AuthKeyUnregisteredError, AuthKeyPermEmptyError) as e:
            self.log.warning(f"[Telethon] BOT 客户端启动失败：API ID/Hash 或授权密钥相关错误 - {type(e).__name__}: {e}")
        except ConnectionError as e:
            self.log.warning(f"[Telethon] BOT 客户端连接/启动失败：网络连接错误 - {type(e).__name__}: {e}")
        except Exception as e:
            self.log.warning(f"[Telethon] BOT 客户端连接/启动时发生未知错误: {type(e).__name__} - {e}")
        finally:
            if not bot_creation_successful:
                return bot_creation_successful

        # --- 初始化 USER 客户端 ---
        self.log.info("[Telethon] 准备初始化 USER 客户端...")
        session_path_user = path.join(pjt_path, "cache", "user")
        user_client = TelegramClient(session_path_user, **self.client_config())
        self.log.info("[Telethon] USER 客户端实例创建成功。")

        try:
            self.log.info("[Telethon] 正在连接 USER 客户端...")
            await user_client.connect()
            if user_client.is_connected():
                self.log.info("[Telethon] USER 客户端连接成功。")
            else:
                self.log.warning("[Telethon] USER 客户端 connect() 调用后仍未连接")

            # 检查用户是否已授权 (已登录)
            if not await user_client.is_user_authorized():
                self.log.warning("[Telethon] USER 客户端未授权 (未登录), 需前往Bot 发送 /login 进行登录")
                # 在实际应用中，这里通常需要一个交互式登录流程，或者提示用户手动登录。
                # 对于自动化脚本，如果 session 文件无效或首次运行，这里就无法自动完成。
                # 你可以选择将 client 赋值给 self._user_client，但它将是未登录状态。
                # 或者，如果强制要求登录，这里可以标记为失败。
                self._user_client = user_client # 如果你想保留未授权的客户端实例
            else:
                self.log.info("[Telethon] USER 客户端已授权，尝试静默启动...")
                # 对于已授权的用户客户端，调用 start() 通常不会有太多交互，除非 session 过期等问题
                # 注意：不带参数的 client.start() 会尝试用已有的 session 登录
                await user_client.start() # 确保这个调用不会卡住等待输入
                # 再次检查登录状态，确保 start() 后仍然是登录的
                if await user_client.is_user_authorized():
                    self._user_client = user_client # 赋值给实例属性
                    self.log.info("[Telethon] USER 客户端启动并认证成功！")
                    user_creation_successful = True
                else:
                    self.log.warning("[Telethon] USER 客户端启动后未能保持授权状态，可能 Session 已失效。")
                    await user_client.disconnect()
        except SessionPasswordNeededError:
            self.log.warning("[Telethon] USER 客户端启动失败：需要两步验证密码 (2FA), 请在客户端(手机/电脑)打开设置->隐私与安全->两步验证, 关闭两步验证")
        except (PhoneNumberInvalidError, PhoneNumberUnoccupiedError, PhoneNumberBannedError) as e:
            self.log.warning(f"[Telethon] USER 客户端启动失败：手机号码问题 - {type(e).__name__}: {e}")
        except (PhoneCodeInvalidError, PhoneCodeExpiredError) as e:
            self.log.warning(f"[Telethon] USER 客户端启动失败：验证码问题 - {type(e).__name__}: {e}")
        except (UserDeactivatedBanError, UserDeactivatedError) as e:
            self.log.warning(f"[Telethon] USER 客户端启动失败：账户被封禁或停用 - {type(e).__name__}: {e}")
        except UserMigrateError as e:
            self.log.warning(f"[Telethon] USER 客户端遭遇 DC 迁移: {e.new_dc}. Telethon 通常会自动处理。")
        except ConnectionError as e:
            self.log.warning(f"[Telethon] USER 客户端连接/启动失败：网络连接错误 - {type(e).__name__}: {e}")
        except Exception as e:
            self.log.warning(f"[Telethon] USER 客户端连接/启动时发生未知错误: {type(e).__name__} - {e}")
        finally:
            if not user_creation_successful:
                return user_creation_successful
            
        return True if bot_creation_successful is True else False
    
    # async def _create_client(self):
    #     self.log.info("开始初始化客户端")
    #     bot_token = self.token
    #     for x in ["BOT", "USER"]:
    #         if x != "BOT":
    #             bot_token = None
    #         session_path = path.join(PjtPath, "cache", x.lower())
    #         client = TelegramClient(session_path, **self.client_config())
    #         self.log.info(f"{x} 客户端实例创建成功")

    #         # 建立连接，不触发交互式登录
    #         self.log.info(f"正在连接 {x} 客户端...")
    #         await client.connect()
    #         self.log.info(f"{x} 客户端连接成功")

    #         if bot_token:
    #             # Bot 客户端，使用 token 启动
    #             self.log.info("正在启动 BOT 客户端...")
    #             await client.start(bot_token=bot_token)
    #             self._bot_client = client
    #             self.log.info("BOT 客户端启动成功")
    #         else:
    #             self.log.info("正在启动 USER 客户端...")
    #             if not await client.is_user_authorized():
    #                 self.log.warning("USER 客户端未登录。")
    #                 self._user_client = client
    #             else:
    #                 self.log.info("USER 客户端已授权，尝试启动...")
    #                 await client.start()
    #                 self._user_client = client
    #                 self.log.info("USER 客户端启动成功")

    async def hello(self):
        opt = {
            'method': 'GET',
            'url': 'http://sign.lolkda.top/api/ip'
        }
        client = self._bot_client
        response =  await self.req.async_requests(opt, "ip")
        self.log.ResetPrint()
        response = loads(response.text)
        await client.send_message(
            self.user_id,
            f'叮咚, Bot已成功启动\n当前IP：{response["ip"]}\n\n\t',
            link_preview=False
        )

    async def start(self):
        if not self._load_config():
            self.log.error(f"[Telethon] start: [False] 核心环境变量缺失未能启动", exit=False)
            return
        if not await self._create_client():
            self.log.error(f"[Telethon] start: [False] 核心环境变量缺失未能启动", exit=False)
            return
        await self.hello()