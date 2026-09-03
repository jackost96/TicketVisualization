from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://ticketsystem:ticketsystem@localhost:5432/ticketsystem"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""

    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
