from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Legal Document Simplifier"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True
    database_url: str
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: set = {"txt", "pdf", "docx"}

    # redis_url: str

    class Config:
        env_prefix = "" 
        extra = "ignore"  
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
