from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./compass.db"
    session_expiry_hours: int = 24
    cookie_secure: bool = False  # Set True in production when serving over HTTPS

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_temperature: float = 0.7
    ollama_timeout_seconds: float = 30.0


settings = Settings()
