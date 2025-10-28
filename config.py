
from pydantic_settings import BaseSettings
import os 
import secrets
from dotenv import load_dotenv
load_dotenv()
class Settings(BaseSettings):
    api_url: str = "http://127.0.0.1:8000/api/"

class Config:
    env_file = ".env"

settings = Settings()