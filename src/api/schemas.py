from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict



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


class SimulationRequest(BaseModel):
    candidate_algorithm: str = Field(..., description="Target candidate PQC algorithm (e.g. 'ML-DSA-65', 'ML-KEM-768', 'AES-256-GCM').")


class LifecycleUpdateRequest(BaseModel):
    new_state: str = Field(..., description="Target lifecycle state (DISCOVERED, ASSESSED, PLANNED, READY, IN_PROGRESS, MIGRATED, VERIFIED).")
    notes: Optional[str] = None


class OrganizationCreateRequest(BaseModel):
    name: str = Field(..., description="Enterprise organization name.")


class ProjectCreateRequest(BaseModel):
    organization_id: str = Field(..., description="Parent organization ID.")
    name: str = Field(..., description="Project name.")
    description: Optional[str] = None
    business_criticality: Optional[str] = "high"


class RepositoryCreateRequest(BaseModel):
    project_id: str = Field(..., description="Parent project ID.")
    name: str = Field(..., description="Repository name.")
    provider: Optional[str] = "git"
    url: Optional[str] = ""
    default_branch: Optional[str] = "main"
    environment: Optional[str] = "production"


class AlertPatchRequest(BaseModel):
    status: str = Field(..., description="Target alert status: 'ACKNOWLEDGED' or 'RESOLVED'.")


class ScheduleCreateRequest(BaseModel):
    repository_id: str = Field(..., description="Target repository ID.")
    enabled: Optional[bool] = True
    interval_hours: Optional[int] = 24


class SchedulePatchRequest(BaseModel):
    enabled: Optional[bool] = None
    interval_hours: Optional[int] = None


class AdvancedDiscoveryRequest(BaseModel):
    path: str
    repo_id: Optional[str] = None
    repo_name: str = "default-repo"
    org_id: str = "default-org"
    project_id: str = "default-project"


class GitCompareRequest(BaseModel):
    repository: str
    baseline: str = "HEAD~1"
    current: str = "HEAD"


class CopilotQueryRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=300)


class CopilotEvidenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asset_id: Optional[str] = Field(default=None, max_length=128)
    algorithm: Optional[str] = Field(default=None, max_length=128)
    evidence: Optional[str] = Field(default=None, max_length=4000)
    context: Optional[Dict[str, Any]] = None


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
