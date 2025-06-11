from json import loads, JSONDecodeError
from openai import AsyncOpenAI
from adapters import OpenAiChatAdapter, BaseAdapter
from function.PrintLog import PrintMethodClass
from typing import Optional, List, Dict, Literal, ClassVar
from urllib.parse import urlparse, urlunparse, ParseResult
from function.AsyncMethod import EnvMethod, ReqMethod, AsyncResponse

class GeminiAdapter(OpenAiChatAdapter, BaseAdapter['GeminiAdapter']):

    obj: ClassVar["GeminiAdapter"] = None
    name: ClassVar[str] = "gemini_adapter"

    def __init__(self):
        self.req = ReqMethod()
        self.log = PrintMethodClass()
        self._gemini_base_url: str = None
        self._gemini_api_key: Optional[str] = None
        self._gemini_client: Optional[AsyncOpenAI] = None
        self._gemini_models: list = []
        # self.gemini_model: Optional[str] = None

    def _load_config(self):
        """
        初始化配置
        """
        env_config = [
            ('_gemini_base_url', 'gemini_base_url', "https://generativelanguage.googleapis.com/v1beta"),
            ("_gemini_api_key", 'gemini_api_key', None),
        ]

        missing = EnvMethod.checkEnv(self, env_config, exit=False)
        must = {'gemini_api_key'}

        missing_and_must_vars = must.intersection(set(missing)) # 返回两个set中相同元素

        if missing_and_must_vars:
            self.log.warning(f"[Gemini] 必须的环境变量缺失或无效 {list(missing_and_must_vars)}。")
            return False
        self.log.info("[Gemini] 核心配置已加载")
        return True

    def _create_client(self):
        """
        实例会话
        """
        self.log.info(f"[Gemini] 创建对话实例")
        self._gemini_client = AsyncOpenAI(api_key=self._gemini_api_key, base_url=self._gemini_base_url)

    def _code_base_url(self):
        """
        处理gemini_base_url
        """
        parsed_url = urlparse(self._gemini_base_url)
        path_list = [x for x in parsed_url.path.split("/") if x]
        if "v1beta" not in path_list:
            path_list.append("v1beta")
        new_path = "/" + "/".join(path_list)

        self._gemini_base_url = urlunparse((parsed_url.scheme, parsed_url.netloc, new_path, parsed_url.params, parsed_url.query, parsed_url.fragment))
        self.log.info(f"[Gemini]  OpenAI 兼容层 Base URL: {self._gemini_base_url}")

    async def _check_model(self):
        """
        检测key可用model
        """
        self.log.info("[Gemini] 获取模型列表...")
        opt = {
            "method": "GET",
            "url": f"{self._gemini_base_url}/models?key={self._gemini_api_key}"
        }
        response: AsyncResponse = await self.req.async_requests(opt, "get_gemini_models")
        if response.status != 200:
            self.log.warning("[Gemini] get_gemini_models失败")
            return False
        try:
            response = loads(response.text)
        except JSONDecodeError:
            self.log.warning("响应内容错误")
            return False
        if len(response['models']) == 0:
            self.log.warning("[Gemini] 无可用model")
            return False
        for x in response['models']:
            name: str = x['name']
            models = name.split("/")[1] # 模型资源名称
            inputTokenLimit = x['inputTokenLimit'] # 模型能接受的最大输入 token 数量。
            outputTokenLimit = x['outputTokenLimit'] # 模型能生成的最大输出 token 数量。
            self._gemini_models.append(models)
        self.log.info(f"[Gemini] 可用模型 {self._gemini_models}")
        return True
    
    def get_chat_client(self):
        """
        获取chat对话实例
        """
        return self._gemini_client
    
    def get_chat_models(self):
        """
        获取Ai模型列表
        """
        return self._gemini_models

    async def start(self):
        if not self._load_config():
            raise RuntimeError(f"核心环境变量缺失未能启动")

        self._code_base_url()
        if not await self._check_model():
            raise RuntimeError(f"无法获取模型列表")

        self._create_client()