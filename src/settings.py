from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Legal Document Simplifier"
    environment: str = "development"
    debug: bool = True

    # Later you’ll add:
    # database_url: str
    # redis_url: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
