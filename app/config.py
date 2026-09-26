from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    GOOGLE_DRIVE_FOLDER_ID: str | None = None
    GOOGLE_SERVICE_ACCOUNT_JSON: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
         extra="ignore",
    )


settings = Settings()