from pydantic_settings import BaseSettings, SettingsConfigDict

# Configuración de la app - Datos para conectarse a PostgreSQL
class Settings(BaseSettings):
    APP_NAME: str = "PsicoDesk API"
    APP_VERSION: str = "0.1.0"
    
    DATABASE_HOST: str
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )
    
settings = Settings()