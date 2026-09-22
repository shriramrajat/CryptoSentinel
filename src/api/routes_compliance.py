"""Phase 6 compliance API endpoints."""
from fastapi import APIRouter
from ecdat.compliance import get_summary, get_requirements

router_compliance = APIRouter()

@router_compliance.get("/api/v1/compliance")
def compliance_summary() -> dict:
    """Return deterministic SIH26164 requirement coverage summary."""
    return get_summary()

@router_compliance.get("/api/v1/compliance/requirements")
def compliance_requirements() -> dict:
    """Return full SIH26164 requirement traceability matrix."""
    return {"requirements": get_requirements()}
