import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.infra.config.auth import AuthSettings
from app.infra.config.postgres import PostgreSQLSettings


class Settings(BaseSettings):
    postgres: PostgreSQLSettings
    auth: AuthSettings

    model_config = SettingsConfigDict(env_nested_delimiter="__")


def generate_settings():
    load_dotenv(override=True, dotenv_path=os.getcwd() + "/.env")
    return Settings()  # type: ignore
