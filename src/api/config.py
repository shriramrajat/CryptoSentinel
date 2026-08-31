import os
from dataclasses import dataclass, field

@dataclass
class Settings:
    app_name: str = "CryptoSentinel API"
    version: str = "0.1.0"
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "False").lower() in ("true", "1", "yes"))
    cors_origins: str = field(default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"))

settings = Settings()
