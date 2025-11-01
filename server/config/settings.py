"""
Configuration Settings for LearnPro Platform
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = ConfigDict(extra='ignore')  # Allow extra fields from .env
    
    # Application
    APP_NAME: str = "LearnPro - Agentic RAG Adaptive Learning System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_PREFIX: str = "/api/v1"
    
    # Azure OpenAI - System 1 (GPT-4.1)
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    AZURE_OPENAI_DEPLOYMENT_GPT_4_1: str = os.getenv("AZURE_OPENAI_API_DEPLOYMENT_NAME_GPT_4_1", "gpt-4.1")
    AZURE_OPENAI_DEPLOYMENT_GPT_4_1_MINI: str = os.getenv("AZURE_OPENAI_API_DEPLOYMENT_NAME_GPT_4_1_MINI", "gpt-4.1-mini")
    
    # Azure OpenAI - System 2 (GPT-5)
    AZURE_OPENAI_API_KEY_2: str = os.getenv("AZURE_OPENAI_API_KEY_2", "")
    AZURE_OPENAI_ENDPOINT_2: str = os.getenv("AZURE_OPENAI_ENDPOINT_2", "")
    AZURE_OPENAI_API_VERSION_2: str = os.getenv("AZURE_OPENAI_API_VERSION_2", "2024-02-15-preview")
    AZURE_OPENAI_DEPLOYMENT_GPT_5: str = os.getenv("AZURE_OPENAI_API_DEPLOYMENT_NAME_GPT_5", "gpt-5")
    AZURE_OPENAI_DEPLOYMENT_GPT_5_MINI: str = os.getenv("AZURE_OPENAI_API_DEPLOYMENT_NAME_GPT_5_MINI", "gpt-5-mini")
    
    # MongoDB
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "learnpro")
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    REDIS_TTL: int = int(os.getenv("REDIS_TTL", "3600"))  # 1 hour default
    
    # ChromaDB
    CHROMADB_PATH: str = os.getenv("CHROMADB_PATH", "./data/chromadb")
    CHROMADB_COLLECTION_TOPICS: str = "topics"
    CHROMADB_COLLECTION_QUESTIONS: str = "questions"
    
    # Pathway
    PATHWAY_INPUT_CONNECTOR: str = os.getenv("PATHWAY_INPUT_CONNECTOR", "kafka")
    PATHWAY_OUTPUT_CONNECTOR: str = os.getenv("PATHWAY_OUTPUT_CONNECTOR", "kafka")
    PATHWAY_KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("PATHWAY_KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    
    # PDF Processing
    PDF_DOC_PATH: str = os.getenv("PDF_DOC_PATH", "./doc")
    OUTPUT_PATH: str = os.getenv("OUTPUT_PATH", "./output")
    
    # Embeddings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION: int = 384  # for all-MiniLM-L6-v2
    
    # Quiz Generation
    QUIZ_MIN_QUESTIONS: int = 5
    QUIZ_MAX_QUESTIONS: int = 20
    QUIZ_DEFAULT_QUESTIONS: int = 10
    
    # Performance Thresholds
    MASTERY_THRESHOLD: float = 0.8  # 80% for mastery
    WEAK_AREA_THRESHOLD: float = 0.6  # Below 60% is weak
    STRUGGLE_THRESHOLD: int = 3  # 3+ incorrect attempts = struggle
    
    # Pathway Configuration
    PATHWAY_BATCH_SIZE: int = 100
    PATHWAY_WINDOW_SIZE: int = 300  # seconds
    PATHWAY_ANOMALY_THRESHOLD: float = 2.0  # standard deviations
    PATHWAY_KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    PATHWAY_BUFFER_SIZE: int = 10000


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings
