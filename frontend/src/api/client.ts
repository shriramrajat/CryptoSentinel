const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

export async function fetchClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      throw new ApiError(response.status, 'UNKNOWN_ERROR', 'An unknown error occurred while parsing the error response');
    }
    
    throw new ApiError(
      response.status,
      errorData?.error?.code || 'UNKNOWN_ERROR',
      errorData?.error?.message || 'An API error occurred'
    );
  }

  return response.json();
}

import type { ScanRequest, ScanResponse } from '../types/api';

export const scanApi = {
  getHealth: () => fetchClient<{ status: string }>('/health'),
  getVersion: () => fetchClient<{ version: string }>('/version'),
  runScan: (request: ScanRequest) =>
    fetchClient<ScanResponse>('/api/v1/scan', {
      method: 'POST',
      body: JSON.stringify(request),
    }),
  exportCbom: (request: ScanRequest) =>
    fetchClient<Record<string, any>>('/api/v1/cbom', {
      method: 'POST',
      body: JSON.stringify(request),
    }),
  updateContext: (asset_id: string, context: Record<string, any>) =>
    fetchClient<{ status: string; asset_id: string; context: any }>('/api/v1/context', {
      method: 'POST',
      body: JSON.stringify({ asset_id, context }),
    }),
  getAssetContext: (asset_id: string) =>
    fetchClient<{ asset_id: string; context: any }>(`/api/v1/assets/${asset_id}/context`),
  getAssetRisk: (asset_id: string) =>
    fetchClient<any>(`/api/v1/assets/${asset_id}/risk`),
  getRiskSummary: () =>
    fetchClient<any>('/api/v1/risk/summary'),
  getQuantumRisk: () =>
    fetchClient<any>('/api/v1/risk/quantum'),
  getHndlRisk: () =>
    fetchClient<any>('/api/v1/risk/hndl'),
};
