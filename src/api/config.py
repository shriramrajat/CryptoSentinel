import os
from dataclasses import dataclass, field

@dataclass
class Settings:
    app_name: str = "CryptoSentinel API"
    version: str = "0.1.0"
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "False").lower() in ("true", "1", "yes"))

settings = Settings()
