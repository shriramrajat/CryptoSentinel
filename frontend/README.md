# CryptoSentinel Frontend

This is the React frontend application for CryptoSentinel.

## Prerequisites
- Node.js (v18 or higher recommended)
- npm (v9 or higher recommended)

## Installation
```bash
npm install
```

## Development
To start the Vite development server:
```bash
npm run dev
```

To build the production bundle:
```bash
npm run build
```

## Environment Configuration
The frontend communicates with the backend API. The base URL is configured via the `.env` file.
Copy `.env.example` to `.env` if you need to override the default:
```bash
cp .env.example .env
```
The variable used is `VITE_API_BASE_URL`. If not set, it defaults to `http://localhost:8000`.

## Backend Relationship
The frontend depends on the CryptoSentinel FastAPI backend. 
To run the backend locally alongside the frontend, run the following from the repository root:
```bash
python -m uvicorn api.main:app --app-dir src --reload
```

## API Contract
The backend API contract is explicitly defined and frozen. Frontend developers must build against this contract.
The contract documentation is located at:
[`../Docs/FRONTEND.md`](../Docs/FRONTEND.md)

## Deployment Limitation: Local Filesystem Scanning
The current backend API accepts a `target_path` and scans files accessible to its own local filesystem process. A deployed browser frontend cannot provide a user's local filesystem path to a remote backend. The current scanning workflow is suitable for local deployment or demos where the backend has access to the target path. Remote repository ingestion (e.g., GitHub integration or file uploads) is a future product capability.
