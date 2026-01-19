from functools import lru_cache
from typing import Any

from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import (
    DotEnvSettingsSource,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
)


class EVCustomSource(EnvSettingsSource):
    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        if field_name == "trusted_clients":
            # convert trusted clients to a string set.
            return set(map(str.strip, value.split(","))) if value else set()
        return super().prepare_field_value(field_name, field, value, value_is_complex)


class DotEnvEVCSource(DotEnvSettingsSource, EVCustomSource):
    pass


class Settings(BaseSettings):
    """Application settings."""

    # External API configuration
    api_username: str
    api_password: str
    api_url: str
    api_timeout: int = 30

    # Cache configuration
    cache_type: str = "redis"
    cache_default_timeout: int = 5 * 24 * 60 * 60  # 5 days
    redis_url: str = "redis://localhost:6379/0"
    cache_excluded_paths: list[str] = ["/up"]

    # Security
    trusted_clients: set[str] = set()

    # API settings
    api_title: str = "Ezan Vakti API"
    api_description: str = (
        "Diyanet İşleri Başkanlığı tarafından yayınlanan ezan vakitlerini sağlar."
    )
    api_version: str = "0.6.0"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # parse comma separated trusted_clients using EVCustomSource
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            EVCustomSource(settings_cls),
            DotEnvEVCSource(settings_cls),
            file_secret_settings,
        )


@lru_cache
def get_settings() -> Settings:
    """Returns the application settings from environment variables."""
    return Settings()  # type: ignore
