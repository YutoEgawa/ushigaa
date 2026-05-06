from functools import lru_cache

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ushigaa-api"
    api_prefix: str = "/v1"
    allowed_origins: list[str] = Field(
        default=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "https://ushigaa.com",
            "https://www.ushigaa.com",
        ],
        alias="ALLOWED_ORIGINS",
    )
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_anon_key: str = Field(..., alias="SUPABASE_ANON_KEY")
    request_timeout_seconds: float = 10.0
    contact_recipient_email: str = Field("y.egawa.ahstu0415@gmail.com", alias="CONTACT_RECIPIENT_EMAIL")
    sendgrid_api_key: str | None = Field(None, alias="SENDGRID_API_KEY")
    sendgrid_from_email: str | None = Field(None, alias="SENDGRID_FROM_EMAIL")
    sendgrid_from_name: str = Field("ウシガー", alias="SENDGRID_FROM_NAME")

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @computed_field
    @property
    def rest_url(self) -> str:
        return f"{self.supabase_url.rstrip('/')}/rest/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
