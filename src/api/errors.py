from fastapi import Request
from fastapi.responses import JSONResponse
from ecdat.service import AnalysisError, ScannerError

async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"error": {"code": "INVALID_INPUT", "message": str(exc)}}
    )

async def scanner_error_handler(request: Request, exc: ScannerError):
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "SCANNER_FAILURE", "message": "The scanner encountered an internal failure."}}
    )

async def analysis_error_handler(request: Request, exc: AnalysisError):
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "ANALYSIS_FAILURE", "message": "The analysis engine encountered an internal failure."}}
    )

async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected internal server error occurred."}}
    )
