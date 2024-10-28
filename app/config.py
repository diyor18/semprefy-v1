from pydantic_settings import BaseSettings


# After setting env variables in the system(YT FastAPI Sanjeev video 8:50-9:20), validation and accessing is below
class Settings(BaseSettings):
    database_hostname: str 
    database_port: str
    database_password: str 
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    
    class Config: #for dev env we are using .env file, for production -> need to set up in the system
        env_file = ".env"
    

settings = Settings()

# accessing -> settings.database_password
