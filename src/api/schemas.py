from typing import List, Optional
from pydantic import BaseModel


class ScanRequest(BaseModel):
    target_path: str
    language_filters: Optional[List[str]] = None
    generate_cbom: Optional[bool] = False


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
