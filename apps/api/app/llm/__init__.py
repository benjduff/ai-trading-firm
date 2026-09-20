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


def get_red_team_gateway() -> ModelGateway:
    """A distinct model from get_default_gateway() so Red Team doesn't share the
    Fundamental Analyst's exact model, per CLAUDE.md's Red Team independence rule.
    Ideally a different provider entirely; same provider/different model for now."""
    if not settings.openai_api_key:
        raise ModelGatewayNotConfiguredError(
            "OPENAI_API_KEY is not set; add it to apps/api/.env"
        )
    return OpenAIGateway(
        api_key=settings.openai_api_key, model=settings.openai_red_team_model
    )
