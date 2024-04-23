from pydantic_settings import BaseSettings


class Config(BaseSettings):
    jwt_secret_key: str = "secret"


config = Config()
