from fastapi import APIRouter, HTTPException
from .schemas import ScanRequest, ErrorResponse
from .config import settings
from ecdat.service import ScanService, ScannerError, AnalysisError

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
    """
    Scan a target path for cryptographic assets.

    - `target_path`: Absolute or relative path to scan.
    - `language_filters`: Optional list of language names to restrict scanning (e.g. ["python", "java"]).
    - `generate_cbom`: If true, include a CycloneDX v1.6 CBOM in the response under the `cbom` key.
    """
    service = ScanService()
    return service.run_scan(
        request.target_path,
        request.language_filters,
        generate_cbom=request.generate_cbom or False,
    )


@router.post(
    "/api/v1/cbom",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid Input"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def cbom_endpoint(request: ScanRequest) -> dict:
    """
    Scan a target path and return ONLY the CycloneDX v1.6 CBOM JSON.
    The full findings payload is not returned — use /api/v1/scan for full results.
    """
    service = ScanService()
    try:
        result = service.run_scan(
            request.target_path,
            request.language_filters,
            generate_cbom=True,
        )
        cbom = result.get("cbom")
        if cbom is None:
            cbom_error = result.get("cbom_error", "CBOM generation failed with no error details.")
            raise HTTPException(status_code=500, detail=f"CBOM generation error: {cbom_error}")
        return cbom
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except (ScannerError, AnalysisError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))
