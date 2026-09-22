from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field



class ScanRequest(BaseModel):
    target_path: str
    language_filters: Optional[List[str]] = None
    generate_cbom: Optional[bool] = False
    user_context_map: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Map of asset_id or 'default' to asset context attributes.",
    )
    policy_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Risk policy configuration overrides (quantum_horizon_years, migration_lead_time_years, etc.).",
    )


class ContextUpdateRequest(BaseModel):
    asset_id: str
    context: Dict[str, Any]


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
