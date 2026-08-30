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
