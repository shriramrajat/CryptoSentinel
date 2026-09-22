export interface ScanRequest {
  target_path: string;
  language_filters?: string[] | null;
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
  severity: "critical" | "high" | "medium" | "low" | "info";
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
}

export interface ScanMetadata {
  scan_duration_ms: number;
  scanner_version: string;
}

export interface ScanResponse {
  summary: ScanSummary;
  findings: Finding[];
  errors: Array<{ file: string; error: string }>;
  skipped_files: Array<{ file: string; reason: string }>;
  metadata: ScanMetadata;
}
