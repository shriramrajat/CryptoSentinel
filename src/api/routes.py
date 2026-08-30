from fastapi import APIRouter
from .schemas import ScanRequest, ErrorResponse
from .config import settings
from ecdat.service import ScanService

router = APIRouter()

@router.get("/health")
def health() -> dict:
    return {"status": "ok"}

@router.get("/version")
def version() -> dict:
    return {"version": settings.version}

@router.post(
    "/api/v1/scan",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid Input"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def scan_endpoint(request: ScanRequest) -> dict:
    service = ScanService()
    return service.run_scan(request.target_path, request.language_filters)
