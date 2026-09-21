from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://trading:trading@localhost:5432/ai_trading_firm"
    sec_edgar_user_agent: str = "benjduff xmrduff@gmail.com"

    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-5.5"
    openai_red_team_model: str = "gpt-5.5-pro"

    polygon_api_key: Optional[str] = None

    execution_service_url: str = "http://localhost:8100"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
