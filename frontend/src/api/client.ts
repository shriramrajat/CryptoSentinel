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

import type { ScanRequest, ScanResponse, SimulationResult, PostureResponse, PostureTrend, Alert, ScanSchedule } from '../types/api';

export const scanApi = {
  getHealth: () => fetchClient<{ status: string }>('/health'),
  getVersion: () => fetchClient<{ version: string }>('/version'),
  getLatestScan: () => fetchClient<{ status: string; scan: ScanResponse | null }>('/api/v1/scan/latest'),

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

  // Phase 3 Endpoints
  getAssetMigration: (asset_id: string) =>
    fetchClient<any>(`/api/v1/assets/${asset_id}/migration`),
  getAssetRecommendations: (asset_id: string) =>
    fetchClient<any>(`/api/v1/assets/${asset_id}/recommendations`),
  simulateMigration: (asset_id: string, candidate_algorithm: string) =>
    fetchClient<{ asset_id: string; simulation: SimulationResult }>(`/api/v1/assets/${asset_id}/simulate-migration`, {
      method: 'POST',
      body: JSON.stringify({ candidate_algorithm }),
    }),
  getMigrationSummary: () =>
    fetchClient<any>('/api/v1/migration/summary'),
  getMigrationRoadmap: () =>
    fetchClient<any>('/api/v1/migration/roadmap'),
  updateMigrationStatus: (asset_id: string, new_state: string, notes?: string) =>
    fetchClient<{ status: string; asset_id: string; lifecycle_record: any }>(`/api/v1/assets/${asset_id}/migration-status`, {
      method: 'PATCH',
      body: JSON.stringify({ new_state, notes }),
    }),

  // Phase 4 Endpoints
  getOrganizations: () =>
    fetchClient<{ organizations: any[] }>('/api/v1/organizations'),
  getProjects: (organization_id?: string) =>
    fetchClient<{ projects: any[] }>(`/api/v1/projects${organization_id ? `?organization_id=${organization_id}` : ''}`),
  getRepositories: (project_id?: string) =>
    fetchClient<{ repositories: any[] }>(`/api/v1/repositories${project_id ? `?project_id=${project_id}` : ''}`),
  getInventory: (repository_id?: string) =>
    fetchClient<{ total_assets: number; assets: any[] }>(`/api/v1/inventory${repository_id ? `?repository_id=${repository_id}` : ''}`),
  getInventoryAssetDetail: (asset_id: string) =>
    fetchClient<any>(`/api/v1/inventory/assets/${asset_id}`),
  getDriftEvents: (repository_id?: string) =>
    fetchClient<{ total_drift_events: number; drift_events: any[] }>(`/api/v1/drift${repository_id ? `?repository_id=${repository_id}` : ''}`),
  getPosture: (repository_id?: string) =>
    fetchClient<PostureResponse>(`/api/v1/posture${repository_id ? `/repository/${repository_id}` : ''}`),
  getPostureTrends: (repository_id?: string) =>
    fetchClient<{ trends: PostureTrend[] }>(`/api/v1/posture/trends${repository_id ? `?repository_id=${repository_id}` : ''}`),
  getAlerts: (repository_id?: string, status?: string, severity?: string) => {
    const params = new URLSearchParams();
    if (repository_id) params.append('repository_id', repository_id);
    if (status) params.append('status', status);
    if (severity) params.append('severity', severity);
    const query = params.toString();
    return fetchClient<{ total_alerts: number; alerts: Alert[] }>(`/api/v1/alerts${query ? `?${query}` : ''}`);
  },
  updateAlertStatus: (alert_id: string, status: string) =>
    fetchClient<{ status: string; alert: Alert }>(`/api/v1/alerts/${alert_id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),
  getSchedules: (repository_id?: string) =>
    fetchClient<{ schedules: ScanSchedule[] }>(`/api/v1/schedules${repository_id ? `?repository_id=${repository_id}` : ''}`),
};
