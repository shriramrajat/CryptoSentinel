# CryptoSentinel Frontend Integration Contract

This document outlines the API contract for the CryptoSentinel backend. Frontend developers must build exclusively against this contract.

## Backend Base URL

**Local Default**: `http://127.0.0.1:8000`

*Note: In production or staging, the base URL must be injected via environment configuration.*

## Endpoints

| Method | Endpoint | Purpose | Success | Errors |
|--------|----------|---------|---------|--------|
| `GET`  | `/health`| System liveness check | `200 OK` | `500 Internal Server Error` |
| `GET`  | `/version`| Get scanner version | `200 OK` | `500 Internal Server Error` |
| `POST` | `/api/v1/scan`| Execute repository crypto scan | `200 OK` | `400 Bad Request`, `500 Internal Server Error` |

---

## Detailed Endpoint Specifications

### 1. Health Check
- **Path**: `/health`
- **Method**: `GET`
- **Purpose**: Verify the backend is online and accepting requests.
- **Success Response** (`200 OK`):
  ```json
  {
    "status": "ok"
  }
  ```

### 2. Version Information
- **Path**: `/version`
- **Method**: `GET`
- **Purpose**: Get the currently deployed scanner and API version.
- **Success Response** (`200 OK`):
  ```json
  {
    "version": "0.1.0"
  }
  ```

### 3. Repository Scan
- **Path**: `/api/v1/scan`
- **Method**: `POST`
- **Purpose**: Instruct the backend to traverse a file path, detect cryptographic assets, and return post-quantum risk assessments.

#### Request Body
```json
{
  "target_path": "/absolute/path/to/repository",
  "language_filters": ["python", "java"]
}
```
*Note: `language_filters` is optional. If omitted or null, all supported languages are scanned.*

#### Success Response (`200 OK`)
The exact structure of the scan response:
```json
{
  "summary": {
    "total_files_discovered": 100,
    "total_files_scanned": 90,
    "files_skipped": 10,
    "files_failed": 0,
    "total_crypto_assets": 5,
    "severity_counts": {
      "critical": 0,
      "high": 1,
      "medium": 3,
      "low": 1,
      "info": 0
    },
    "quantum_threat_counts": {
      "shor": 1,
      "grover": 0,
      "none": 4
    },
    "algorithm_distribution": {
      "RSA": 1,
      "AES": 2,
      "SHA-256": 2
    },
    "quantum_vulnerable_assets": 1
  },
  "findings": [
    {
      "finding_id": "crypto-1234abcd...",
      "algorithm": "RSA",
      "category": "asymmetric_encryption",
      "key_length": 2048,
      "mode": null,
      "padding": null,
      "file_location": {
        "file_path": "src/main.py",
        "line_number": 42
      },
      "evidence": {
        "file_path": "src/main.py",
        "line_number": 42,
        "code_snippet": "RSA.generate(2048)",
        "detection_mechanism": "ast",
        "matched_rule_id": "unknown"
      },
      "risk": {
        "severity": "high",
        "reason": "RSA is vulnerable to Shor's algorithm.",
        "confidence": 0.95,
        "quantum_threat": "shor",
        "pqc_recommendation": {
          "target_algorithm": "ML-KEM",
          "nist_standard": "FIPS 203",
          "migration_type": "drop-in"
        }
      }
    }
  ],
  "errors": [],
  "skipped_files": [],
  "metadata": {
    "scan_duration_ms": 1500,
    "scanner_version": "0.1.0"
  }
}
```
*Note: `key_length`, `mode`, `padding`, and `pqc_recommendation` can be `null`.*

#### Error Responses
- **`400 Bad Request`**: Validation failures (e.g., directory does not exist).
- **`500 Internal Server Error`**: Core engine failures (`ScannerError`, `AnalysisError`) or unhandled exceptions.

---

## TypeScript Request/Response Models

```typescript
export interface ScanRequest {
  target_path: string;
  language_filters?: string[] | null;
}

export interface ErrorDetail {
  code: string; // e.g., "INVALID_INPUT", "SCANNER_FAILURE", "ANALYSIS_FAILURE", "INTERNAL_ERROR"
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

export interface Finding {
  finding_id: string;
  algorithm: string;
  category: string;
  key_length: number | null;
  mode: string | null;
  padding: string | null;
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
```

---

## API Flow

The frontend application must implement the following user interaction flow:

1. **User Action**: The user inputs a target directory path and optionally selects language filters.
2. **API Request**: The frontend issues a `POST /api/v1/scan` request.
3. **Loading State**: The frontend **must** display a loading indicator, as static analysis can be a long-running process depending on repository size.
4. **Success/Error State**: 
    - If `200 OK`: Transition to the results view.
    - If `400` or `500`: Display the `.error.message` from the `ErrorResponse` cleanly to the user.
5. **Result Rendering**: Render the returned `ScanResponse` dynamically.

---

## Frontend Rules

1. **Source of Truth**: The frontend must treat the API response schemas as the definitive source of truth.
2. **No Business Logic**: The frontend **must not** duplicate scanner logic or calculate risk independently. Do not attempt to re-evaluate the risk severities based on algorithms.
3. **Consumption Only**: The frontend must consume backend responses and map them directly to UI components.
4. **Resilience**: The frontend must handle loading, error, and empty states (e.g., zero discoveries) gracefully.
5. **Undocumented Fields**: The frontend must not rely on undocumented fields, as they may be removed in future iterations.

---

## Local Development

To run the backend locally against the frontend, execute the following command in the `CryptoSentinel` repository root:

```bash
python -m uvicorn api.main:app --app-dir src --reload
```

The backend will start at `http://127.0.0.1:8000`. Ensure that your frontend's environment points to this URL during local development.
