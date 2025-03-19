from autogen_ext.models.openai import OpenAIChatCompletionClient
# pip install -U "autogen-agentchat"
# pip install -U "autogen-ext[openai]"

model_client = OpenAIChatCompletionClient(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
    api_key="sk-5a50b36c0c7d4e04aa43d71fdd5d0d48",
    model_info={
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "family": "unknown",
    },
)