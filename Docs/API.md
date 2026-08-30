# CryptoSentinel API

## Phase 1 — Backend API Foundation

CryptoSentinel exposes the deterministic scanner and risk engine through a small FastAPI transport layer. The API does not perform security classification itself; it delegates discovery to `ecdat.scanner` and risk interpretation to `ecdat.risk`.

### Run locally

```bash
pip install -r requirements.txt
uvicorn api.main:app --app-dir src --reload
```

### Health

`GET /health`

```json
{"status": "ok"}
```

### Version

`GET /version`

```json
{"version": "0.1.0"}
```

### Scan

`POST /api/v1/scan`

Request:

```json
{
  "target_path": "/absolute/path/to/repository",
  "language_filters": ["python", "java"]
}
```

Supported filters: `python`, `java`, `c`, `cpp`, `pem`.

The response contains:

- `summary`: file counts, severity counts, quantum-threat counts, algorithm distribution
- `findings`: canonical crypto asset metadata, evidence, and deterministic risk/PQC assessment
- `errors`: per-file failures that did not abort the scan
- `skipped_files`: files excluded by safety/resource limits
- `metadata`: scan duration and scanner version

### Security boundary

The scanner remains deterministic and rule-backed. The API is only the transport/service boundary for the existing engine. Hardcoded-secret evidence is redacted by the scanner before it reaches the response.
