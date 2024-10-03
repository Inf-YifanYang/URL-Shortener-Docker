from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = 'url_shortener'
    ENVIRONMENT: str = 'local'
    DATABASE_URL: str = 'sqlite:///url_shortener.db'
    # BASE_URL: str = 'http://localhost:8080'
    BASE_URL: str = 'http://0.0.0.0:8080'
    SHORTEN_URL_SIZE: int = 5
    
def get_settings() -> Settings:
    settings = Settings()
    return settings