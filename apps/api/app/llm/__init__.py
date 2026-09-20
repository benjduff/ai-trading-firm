from app.config import settings
from app.llm.gateway import ModelGateway
from app.llm.openai_gateway import OpenAIGateway


class ModelGatewayNotConfiguredError(RuntimeError):
    pass


def get_default_gateway() -> ModelGateway:
    if not settings.openai_api_key:
        raise ModelGatewayNotConfiguredError(
            "OPENAI_API_KEY is not set; add it to apps/api/.env"
        )
    return OpenAIGateway(api_key=settings.openai_api_key, model=settings.openai_model)
