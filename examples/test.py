from typing import Dict

from llama_index.core import Settings
from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.llms.openai import OpenAI
from llama_index.llms.openai.utils import ALL_AVAILABLE_MODELS, CHAT_MODELS
DEEPSEEK_MODELS: Dict[str, int] = {
    "deepseek-chat": 128000,
}
ALL_AVAILABLE_MODELS.update(DEEPSEEK_MODELS)
CHAT_MODELS.update(DEEPSEEK_MODELS)

llm = OpenAI(
    model="deepseek-chat",
    api_key="sk-5a50b36c0c7d4e04aa43d71fdd5d0d48",  # uses OPENAI_API_KEY env var by default
    api_base="https://api.deepseek.com/v1",
)

Settings.llm = llm
chat_engine = SimpleChatEngine.from_defaults()
# 流式打印
# 使用场景：当需要有用户交互时比较方便，做智能体的话，可以用
chat_engine.streaming_chat_repl()
# 非流式打印
# chat_engine.chat_repl()
