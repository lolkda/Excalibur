# 🤖 高性能异步Chat框架

一个基于 **Python、FastAPI 和 Telethon** 构建的高性能、异步、模块化的机器人框架。

## 🧠 核心设计

框架采用 **适配器 (Adapter)** 与 **插件 (Plugin)** 分离的设计模式，实现了高度的解耦和可扩展性。

* **适配器 (Adapters)**：负责与外部服务（如 Telegram、Gemini AI）进行通信和集成，封装复杂的 API 交互细节。
* **插件 (Plugins)**：实现具体的业务逻辑和功能（如命令处理、消息监控、定时任务）。
* **主程序 (`main.so`)**：作为协调者，动态加载适配器和插件，并通过 FastAPI 启动 Web 服务，管理整个应用的生命周期。
* **核心函数库 (`function/`)**：提供一系列通用工具集（如异步 HTTP 请求、数据库操作、日志系统、环境变量管理），简化开发流程。

## ✨ 主要特性

* **完全异步**：基于 asyncio，所有 I/O 操作均为非阻塞，性能卓越。
* **高度模块化**：功能通过插件动态加载，易于独立开发、测试和分发。
* **轻松扩展**：通过适配器模式，可方便接入新的聊天平台或 AI 服务。
* **配置驱动**：所有敏感信息和配置均通过环境变量管理，安全且灵活。
* **Web 服务集成**：内置 FastAPI，可为机器人添加 Web API 接口或管理面板。

## 🚀 快速开始

### 1. 环境要求

* Python 3.8 或更高版本
* bash 环境（用于执行启动脚本）

### 2. 安装

```bash
git clone <your-repository-url>
cd <repository-directory>
pip install -r requirements.txt
```

### 3. 配置

所有配置存储在 `env/config.sh` 文件中。首次启动前，请根据实际情况修改此文件。

```bash
cp env/config.sh.template env/config.sh
```

编辑 `env/config.sh` 文件，填入必要的 API Keys、代理设置、数据库信息等。例如：

```bash
# telegram bot api
export api_id=123456
export api_hash=xxxxxxxxxxxxxxxxxxxxxxxxxx
export bot_token=123456789:xxxxxxxxxxxxxxxxxxxxxxxxxx

# 代理
export proxy_on=true
export proxy_host=127.0.0.1
export proxy_port=7890

# gemini api
export gemini_api_key=xxxxxxxxxxxxxxxxxxxxxxxxxx
export gemini_base_url="https://xxxx/v1"
```

### 4. 运行

执行启动脚本：

```bash
bash start.sh
```

脚本会自动加载环境变量并启动 FastAPI 服务。

## 🛠️ 开发指南

### 开发适配器 (Adapter)

适配器是连接外部服务的桥梁。

#### 1. 基础结构

* 文件位置：`adapters/`
* 必须继承 `adapters.BaseAdapter`
* 核心字段：

  * `name: ClassVar[str]`：唯一标识符
  * `obj: ClassVar[T]`：全局访问实例
  * `async def start(self)`：初始化逻辑

#### 2. 示例模板

```python
# adapters/my_new_adapter.py
from typing import ClassVar
from adapters import BaseAdapter
from function.PrintLog import PrintMethodClass

class MyNewAdapter(BaseAdapter["MyNewAdapter"]):
    name: ClassVar[str] = "my_new_adapter"
    obj: ClassVar["MyNewAdapter"] = None

    def __init__(self):
        self.log = PrintMethodClass()

    async def start(self):
        self.log.info(f"[{self.name}] 适配器正在启动...")
        # 连接外部服务的逻辑
        self.log.info(f"[{self.name}] 适配器启动成功！")
```

### 开发插件 (Plugin)

插件负责具体功能逻辑。

#### 1. 基础结构

* 文件位置：`plugin/`
* 必须继承 `plugin.BasePlugin`
* 核心要素：

  * `plugin_method: ClassVar[str]` 帮助描述
  * `__init__()` 注册事件处理器

#### 2. 示例模板

```python
# plugin/my_new_plugin.py
from plugin import BasePlugin
from adapters.telegram import TelegramAdapter
from telethon import events, TelegramClient
from telethon.tl.custom.message import Message

class MyNewPlugin(BasePlugin):
    plugin_method: str = "我的新插件\n\n使用方法：发送 /mycommand"

    def __init__(self):
        self.client: TelegramAdapter = TelegramAdapter.obj
        if not self.client:
            return
        self.user: TelegramClient = self.client.get_user_client
        self.user.add_event_handler(
            self.my_command_handler, 
            events.NewMessage(pattern=r'^/mycommand$', outgoing=True)
        )

    async def my_command_handler(self, event: Message):
        await event.reply("Hello from MyNewPlugin!")
```

### 使用核心函数库

核心工具可从 `function/` 目录导入：

* `function.AsyncMethod.ReqMethod`: 异步 HTTP 请求
* `function.AsyncMethod.EnvMethod`: 环境变量
* `function.sqlMethod.AsyncSQLAlchemyMethod`: 数据库操作
* `function.PrintLog.PrintMethodClass`: 彩色日志

## 📁 项目结构

```
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
├── main.so               # 主程序入口
├── start.sh              # 启动脚本
└── requirements.txt      # Python 依赖
```

## 🤝 贡献

欢迎贡献！如果有新想法或发现问题，请提交 PR 或创建 Issue。

```bash
git checkout -b feature/AmazingFeature
git commit -m 'Add some AmazingFeature'
git push origin feature/AmazingFeature
```

## 📄 许可证

本项目采用 MIT 许可证。
