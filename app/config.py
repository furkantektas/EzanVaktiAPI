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
            return set(map(str.strip, value.split(","))) if value else {}
        return super().prepare_field_value(field_name, field, value, value_is_complex)


class DotEnvEVCSource(DotEnvSettingsSource, EVCustomSource):
    pass


class Settings(BaseSettings):
    cache_type: str = "redis"
    cache_default_timeout: int = 5 * 24 * 60 * 60  # 5 days
    redis_url: str = "redis://localhost:6379/0"
    svc_wsdl_url: str
    svc_username: str
    svc_password: str
    trusted_clients: set[str] = {}

    model_config = SettingsConfigDict(
        env_file=".envs", extra="ignore", secrets_dir="/run/secrets"
    )

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
    return Settings()
