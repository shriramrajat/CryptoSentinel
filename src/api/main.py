from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from ecdat.service import AnalysisError, ScanService, ScannerError

SCANNER_VERSION = "0.1.0"

app = FastAPI(
    title="CryptoSentinel API",
    version=SCANNER_VERSION,
    description="Scan source repositories for cryptographic assets and assess post-quantum migration risk.",
)


class ScanRequest(BaseModel):
    target_path: str
    language_filters: Optional[List[str]] = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict:
    return {"version": SCANNER_VERSION}


@app.post("/api/v1/scan")
def scan_endpoint(request: ScanRequest) -> dict:
    service = ScanService()
    try:
        return service.run_scan(request.target_path, request.language_filters)
    except ValueError as exc:
        return {"error": {"code": "INVALID_INPUT", "message": str(exc)}}
    except ScannerError as exc:
        return {"error": {"code": "SCANNER_FAILURE", "message": str(exc)}}
    except AnalysisError as exc:
        return {"error": {"code": "ANALYSIS_FAILURE", "message": str(exc)}}
    except Exception as exc:
        return {"error": {"code": "INTERNAL_ERROR", "message": f"An unexpected failure occurred: {exc}"}}
