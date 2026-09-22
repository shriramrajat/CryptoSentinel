# Phase 5: Advanced Discovery

## Architecture

Phase 5 adds bounded adapters under `src/ecdat/discovery`. Each adapter returns an `AdvancedDiscoveryResult` containing normalized findings, source location, evidence, confidence, detection mechanism, rule ID, metadata, and deterministic identity inputs. `finding_to_asset` is the compatibility boundary to the existing Phase 1 `CryptoAsset` and `Evidence` models; Phase 4 remains the only persistent inventory.

## Adapters

- **Binary:** safely reads ELF and PE files, detecting library references, selected imported symbols, and algorithm strings. Library presence is marked as inferred; symbol evidence is directly observed.
- **Container:** inspects tar/zip OCI-compatible archives and directories by names only. It never runs an image or extracts untrusted content.
- **Dependencies:** supports `requirements.txt`, `pyproject.toml`, `package.json`, Go modules, Maven XML, and lock/manifest text formats. Presence is `DEPENDENCY_PRESENT`; usage is not fabricated.
- **Protocols:** extracts structured TLS, SSH, JWT/JWS/JWE evidence where tokens are present.

## Graph and Git/CI

`CryptoGraph` is a deterministic in-memory relational graph with nodes, deduplicated relationships, neighbor traversal, and serialization. `GitInspector` captures commit metadata and compares baseline/current file changes using argument-array subprocess calls and timeouts. Results expose review events and never automatically block merges.

## Query and copilot

`SecurityQueryEngine` supports an allowlist for RSA, SHA-1, quantum-vulnerable, expired-certificate, migration-state, and recent-discovery intents with pagination. Unsupported or malformed input returns `UNSUPPORTED_QUERY`. `EvidenceCopilot` can translate bounded requests and explain supplied evidence; it cannot execute SQL, mutate inventory, calculate risk, or create assets.

## Security and limits

Inputs are size-bounded, archive members are checked for traversal and member limits, subprocesses use fixed argument arrays and timeouts, and no container or binary is executed. Evidence is retained as metadata/snippets; secrets are not extracted by these adapters. These scanners are conservative and should be treated as untrusted-input processors.

## API surface

- `POST /api/v1/discovery/{binary|container|dependency|protocol}`
- `GET /api/v1/graph`
- `GET /api/v1/query?q=...`
- `POST /api/v1/git/compare`
- `POST /api/v1/copilot/query`
- `POST /api/v1/copilot/explain`

## Tests and limitations

The adapters are designed for deterministic fixture-based tests. Binary parsing is indicator-based rather than a complete ELF/PE loader; container analysis does not inspect compressed file contents; dependency parsing intentionally avoids claiming primitive usage; and graph persistence is deferred until a Phase 6 integration requires it.

## Phase 6 integration contract

Future sources should implement `scan(path) -> AdvancedDiscoveryResult`, preserve `DiscoveryFinding` evidence and confidence, and use `finding_to_asset` only when evidence supports a canonical asset. Integrations for cloud KMS, HSMs, runtime telemetry, SBOM/CBOM correlation, and fleet scanning can register adapters with `DiscoveryRegistry` without changing Phase 1–4 semantics.
