from typing import Literal
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

base_model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    extra="ignore",
)


class TwilioSettings(BaseSettings):
    """Settings for Twilio integration."""

    model_config = SettingsConfigDict(**base_model_config, env_prefix="TWILIO_")

    account_sid: str = Field(description="The Twilio account SID")
    api_key: str = Field(description="The Twilio API key")
    api_secret: str = Field(description="The Twilio API secret")
    auth_token: str = Field(description="The Twilio auth token")
    phone_number: str = Field(description="The Twilio phone number")


class Settings(BaseSettings):
    """The settings for Voice API."""

    model_config = SettingsConfigDict(**base_model_config)

    app_environment: Literal["LOCAL", "PROD"] = Field(
        default="PROD", description="PROD or LOCAL"
    )

    @computed_field
    @property
    def is_local(self) -> bool:
        return self.app_environment == "LOCAL"

    twilio: TwilioSettings = Field(default_factory=TwilioSettings)


settings = Settings()
