from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Legal Document Simplifier"
    app_version: str = "0.1.0"
    debug: bool = True

    # DB
    DATABASE_URL: str

    # Security
    environment: str = "development"
    SECRET_KEY: str = "change-me"
    TOKEN_EXPIRE_MINUTES: int = 30

    # File handling
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: list[str] = ["txt", "pdf", "docx"]


    class Config:
        env_file = ".env"
        extra = "ignore"  # ignore extra env vars


settings = Settings()
