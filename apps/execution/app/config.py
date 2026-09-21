from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://trading:trading@localhost:5432/ai_trading_firm"

    broker_backend: Literal["mock", "ibkr"] = "mock"
    ibkr_host: str = "127.0.0.1"
    ibkr_port: int = 7497  # TWS paper trading default; IB Gateway paper default is 4002
    ibkr_client_id: int = 7

    polygon_api_key: Optional[str] = None

    # Hard risk limits, re-validated independently of whatever the research
    # system's Risk module proposed - this service does not trust its caller.
    max_position_pct_hard_cap: float = 10.0
    max_notional_usd_hard_cap: float = 5000.0
    max_proposal_age_hours: int = 48

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
