一个基于 Python、FastAPI 和 Telethon 构建的高性能、异步、模块化的机器人框架。

核心设计
本框架采用 适配器 (Adapter) 与 插件 (Plugin) 分离的设计模式，实现了高度的解耦和可扩展性。

适配器 (Adapters): 负责与外部服务（如 Telegram、Gemini AI）进行通信和集成，封装了复杂的 API 交互细节。
插件 (Plugins): 负责实现具体的业务逻辑和功能（如命令处理、消息监控、定时任务）。
主程序 (mainbot.py): 作为协调者，动态加载适配器和插件，并通过 FastAPI 启动 Web 服务，管理整个应用的生命周期。
核心函数库 (function/): 提供了一系列通用的工具集（如异步 HTTP 请求、数据库、日志、环控变量管理），简化开发。
✨ 主要特性
完全异步: 基于 asyncio，所有 I/O 操作均为非阻塞，性能卓越。
高度模块化: 功能通过插件动态加载，易于独立开发、测试和分发。
轻松扩展: 通过适配器模式，可以方便地接入新的聊天平台或 AI 服务。
配置驱动: 所有敏感信息和配置均通过环境变量管理，安全且灵活。
Web 服务集成: 内置 FastAPI，可以轻松地为机器人添加 Web API 接口或管理面板。
强大的工具集: 自带封装好的数据库 ORM (SQLAlchemy)、模拟浏览器请求 (curl_cffi)、定时任务 (aiocron) 等常用库。
🚀 快速开始
1. 环境要求
Python 3.8 或更高版本
bash 环境 (用于执行启动脚本)
2. 安装
克隆本仓库到您的本地机器：

Bash

git clone <your-repository-url>
cd <repository-directory>
安装所需的 Python 依赖包：

Bash

pip install -r requirements.txt
3. 配置
所有配置都存储在 env/config.sh 文件中。在首次启动前，请务必根据您的实际情况修改此文件。

复制一份配置模板（如果 config.sh 不存在）：

Bash

cp env/config.sh.template env/config.sh
编辑 env/config.sh 文件，填入必要的 API Keys、代理设置、数据库信息等。这是一个示例片段：

Bash

# telegram bot api
export api_id=123456
export api_hash=xxxxxxxxxxxxxxxxxxxxxxxxxx
export bot_token=123456789:xxxxxxxxxxxxxxxxxxxxxxxxxx

# 代理
export proxy_on=true # 是否开启代理 true | false
export proxy_host=127.0.0.1
export proxy_port=7890

# gemini api
export gemini_api_key=xxxxxxxxxxxxxxxxxxxxxxxxxx
export gemini_base_url="https://xxxx/v1"

# ... 其他配置 ...
4. 运行
执行启动脚本来运行程序：

Bash

bash start.sh
该脚本会自动加载环境变量并启动 FastAPI 服务。

🛠️ 开发指南
我们欢迎您为本框架开发新的适配器和插件。

开发适配器 (Adapter)
适配器是连接外部服务的桥梁。

1. 基础结构
文件位置: adapters/ 目录。
基类: 必须继承 adapters.BaseAdapter。
核心要素:
name: ClassVar[str]: 适配器的唯一标识符。
obj: ClassVar[T]: 指向自身实例的类变量，用于全局访问。
async def start(self): 实现服务连接和初始化的异步方法。
2. 代码模板
Python

# adapters/my_new_adapter.py
from typing import ClassVar
from adapters import BaseAdapter
from function.PrintLog import PrintMethodClass

class MyNewAdapter(BaseAdapter["MyNewAdapter"]):
    # 适配器的唯一名称
    name: ClassVar[str] = "my_new_adapter"
    # 保存自身实例，方便全局访问
    obj: ClassVar["MyNewAdapter"] = None

    def __init__(self):
        self.log = PrintMethodClass()
        # ...

    async def start(self):
        """
        在应用启动时执行的初始化逻辑。
        """
        self.log.info(f"[{self.name}] 适配器正在启动...")
        # ... 连接外部服务的代码 ...
        self.log.info(f"[{self.name}] 适配器启动成功！")
    
    # ... 其他为插件提供的公共方法 ...
开发插件 (Plugin)
插件是实现具体功能的地方。

1. 基础结构
文件位置: plugin/ 目录。
基类: 必须继承 plugin.BasePlugin。
核心要素:
plugin_method: ClassVar[str]: 插件的帮助说明，供 /help 命令使用。
__init__(self): 插件的构造函数，用于获取适配器实例并注册事件处理器。
2. 代码模板
Python

# plugin/my_new_plugin.py
from plugin import BasePlugin
from adapters.telegram import TelegramAdapter
from telethon import events, TelegramClient
from telethon.tl.custom.message import Message

class MyNewPlugin(BasePlugin):
    # 插件的帮助信息
    plugin_method: str = "我的新插件\n\n使用方法：发送 /mycommand"

    def __init__(self):
        # 1. 获取已初始化的 Telegram 适配器实例
        self.client: TelegramAdapter = TelegramAdapter.obj
        
        # 安全检查
        if not self.client:
            return

        # 2. 获取底层的 Telethon 客户端
        self.user: TelegramClient = self.client.get_user_client
        
        # 3. 注册事件处理器
        self.user.add_event_handler(
            self.my_command_handler, 
            events.NewMessage(pattern=r'^/mycommand$', outgoing=True)
        )

    async def my_command_handler(self, event: Message):
        """
        处理 /mycommand 指令的回调函数。
        """
        await event.reply("Hello from MyNewPlugin!")

3. 使用核心函数库
您可以直接从 function/ 目录导入各种工具来加速开发：

function.AsyncMethod.ReqMethod: 发起异步 HTTP 请求。
function.AsyncMethod.EnvMethod: 读取环境变量。
function.sqlMethod.AsyncSQLAlchemyMethod: 操作数据库。
function.PrintLog.PrintMethodClass: 打印彩色日志。
...等等。
📁 项目结构
.
├── adapters/             # 适配器目录
│   ├── __init__.py       # 适配器基类
│   ├── telegram.py       # Telegram 适配器
│   └── gemini.py         # Gemini AI 适配器
├── plugin/               # 插件目录
│   ├── __init__.py       # 插件基类
│   └── ...               # 各种功能插件
├── function/             # 核心函数与工具库
│   ├── __init__.py
│   └── ...
├── module/               # 复杂的业务逻辑模块
├── env/                  # 环境配置目录
│   └── config.sh         # 环境变量配置文件
├── cache/                # 缓存目录
├── mainbot.py            # 主程序入口
├── start.sh              # 启动脚本
└── requirements.txt      # Python 依赖
🤝 贡献
欢迎任何形式的贡献！如果您有好的想法或发现了 Bug，请随时提交 Pull Request 或创建 Issue。

Fork 本仓库
创建您的新分支 (git checkout -b feature/AmazingFeature)
提交您的更改 (git commit -m 'Add some AmazingFeature')
推送到分支 (git push origin feature/AmazingFeature)
提交 Pull Request
📄 许可证
本项目采用 MIT 许可证。
