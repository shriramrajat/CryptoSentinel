export interface ScanRequest {
  target_path: string;
  language_filters?: string[] | null;
  user_context_map?: Record<string, any> | null;
  policy_config?: Record<string, any> | null;
}

export interface ErrorDetail {
  code: string;
  message: string;
}

export interface ErrorResponse {
  error: ErrorDetail;
}

export interface PqcRecommendation {
  target_algorithm: string;
  nist_standard: string;
  migration_type: string;
}

export interface RiskAssessment {
  severity: "critical" | "high" | "medium" | "low" | "info" | "unknown";
  reason: string;
  confidence: number;
  quantum_threat: "shor" | "grover" | "none";
  pqc_recommendation: PqcRecommendation | null;
}

export interface Evidence {
  file_path: string;
  line_number: number;
  code_snippet: string;
  detection_mechanism: string;
  matched_rule_id: string;
}

export interface FileLocation {
  file_path: string;
  line_number: number;
}

export interface CertificateMetadata {
  subject?: string | null;
  issuer?: string | null;
  serial_number?: string | null;
  not_before?: string | null;
  not_after?: string | null;
  is_expired?: boolean;
  signature_algorithm?: string | null;
  is_weak_signature?: boolean;
  key_type?: string | null;
  key_size?: number | null;
  is_weak_key?: boolean;
  subject_alt_names?: string[];
}

export interface KeyMetadata {
  key_type?: string | null;
  key_size?: number | null;
  private_material?: string;
}

export interface ContextField<T = any> {
  value: T;
  source: "observed" | "derived" | "user" | "unknown";
  confidence: number;
  notes?: string | null;
}

export interface AssetContext {
  application?: ContextField<string>;
  system?: ContextField<string>;
  environment?: ContextField<string>;
  owner?: ContextField<string>;
  team?: ContextField<string>;
  repository?: ContextField<string>;
  service?: ContextField<string>;
  deployment_type?: ContextField<string>;
  internet_exposed?: ContextField<boolean | null>;
  data_type?: ContextField<string>;
  data_sensitivity?: ContextField<string>;
  data_lifetime_years?: ContextField<number | null>;
  business_criticality?: ContextField<string>;
  operational_criticality?: ContextField<string>;
  external_dependency?: ContextField<boolean | null>;
  compliance_relevance?: ContextField<string[]>;
}

export interface QuantumThreatAssessment {
  threat_type: "shor" | "grover" | "none";
  threat_name: string;
  description: string;
  impact_summary: string;
  security_margin_bits?: number | null;
  quantum_resistant: boolean;
}

export interface HNDLAssessment {
  status: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "NOT_APPLICABLE" | "UNKNOWN";
  is_confidentiality_primitive: boolean;
  is_shor_vulnerable: boolean;
  reasons: string[];
  exposure_summary: string;
}

export interface MoscaLifecycleAssessment {
  urgency: "CRITICAL" | "HIGH" | "MODERATE" | "LOW" | "UNKNOWN";
  data_lifetime_years?: number | null;
  migration_lead_time_years: number;
  quantum_horizon_years: number;
  protection_horizon_years?: number | null;
  safety_margin_years?: number | null;
  formula: string;
  explanation: string;
}

export interface RiskExplanation {
  what: string;
  where: string;
  context_summary: Record<string, any>;
  why_vulnerable: string[];
  why_now: string[];
  missing_information: string[];
  recommendations: string[];
}

export interface QuantumRiskIntelligence {
  asset_id: string;
  technical_quantum_risk: "critical" | "high" | "medium" | "low" | "info" | "unknown";
  quantum_threat: QuantumThreatAssessment;
  hndl_assessment: HNDLAssessment;
  lifecycle_assessment: MoscaLifecycleAssessment;
  context_criticality: string;
  business_urgency: "critical" | "high" | "medium" | "low" | "info" | "unknown";
  overall_priority: "IMMEDIATE_ACTION" | "PLANNING_REQUIRED" | "NEEDS_CONTEXT" | "MONITOR" | "LOW_PRIORITY";
  reasons: string[];
  assumptions: Record<string, any>;
  confidence: number;
  explanation: RiskExplanation;
  pqc_recommendation?: PqcRecommendation | null;
  calculated_at: string;
}

export interface HybridStrategy {
  classical_component: string;
  pqc_component: string;
  combined_public_key_bytes: number;
  combined_ciphertext_or_sig_bytes: number;
  rationale: string;
}

export interface MigrationConstraints {
  key_size_overhead: boolean;
  ciphertext_or_sig_overhead: boolean;
  packet_fragmentation_risk: boolean;
  protocol_compatibility_risk: boolean;
  library_availability_risk: boolean;
  deployment_complexity: string;
  constraint_items: string[];
}

export interface MigrationRecommendation {
  asset_id: string;
  current_algorithm: string;
  current_purpose: string;
  current_library: string;
  recommended_algorithm: string;
  recommended_family: string;
  nist_standard: string;
  migration_type: string;
  hybrid_strategy?: HybridStrategy | null;
  alternative_recommendation?: string | null;
  rationale: string[];
  constraints: MigrationConstraints;
  confidence: number;
  source: string;
  assumptions: Record<string, any>;
}

export interface DimensionScore {
  name: string;
  passed: boolean;
  score: number;
  notes: string;
}

export interface MigrationReadiness {
  state: "READY_FOR_MIGRATION" | "READY_FOR_PLANNING" | "PARTIALLY_READY" | "NOT_READY" | "UNKNOWN";
  overall_score: number;
  discovery_completeness: DimensionScore;
  context_completeness: DimensionScore;
  dependency_library_support: DimensionScore;
  protocol_compatibility: DimensionScore;
  testing_readiness: DimensionScore;
  checklist: string[];
}

export interface RoadmapStep {
  step_number: number;
  title: string;
  description: string;
  estimated_effort: string;
  completed: boolean;
}

export interface MigrationRecord {
  asset_id: string;
  current_state: string;
  last_updated: string;
  history: Array<Record<string, any>>;
  notes?: string | null;
}

export interface MigrationIntelligence {
  recommendation: MigrationRecommendation;
  readiness: MigrationReadiness;
  migration_priority: string;
  lifecycle_record: MigrationRecord;
  roadmap: RoadmapStep[];
}

export interface SimulationResult {
  asset_id: string;
  current_algorithm: string;
  candidate_algorithm: string;
  candidate_pqc_info?: Record<string, any> | null;
  projected_security_posture: string;
  projected_quantum_risk: string;
  key_size_delta_bytes: number;
  ciphertext_or_sig_delta_bytes: number;
  bandwidth_latency_impact: string;
  compatibility_risk: string;
  remaining_uncertainties: string[];
  simulation_disclaimer: string;
}

export interface Finding {
  finding_id: string;
  algorithm: string;
  category: string;
  key_length: number | null;
  mode: string | null;
  padding: string | null;
  purpose?: string | null;
  language?: string | null;
  certificate_metadata?: CertificateMetadata | null;
  key_metadata?: KeyMetadata | null;
  file_location: FileLocation;
  evidence: Evidence;
  risk: RiskAssessment;
  context?: AssetContext;
  quantum_risk_intelligence?: QuantumRiskIntelligence;
  migration_intelligence?: MigrationIntelligence;
}

export interface ScanSummary {
  total_files_discovered: number;
  total_files_scanned: number;
  files_skipped: number;
  files_failed: number;
  total_crypto_assets: number;
  severity_counts: Record<string, number>;
  quantum_threat_counts: Record<string, number>;
  algorithm_distribution: Record<string, number>;
  quantum_vulnerable_assets: number;
  hndl_counts?: Record<string, number>;
  mosca_urgency_counts?: Record<string, number>;
  priority_counts?: Record<string, number>;
  unknown_context_count?: number;
  migration_priority_counts?: Record<string, number>;
  migration_type_counts?: Record<string, number>;
  readiness_state_counts?: Record<string, number>;
}

export interface ScanMetadata {
  scan_duration_ms: number;
  scanner_version: string;
  policy?: Record<string, any>;
  target_path?: string;
}

export interface ScanResponse {
  summary: ScanSummary;
  findings: Finding[];
  errors: Array<{ file: string; error: string }>;
  skipped_files: Array<{ file: string; reason: string }>;
  metadata: ScanMetadata;
  target_path?: string;
  inventory_metadata?: {
    scan_id: string;
    repository_id: string;
    drift_events_count: number;
    alerts_created_count: number;
    total_active_assets: number;
  };
}


export interface Organization {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  business_criticality: string;
  created_at: string;
  updated_at: string;
}

export interface Repository {
  id: string;
  project_id: string;
  name: string;
  provider: string;
  url: string;
  default_branch: string;
  environment: string;
  created_at: string;
  updated_at: string;
}

export interface ScanRecord {
  id: string;
  repository_id: string;
  started_at: string;
  completed_at?: string | null;
  status: "IN_PROGRESS" | "COMPLETED" | "FAILED";
  commit_sha: string;
  branch: string;
  scanner_version: string;
  source_type: string;
  asset_count: number;
  error_count: number;
}

export interface DriftEvent {
  id: string;
  repository_id: string;
  scan_id: string;
  asset_id: string;
  type: "NEW_ASSET" | "REMOVED_ASSET" | "MODIFIED_ASSET" | "RISK_REGRESSION" | "RISK_IMPROVEMENT" | "MIGRATION_PROGRESS" | "MIGRATION_REGRESSION";
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";
  before_state: Record<string, any>;
  after_state: Record<string, any>;
  detected_at: string;
  explanation: string;
}

export interface Alert {
  id: string;
  type: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  scope_type: string;
  scope_id: string;
  repository_id: string;
  asset_id?: string | null;
  message: string;
  created_at: string;
  updated_at: string;
  status: "OPEN" | "ACKNOWLEDGED" | "RESOLVED";
  dedup_key: string;
}

export interface PostureResponse {
  scope: {
    organization_id?: string | null;
    project_id?: string | null;
    repository_id?: string | null;
  };
  totals: {
    total_repositories: number;
    total_scans: number;
    total_crypto_assets: number;
    unique_crypto_assets: number;
    quantum_vulnerable_assets: number;
    hndl_sensitive_assets: number;
    critical_high_priority_assets: number;
  };
  migration_progress: {
    ready_for_migration: number;
    partially_ready: number;
    not_ready: number;
    currently_migrating: number;
    migrated_assets: number;
  };
  distributions: {
    priority_counts: Record<string, number>;
    severity_counts: Record<string, number>;
    hndl_counts: Record<string, number>;
  };
  monitoring: {
    open_drift_events_count: number;
    active_alerts_count: number;
    unresolved_high_risk_alerts_count: number;
  };
}

export interface PostureTrend {
  scan_id: string;
  repository_id: string;
  timestamp: string;
  total_crypto_assets: number;
  quantum_vulnerable_count: number;
  high_priority_count: number;
  migrated_count: number;
}

export interface ScanSchedule {
  id: string;
  repository_id: string;
  enabled: boolean;
  interval_hours: number;
  next_run_at: string;
  last_run_at?: string | null;
  created_at: string;
  updated_at: string;
}
