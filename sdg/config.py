from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LOCAL_STORAGE_PATH: str = "./data"
    LOCAL_META_STORAGE_PATH: str = "./metadata"

settings = Settings()
