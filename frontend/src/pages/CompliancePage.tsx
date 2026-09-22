import React, { useEffect, useState } from 'react';
import { ShieldIcon } from '../components/common/Icons';
import { fetchClient } from '../api/client';

interface Requirement {
  id: string;
  title: string;
  description: string;
  status: 'IMPLEMENTED' | 'PARTIALLY_IMPLEMENTED' | 'NOT_IMPLEMENTED';
  phase: string;
  module: string;
  api: string;
  test: string;
  limitations: string;
}

interface Summary {
  total: number;
  implemented: number;
  partially_implemented: number;
  not_implemented: number;
}

export const CompliancePage: React.FC = () => {
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [filter, setFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchComplianceData();
  }, []);

  const fetchComplianceData = async () => {
    try {
      setLoading(true);
      const data = await fetchClient<{
        requirements: Requirement[];
        summary?: Summary;
      }>('/api/v1/compliance/requirements');
      setRequirements(data.requirements || []);
      setSummary(data.summary || null);
    } catch (err: any) {
      setError(err.message || 'Failed to load compliance matrix');
    } finally {
      setLoading(false);
    }
  };


  const filtered = requirements.filter((r) => {
    if (filter === 'IMPLEMENTED') return r.status === 'IMPLEMENTED';
    if (filter === 'PARTIALLY_IMPLEMENTED') return r.status === 'PARTIALLY_IMPLEMENTED';
    if (filter === 'NOT_IMPLEMENTED') return r.status === 'NOT_IMPLEMENTED';
    return true;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'IMPLEMENTED':
        return (
          <span className="px-2.5 py-1 text-xs font-mono font-semibold rounded-full bg-[#00FFA3]/10 text-[#00FFA3] border border-[#00FFA3]/30">
            ✓ IMPLEMENTED
          </span>
        );
      case 'PARTIALLY_IMPLEMENTED':
        return (
          <span className="px-2.5 py-1 text-xs font-mono font-semibold rounded-full bg-[#FF8A00]/10 text-[#FF8A00] border border-[#FF8A00]/30">
            ⚠️ PARTIAL
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 text-xs font-mono font-semibold rounded-full bg-[#FF4D4D]/10 text-[#FF4D4D] border border-[#FF4D4D]/30">
            ✕ NOT IMPLEMENTED
          </span>
        );
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between border-b border-[#232B3D] pb-6 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <ShieldIcon className="w-8 h-8 text-[#00E5FF]" />
            <h1 className="text-2xl font-bold text-[#F5F7FA]">SIH26164 Compliance Matrix</h1>
          </div>
          <p className="text-sm text-[#A3ADBF] mt-1">
            Requirement Traceability & Hardware/Cloud Evidence Hardening Engine
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono px-3 py-1.5 rounded-md bg-[#171E2E] text-[#00E5FF] border border-[#00E5FF]/30">
            Phase 6 Compliance Engine
          </span>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-lg bg-[#FF4D4D]/10 border border-[#FF4D4D]/30 text-[#FF4D4D] text-sm">
          Error loading compliance engine: {error}
        </div>
      )}

      {/* Summary Stat Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-[#171E2E] border border-[#232B3D] rounded-xl p-4">
            <div className="text-xs text-[#A3ADBF]">Total Requirements</div>
            <div className="text-2xl font-bold text-[#F5F7FA] mt-1">{summary.total}</div>
            <div className="text-[11px] text-[#00E5FF] mt-1 font-mono">SIH26164 Scope</div>
          </div>
          <div className="bg-[#171E2E] border border-[#232B3D] rounded-xl p-4">
            <div className="text-xs text-[#A3ADBF]">Fully Implemented</div>
            <div className="text-2xl font-bold text-[#00FFA3] mt-1">{summary.implemented}</div>
            <div className="text-[11px] text-[#00FFA3]/80 mt-1 font-mono">Verified in Code</div>
          </div>
          <div className="bg-[#171E2E] border border-[#232B3D] rounded-xl p-4">
            <div className="text-xs text-[#A3ADBF]">Partially Implemented</div>
            <div className="text-2xl font-bold text-[#FF8A00] mt-1">{summary.partially_implemented}</div>
            <div className="text-[11px] text-[#FF8A00]/80 mt-1 font-mono">Static Ref / Standard</div>
          </div>
          <div className="bg-[#171E2E] border border-[#232B3D] rounded-xl p-4">
            <div className="text-xs text-[#A3ADBF]">Not Implemented</div>
            <div className="text-2xl font-bold text-[#FF4D4D] mt-1">{summary.not_implemented}</div>
            <div className="text-[11px] text-[#A3ADBF] mt-1 font-mono">Out of Scope</div>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-[#232B3D] pb-3">
        {['ALL', 'IMPLEMENTED', 'PARTIALLY_IMPLEMENTED', 'NOT_IMPLEMENTED'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              filter === f
                ? 'bg-[#00E5FF]/10 text-[#00E5FF] border border-[#00E5FF]/40'
                : 'text-[#A3ADBF] hover:text-[#F5F7FA] hover:bg-[#171E2E]'
            }`}
          >
            {f.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Requirements Grid */}
      {loading ? (
        <div className="text-center py-12 text-[#A3ADBF] font-mono text-sm">
          Loading SIH26164 requirement matrix...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((req) => (
            <div
              key={req.id}
              className="bg-[#171E2E] border border-[#232B3D] hover:border-[#00E5FF]/30 transition-all rounded-xl p-5 space-y-3"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <span className="text-xs font-mono font-bold text-[#00E5FF] bg-[#00E5FF]/10 px-2 py-0.5 rounded">
                    {req.id}
                  </span>
                  <h3 className="text-base font-semibold text-[#F5F7FA] mt-1">{req.title}</h3>
                </div>
                {getStatusBadge(req.status)}
              </div>

              <p className="text-xs text-[#A3ADBF] leading-relaxed">{req.description}</p>

              <div className="grid grid-cols-2 gap-2 text-[11px] pt-2 border-t border-[#232B3D]">
                <div>
                  <span className="text-[#A3ADBF]">Phase: </span>
                  <span className="text-[#F5F7FA] font-mono">{req.phase}</span>
                </div>
                <div>
                  <span className="text-[#A3ADBF]">Module: </span>
                  <span className="text-[#F5F7FA] font-mono">{req.module}</span>
                </div>
                <div>
                  <span className="text-[#A3ADBF]">Primary API: </span>
                  <span className="text-[#00E5FF] font-mono">{req.api}</span>
                </div>
                <div>
                  <span className="text-[#A3ADBF]">Test File: </span>
                  <span className="text-[#00FFA3] font-mono">{req.test}</span>
                </div>
              </div>

              {req.limitations && (
                <div className="bg-[#0F1523] p-2.5 rounded-lg border border-[#232B3D] text-[11px]">
                  <span className="text-[#FF8A00] font-semibold">Boundary/Limitation: </span>
                  <span className="text-[#A3ADBF]">{req.limitations}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CompliancePage;
