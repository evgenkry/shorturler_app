from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/shorturler_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    SECRET_KEY: str = "SUPER_SECRET_KEY_CHANGE_ME" 
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()
