from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CRM BDS API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql://crm_bds:crm_bds@localhost:5432/crm_bds"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    default_admin_email: str = "admin@example.com"
    default_admin_password: str = "Admin@123456"
    default_admin_name: str = "System Admin"
    seed_demo_users: bool = False
    demo_user_password: str = "Admin@123456"
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
