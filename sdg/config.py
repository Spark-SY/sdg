from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LOCAL_STORAGE_PATH: str = "./data"

settings = Settings()
