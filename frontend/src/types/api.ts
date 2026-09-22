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
}

export interface ScanMetadata {
  scan_duration_ms: number;
  scanner_version: string;
  policy?: Record<string, any>;
}

export interface ScanResponse {
  summary: ScanSummary;
  findings: Finding[];
  errors: Array<{ file: string; error: string }>;
  skipped_files: Array<{ file: string; reason: string }>;
  metadata: ScanMetadata;
}
