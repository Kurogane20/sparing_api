from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Any

class Settings(BaseSettings):
    app_env: str = "dev"
    tz: str = "Asia/Jakarta"
    db_url: str = "mysql+aiomysql://sparing:sparing@mysql:3306/sparing"
    jwt_secret: str = "change_me"
    jwt_alg: str = "HS256"
    access_token_expire_min: int = 60
    refresh_token_expire_min: int = 60*24*7
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    rate_limit_per_min: int = 120
    log_level: str = "info"

    # 👇 add these two so pydantic accepts the values from .env
    gunicorn_workers: int = 2
    uvicorn_workers: int = 1

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _coerce_cors(cls, v: Any):
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                return v  # JSON array will be parsed by pydantic
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",  # 👈 future-proof: ignore any other unexpected envs
    )

settings = Settings()
