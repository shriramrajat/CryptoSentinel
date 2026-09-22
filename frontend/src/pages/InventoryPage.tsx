import React, { useEffect, useState } from 'react';
import { scanApi } from '../api/client';
import type { Alert, DriftEvent, PostureResponse } from '../types/api';

export const InventoryPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'inventory' | 'posture' | 'drift' | 'alerts'>('inventory');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [inventoryAssets, setInventoryAssets] = useState<any[]>([]);
  const [posture, setPosture] = useState<PostureResponse | null>(null);
  const [driftEvents, setDriftEvents] = useState<DriftEvent[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedAssetDetail, setSelectedAssetDetail] = useState<any | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [invRes, postureRes, driftRes, alertsRes] = await Promise.all([
        scanApi.getInventory(),
        scanApi.getPosture(),
        scanApi.getDriftEvents(),
        scanApi.getAlerts(),
      ]);
      setInventoryAssets(invRes.assets || []);
      setPosture(postureRes);
      setDriftEvents(driftRes.drift_events || []);
      setAlerts(alertsRes.alerts || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load enterprise inventory data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleUpdateAlertStatus = async (alertId: string, newStatus: 'ACKNOWLEDGED' | 'RESOLVED') => {
    try {
      await scanApi.updateAlertStatus(alertId, newStatus);
      const alertsRes = await scanApi.getAlerts();
      setAlerts(alertsRes.alerts || []);
    } catch (err: any) {
      alert(`Failed to update alert: ${err.message}`);
    }
  };

  const handleViewAssetDetail = async (assetId: string) => {
    try {
      const detail = await scanApi.getInventoryAssetDetail(assetId);
      setSelectedAssetDetail(detail);
    } catch (err: any) {
      alert(`Failed to fetch asset detail: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-400 animate-pulse">
        <div className="inline-block w-8 h-8 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mb-4"></div>
        <p>Loading Enterprise Cryptographic Inventory & Posture Intelligence...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-950/40 border border-red-500/30 rounded-xl text-red-200 text-center my-6">
        <h3 className="font-semibold text-lg mb-2">Error Loading Enterprise Inventory</h3>
        <p className="text-sm">{error}</p>
        <button onClick={loadData} className="mt-4 px-4 py-2 bg-red-800/60 hover:bg-red-700/80 rounded-lg text-xs font-semibold text-white transition">
          Retry Loading
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <span className="p-2 bg-gradient-to-br from-indigo-500 to-cyan-500 rounded-lg text-white text-base">🏢</span>
            Enterprise Cryptographic Inventory & Monitoring
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Continuous posture tracking, drift detection, historical asset inventory, and security alert management.
          </p>
        </div>
        <button onClick={loadData} className="mt-4 md:mt-0 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg border border-slate-700 transition flex items-center gap-1.5">
          <span>🔄</span> Refresh Enterprise Inventory
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-800 gap-2">
        <button
          onClick={() => setActiveTab('inventory')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition ${
            activeTab === 'inventory' ? 'border-cyan-500 text-cyan-400 bg-cyan-950/20' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          📋 Active Inventory ({inventoryAssets.length})
        </button>
        <button
          onClick={() => setActiveTab('posture')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition ${
            activeTab === 'posture' ? 'border-indigo-500 text-indigo-400 bg-indigo-950/20' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          📊 Posture & Metrics
        </button>
        <button
          onClick={() => setActiveTab('drift')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition ${
            activeTab === 'drift' ? 'border-amber-500 text-amber-400 bg-amber-950/20' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          🔀 Drift Log ({driftEvents.length})
        </button>
        <button
          onClick={() => setActiveTab('alerts')}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition ${
            activeTab === 'alerts' ? 'border-red-500 text-red-400 bg-red-950/20' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          ⚠️ Alerts & Incidents ({alerts.filter((a) => a.status !== 'RESOLVED').length})
        </button>
      </div>

      {/* Tab Content: Active Inventory */}
      {activeTab === 'inventory' && (
        <div className="space-y-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 overflow-x-auto shadow-sm">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-800/80 text-xs uppercase text-slate-400 font-semibold border-b border-slate-700">
                <tr>
                  <th className="py-3 px-4">Asset ID / Algorithm</th>
                  <th className="py-3 px-4">Repository</th>
                  <th className="py-3 px-4">File Path & Line</th>
                  <th className="py-3 px-4">Priority & Risk</th>
                  <th className="py-3 px-4">Migration State</th>
                  <th className="py-3 px-4">First / Last Seen</th>
                  <th className="py-3 px-4">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {inventoryAssets.map((asset) => (
                  <tr key={asset.asset_id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 font-mono text-xs">
                      <div className="font-semibold text-slate-100">{asset.algorithm} ({asset.key_length || 'N/A'} bits)</div>
                      <div className="text-slate-500 text-[10px]">{asset.asset_id.slice(0, 16)}...</div>
                    </td>
                    <td className="py-3 px-4 text-xs font-medium text-slate-300">
                      {asset.repository_name || asset.repository_id || 'Enterprise Core'}
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-slate-400">
                      {asset.source_path}:{asset.line_number}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-bold uppercase ${
                        asset.overall_priority === 'IMMEDIATE_ACTION' ? 'bg-red-950 text-red-400 border border-red-800/60' :
                        asset.overall_priority === 'PLANNING_REQUIRED' ? 'bg-amber-950 text-amber-400 border border-amber-800/60' :
                        'bg-slate-800 text-slate-300 border border-slate-700'
                      }`}>
                        {asset.overall_priority || 'MONITOR'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-xs">
                      <span className="px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/50 text-[11px] font-medium">
                        {asset.lifecycle_state || 'DISCOVERED'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-[11px] text-slate-400 font-mono">
                      <div>1st: {asset.first_seen ? asset.first_seen.slice(0, 10) : 'N/A'}</div>
                      <div>Last: {asset.last_seen ? asset.last_seen.slice(0, 10) : 'N/A'}</div>
                    </td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => handleViewAssetDetail(asset.asset_id)}
                        className="px-2.5 py-1 bg-cyan-950/60 hover:bg-cyan-900/80 text-cyan-300 border border-cyan-700/60 text-xs font-medium rounded transition"
                      >
                        Inspect History
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab Content: Posture */}
      {activeTab === 'posture' && posture && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl text-center">
              <div className="text-2xl font-extrabold text-slate-100">{posture.totals.total_crypto_assets}</div>
              <div className="text-xs text-slate-400 font-medium uppercase mt-1">Total Cryptographic Assets</div>
            </div>
            <div className="bg-slate-900/80 border border-red-900/40 p-4 rounded-xl text-center">
              <div className="text-2xl font-extrabold text-red-400">{posture.totals.quantum_vulnerable_assets}</div>
              <div className="text-xs text-red-300 font-medium uppercase mt-1">Quantum Vulnerable</div>
            </div>
            <div className="bg-slate-900/80 border border-amber-900/40 p-4 rounded-xl text-center">
              <div className="text-2xl font-extrabold text-amber-400">{posture.totals.hndl_sensitive_assets}</div>
              <div className="text-xs text-amber-300 font-medium uppercase mt-1">HNDL Exposure Risk</div>
            </div>
            <div className="bg-slate-900/80 border border-cyan-900/40 p-4 rounded-xl text-center">
              <div className="text-2xl font-extrabold text-cyan-400">{posture.migration_progress.ready_for_migration + posture.migration_progress.migrated_assets}</div>
              <div className="text-xs text-cyan-300 font-medium uppercase mt-1">PQC Ready / Migrated</div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-slate-900/60 border border-slate-800 p-5 rounded-xl">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4">Overall Risk Priority Distribution</h3>
              <div className="space-y-3">
                {Object.entries(posture.distributions.priority_counts).map(([key, count]) => (
                  <div key={key} className="flex justify-between items-center text-xs">
                    <span className="text-slate-400 font-mono">{key}</span>
                    <span className="font-bold text-slate-200">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 p-5 rounded-xl">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4">Migration Progress Readiness</h3>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-emerald-400 font-medium">Ready For Migration</span>
                  <span className="font-bold text-slate-200">{posture.migration_progress.ready_for_migration}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-cyan-400 font-medium">Partially Ready</span>
                  <span className="font-bold text-slate-200">{posture.migration_progress.partially_ready}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-amber-400 font-medium">Not Ready</span>
                  <span className="font-bold text-slate-200">{posture.migration_progress.not_ready}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-indigo-400 font-medium">Currently Migrating</span>
                  <span className="font-bold text-slate-200">{posture.migration_progress.currently_migrating}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab Content: Drift Log */}
      {activeTab === 'drift' && (
        <div className="space-y-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-slate-200 mb-3">Historical Cryptographic Drift Events</h3>
            {driftEvents.length === 0 ? (
              <p className="text-xs text-slate-500">No cryptographic drift events detected yet across scans.</p>
            ) : (
              <div className="space-y-3">
                {driftEvents.map((evt) => (
                  <div key={evt.id} className="p-3 bg-slate-800/40 border border-slate-700/50 rounded-lg flex justify-between items-start text-xs">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 rounded font-bold uppercase text-[10px] ${
                          evt.type === 'NEW_ASSET' ? 'bg-cyan-950 text-cyan-300 border border-cyan-800' :
                          evt.type === 'REMOVED_ASSET' ? 'bg-slate-800 text-slate-400 border border-slate-700' :
                          evt.type === 'RISK_REGRESSION' ? 'bg-red-950 text-red-300 border border-red-800' :
                          'bg-indigo-950 text-indigo-300 border border-indigo-800'
                        }`}>
                          {evt.type}
                        </span>
                        <span className="font-mono text-slate-400 text-[11px]">{evt.detected_at.slice(0, 19)}</span>
                      </div>
                      <p className="text-slate-300 mt-1">{evt.explanation}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab Content: Alerts */}
      {activeTab === 'alerts' && (
        <div className="space-y-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-slate-200 mb-3">Security Alerts & Incidents</h3>
            {alerts.length === 0 ? (
              <p className="text-xs text-slate-500">No open security alerts or incidents detected.</p>
            ) : (
              <div className="space-y-3">
                {alerts.map((al) => (
                  <div key={al.id} className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          al.severity === 'CRITICAL' ? 'bg-red-950 text-red-300 border border-red-800' :
                          al.severity === 'HIGH' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                          'bg-slate-800 text-slate-300 border border-slate-700'
                        }`}>
                          {al.severity}
                        </span>
                        <span className="text-xs font-semibold text-slate-200">{al.type}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                          al.status === 'OPEN' ? 'bg-red-950/60 text-red-400' :
                          al.status === 'ACKNOWLEDGED' ? 'bg-amber-950/60 text-amber-400' :
                          'bg-emerald-950/60 text-emerald-400'
                        }`}>
                          {al.status}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 mt-1">{al.message}</p>
                    </div>
                    {al.status !== 'RESOLVED' && (
                      <div className="flex items-center gap-2">
                        {al.status === 'OPEN' && (
                          <button
                            onClick={() => handleUpdateAlertStatus(al.id, 'ACKNOWLEDGED')}
                            className="px-2.5 py-1 bg-amber-950/80 hover:bg-amber-900 text-amber-300 border border-amber-800/80 text-xs font-medium rounded transition"
                          >
                            Acknowledge
                          </button>
                        )}
                        <button
                          onClick={() => handleUpdateAlertStatus(al.id, 'RESOLVED')}
                          className="px-2.5 py-1 bg-emerald-950/80 hover:bg-emerald-900 text-emerald-300 border border-emerald-800/80 text-xs font-medium rounded transition"
                        >
                          Resolve
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Asset Detail Drawer / Modal */}
      {selectedAssetDetail && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex justify-end">
          <div className="w-full max-w-2xl bg-slate-900 border-l border-slate-800 h-full p-6 overflow-y-auto space-y-6">
            <div className="flex justify-between items-center pb-4 border-b border-slate-800">
              <h2 className="text-lg font-bold text-slate-100">
                Asset History: {selectedAssetDetail.asset.algorithm} ({selectedAssetDetail.asset.asset_id.slice(0, 12)}...)
              </h2>
              <button onClick={() => setSelectedAssetDetail(null)} className="text-slate-400 hover:text-slate-100 text-sm">
                ✕ Close
              </button>
            </div>

            <div className="bg-slate-800/50 p-4 rounded-xl space-y-2 text-xs">
              <div className="grid grid-cols-2 gap-2">
                <div><span className="text-slate-400">Category:</span> <span className="font-semibold text-slate-200">{selectedAssetDetail.asset.category}</span></div>
                <div><span className="text-slate-400">Purpose:</span> <span className="font-semibold text-slate-200">{selectedAssetDetail.asset.purpose || 'unknown'}</span></div>
                <div><span className="text-slate-400">File Path:</span> <span className="font-mono text-slate-300">{selectedAssetDetail.asset.source_path}:{selectedAssetDetail.asset.line_number}</span></div>
                <div><span className="text-slate-400">First Seen:</span> <span className="font-mono text-slate-300">{selectedAssetDetail.first_seen.slice(0, 19)}</span></div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-slate-200 mb-3">Observation Scan History</h3>
              <div className="space-y-2">
                {selectedAssetDetail.observation_history.map((obs: any) => (
                  <div key={obs.id} className="p-3 bg-slate-800/30 border border-slate-800 rounded-lg text-xs flex justify-between">
                    <div>
                      <div className="font-mono text-slate-400">{obs.observed_at.slice(0, 19)}</div>
                      <div className="text-slate-300 mt-0.5">Priority: {obs.overall_priority} | Risk: {obs.technical_quantum_risk}</div>
                    </div>
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px] font-semibold">{obs.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
