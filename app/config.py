import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration with common settings"""
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        pass


class BaseDatabaseConfig(Config):
    """Configuration that reads the database URL from a single env var"""
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_CONNECTION_STRING')


class DevelopmentConfig(BaseDatabaseConfig):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(BaseDatabaseConfig):
    """Production configuration."""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
