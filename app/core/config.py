import os
from typing import Dict, Any, Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Ice Breaker Generator"
    
    # Server Settings
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    DEBUG: bool = Field(default=False)
    
    # LLM Settings
    LLM_TYPE: str = Field(default="mistral")  # Options: mistral, llama, gpt4all
    LLM_MODEL_PATH: Optional[str] = Field(default=None)  # Path to model file for local models
    LLM_API_URL: Optional[str] = Field(default=None)  # API URL for hosted models
    LLM_API_KEY: Optional[str] = Field(default=None)  # API Key for hosted models
    
    # Google Search Settings
    SERP_API_KEY: Optional[str] = Field(default=None)
    GOOGLE_CSE_ID: Optional[str] = Field(default=None)
    GOOGLE_API_KEY: Optional[str] = Field(default=None)
    
    # Web Scraping Settings
    USER_AGENT: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    REQUEST_TIMEOUT: int = Field(default=10)
    
    # Logging Settings
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="<green>{time}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    
    # Memory Settings
    USE_MEMORY: bool = Field(default=True)
    VECTOR_STORE_TYPE: str = Field(default="faiss")  # Options: faiss, pinecone
    PINECONE_API_KEY: Optional[str] = Field(default=None)
    PINECONE_ENVIRONMENT: Optional[str] = Field(default=None)
    
    # Agent Settings
    MAX_ITERATIONS: int = Field(default=5)
    MAX_EXECUTION_TIME: int = Field(default=60)  # in seconds
    
    # Development Settings
    TESTING: bool = Field(default=False)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration based on the selected LLM type."""
        if self.LLM_TYPE == "mistral":
            return {
                "type": "mistral",
                "model_path": self.LLM_MODEL_PATH or os.path.join("models", "mistral-7b-instruct-v0.1.Q4_K_M.gguf"),
                "api_url": self.LLM_API_URL,
                "api_key": self.LLM_API_KEY,
            }
        elif self.LLM_TYPE == "llama":
            return {
                "type": "llama",
                "model_path": self.LLM_MODEL_PATH or os.path.join("models", "llama-2-7b-chat.Q4_K_M.gguf"),
                "api_url": self.LLM_API_URL,
                "api_key": self.LLM_API_KEY,
            }
        elif self.LLM_TYPE == "gpt4all":
            return {
                "type": "gpt4all",
                "model_path": self.LLM_MODEL_PATH or os.path.join("models", "gpt4all-j-v1.3-groovy.bin"),
                "api_url": self.LLM_API_URL,
                "api_key": self.LLM_API_KEY,
            }
        else:
            raise ValueError(f"Unsupported LLM type: {self.LLM_TYPE}")

    def get_search_config(self) -> Dict[str, Any]:
        """Get search configuration."""
        if self.SERP_API_KEY:
            return {
                "type": "serpapi",
                "api_key": self.SERP_API_KEY,
            }
        elif self.GOOGLE_API_KEY and self.GOOGLE_CSE_ID:
            return {
                "type": "google_cse",
                "api_key": self.GOOGLE_API_KEY,
                "cse_id": self.GOOGLE_CSE_ID,
            }
        else:
            raise ValueError("No search API credentials provided")

settings = Settings()