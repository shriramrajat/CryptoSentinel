from fastapi import FastAPI
from .config import settings
from .routes import router
from .errors import (
    value_error_handler,
    scanner_error_handler,
    analysis_error_handler,
    global_exception_handler,
)
from fastapi.middleware.cors import CORSMiddleware
from ecdat.service import AnalysisError, ScannerError

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Scan source repositories for cryptographic assets and assess post-quantum migration risk.",
)

# Configure CORS
origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)

app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(ScannerError, scanner_error_handler)
app.add_exception_handler(AnalysisError, analysis_error_handler)
app.add_exception_handler(Exception, global_exception_handler)
