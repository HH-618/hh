from openai import OpenAI
from juju.core.config import load_settings


class LLMClient:
    def __init__(self, client: OpenAI = None):
        if client is None:
            settings = load_settings()
            client = OpenAI(
                base_url=settings.llm.api_url,
                api_key=settings.llm.api_key,
            )
        self.client = client


def get_client() -> LLMClient:
    return LLMClient()
