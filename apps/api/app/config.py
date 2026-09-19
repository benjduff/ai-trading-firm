from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://trading:trading@localhost:5432/ai_trading_firm"
    sec_edgar_user_agent: str = "benjduff xmrduff@gmail.com"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
