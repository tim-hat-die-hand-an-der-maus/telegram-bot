from dataclasses import dataclass
from typing import Self

from bs_config import Env
from bs_nats_updater import NatsConfig


@dataclass(frozen=True, kw_only=True)
class ApiConfig:
    base_url: str
    token: str

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            base_url=env.get_string("base-url", default="http://api.tim-api"),
            token=env.get_string("token", required=True),
        )


@dataclass(frozen=True, kw_only=True)
class TelegramConfig:
    poll_chat_id: int
    token: str

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            poll_chat_id=env.get_int("poll-chat-id", required=True),
            token=env.get_string("token", required=True),
        )


@dataclass(frozen=True, kw_only=True)
class Config:
    api: ApiConfig
    app_version: str
    nats: NatsConfig
    telegram: TelegramConfig
    sentry_dsn: str | None

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            api=ApiConfig.from_env(env / "api"),
            app_version=env.get_string("app-version", default="dev"),
            nats=NatsConfig.from_env(env / "nats"),
            telegram=TelegramConfig.from_env(env / "telegram"),
            sentry_dsn=env.get_string("sentry-dsn"),
        )


def load_config() -> Config:
    env = Env.load(include_default_dotenv=True)
    return Config.from_env(env)
