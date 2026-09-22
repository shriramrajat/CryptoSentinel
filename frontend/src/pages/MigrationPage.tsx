import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useScan } from '../context/ScanContext';
import { SectionHeader } from '../components/common/SectionHeader';
import { Card } from '../components/common/Card';
import { EmptyState } from '../components/common/EmptyState';
import { Button } from '../components/common/Button';
import { QuantumIcon, ShieldIcon, AlertIcon } from '../components/common/Icons';
import { scanApi } from '../api/client';
import type { SimulationResult, RoadmapStep } from '../types/api';

export default function MigrationPage() {
  const { scanResponse, executeScan } = useScan();
  const navigate = useNavigate();
  const [selectedTab, setSelectedTab] = useState<'recommendations' | 'simulator' | 'readiness' | 'roadmap'>('recommendations');
  const [simAssetId, setSimAssetId] = useState<string>('');
  const [simCandidate, setSimCandidate] = useState<string>('ML-DSA-65');
  const [simResult, setSimResult] = useState<SimulationResult | null>(null);
  const [simLoading, setSimLoading] = useState<boolean>(false);
  const [statusUpdating, setStatusUpdating] = useState<string | null>(null);

  const findings = scanResponse?.findings || [];
  const summary = scanResponse?.summary;

  const directCandidates = findings.filter(
    (f) => f.migration_intelligence?.recommendation?.migration_type === 'DIRECT'
  );
  const hybridCandidates = findings.filter(
    (f) => f.migration_intelligence?.recommendation?.migration_type === 'HYBRID' || f.migration_intelligence?.recommendation?.hybrid_strategy !== null
  );
  const readyForMigration = findings.filter(
    (f) => f.migration_intelligence?.readiness?.state === 'READY_FOR_MIGRATION' || f.migration_intelligence?.readiness?.state === 'READY_FOR_PLANNING'
  );

  const handleSimulate = async () => {
    if (!simAssetId && findings.length > 0) {
      setSimAssetId(findings[0].finding_id);
    }
    const targetId = simAssetId || (findings.length > 0 ? findings[0].finding_id : '');
    if (!targetId) return;

    setSimLoading(true);
    try {
      const res = await scanApi.simulateMigration(targetId, simCandidate);
      setSimResult(res.simulation);
    } catch (err) {
      console.error('Simulation error:', err);
    } finally {
      setSimLoading(false);
    }
  };

  const handleStateTransition = async (assetId: string, newState: string) => {
    setStatusUpdating(assetId);
    try {
      await scanApi.updateMigrationStatus(assetId, newState);
      if (executeScan) {
        await executeScan();
      }
    } catch (err: any) {
      alert(`Transition error: ${err.message || 'Invalid state transition'}`);
    } finally {
      setStatusUpdating(null);
    }
  };

  if (!scanResponse) {
    return (
      <div className="space-y-6">
        <SectionHeader
          title="PQC & Hybrid Migration Intelligence"
          subtitle="Deterministic Post-Quantum Cryptography migration recommendations, hybrid strategies, readiness assessments, and What-If simulator."
        />
        <EmptyState
          title="No Migration Intelligence Available"
          description="Execute a scan on the Dashboard to generate PQC migration recommendations and roadmaps for your codebase."
          action={
            <Button variant="primary" size="sm" onClick={() => navigate('/')}>
              Initiate Scan on Dashboard
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <SectionHeader
        title="PQC & Hybrid Migration Intelligence"
        subtitle="Actionable NIST FIPS 203/204/205 migration planning, hybrid strategies, 5-dimensional readiness, and What-If simulator."
        badge={
          <span className="bg-[#00E5FF]/20 text-[#00E5FF] border border-[#00E5FF]/40 text-xs font-mono px-2.5 py-0.5 rounded-full flex items-center gap-1.5">
            <ShieldIcon className="w-3.5 h-3.5" />
            {findings.length} Assets Analyzed
          </span>
        }
      />

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card className="border-[#7C3AED]/30 bg-[#7C3AED]/10 p-3">
          <div className="text-[11px] font-mono text-[#A3ADBF] uppercase">Direct PQC Candidates</div>
          <div className="text-2xl font-bold font-mono text-[#7C3AED] mt-1">{directCandidates.length}</div>
          <div className="text-[10px] text-[#A3ADBF] mt-0.5">ML-KEM / ML-DSA replacement</div>
        </Card>

        <Card className="border-[#00E5FF]/30 bg-[#00E5FF]/10 p-3">
          <div className="text-[11px] font-mono text-[#A3ADBF] uppercase">Hybrid Strategies</div>
          <div className="text-2xl font-bold font-mono text-[#00E5FF] mt-1">{hybridCandidates.length}</div>
          <div className="text-[10px] text-[#A3ADBF] mt-0.5">Dual Classical + PQC transition</div>
        </Card>

        <Card className="border-[#06D6A0]/30 bg-[#06D6A0]/10 p-3">
          <div className="text-[11px] font-mono text-[#A3ADBF] uppercase">Ready for Planning</div>
          <div className="text-2xl font-bold font-mono text-[#06D6A0] mt-1">{readyForMigration.length}</div>
          <div className="text-[10px] text-[#A3ADBF] mt-0.5">Verified discovery &amp; context</div>
        </Card>

        <Card className="border-[#FFD166]/30 bg-[#FFD166]/10 p-3">
          <div className="text-[11px] font-mono text-[#A3ADBF] uppercase">Critical Priority</div>
          <div className="text-2xl font-bold font-mono text-[#FFD166] mt-1">
            {summary?.migration_priority_counts?.CRITICAL || 0}
          </div>
          <div className="text-[10px] text-[#A3ADBF] mt-0.5">Immediate migration priority</div>
        </Card>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-[#232B3D] pb-3 overflow-x-auto">
        <button
          onClick={() => setSelectedTab('recommendations')}
          className={`px-3 py-1.5 text-xs font-medium rounded-lg font-mono transition-colors ${
            selectedTab === 'recommendations'
              ? 'bg-[#7C3AED] text-white'
              : 'bg-[#0F1523] text-[#A3ADBF] hover:text-[#F5F7FA] border border-[#232B3D]'
          }`}
        >
          PQC Recommendations &amp; Hybrid Strategies ({findings.length})
        </button>

        <button
          onClick={() => setSelectedTab('simulator')}
          className={`px-3 py-1.5 text-xs font-medium rounded-lg font-mono transition-colors ${
            selectedTab === 'simulator'
              ? 'bg-[#00E5FF] text-[#070B14]'
              : 'bg-[#0F1523] text-[#A3ADBF] hover:text-[#F5F7FA] border border-[#232B3D]'
          }`}
        >
          What-If Migration Simulator
        </button>

        <button
          onClick={() => setSelectedTab('readiness')}
          className={`px-3 py-1.5 text-xs font-medium rounded-lg font-mono transition-colors ${
            selectedTab === 'readiness'
              ? 'bg-[#06D6A0] text-[#070B14]'
              : 'bg-[#0F1523] text-[#A3ADBF] hover:text-[#F5F7FA] border border-[#232B3D]'
          }`}
        >
          Readiness &amp; Constraints
        </button>

        <button
          onClick={() => setSelectedTab('roadmap')}
          className={`px-3 py-1.5 text-xs font-medium rounded-lg font-mono transition-colors ${
            selectedTab === 'roadmap'
              ? 'bg-[#FFD166] text-[#070B14]'
              : 'bg-[#0F1523] text-[#A3ADBF] hover:text-[#F5F7FA] border border-[#232B3D]'
          }`}
        >
          Migration Roadmap &amp; Lifecycle
        </button>
      </div>

      {/* TAB 1: RECOMMENDATIONS */}
      {selectedTab === 'recommendations' && (
        <div className="grid grid-cols-1 gap-4">
          {findings.map((item) => {
            const mi = item.migration_intelligence;
            const rec = mi?.recommendation;
            const hybrid = rec?.hybrid_strategy;

            return (
              <Card key={item.finding_id} className="hover:border-[#7C3AED]/50 bg-[#0F1523] border border-[#232B3D]">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#232B3D] pb-3 mb-3">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono font-bold text-sm text-[#F5F7FA]">{item.algorithm}</span>
                    <span className="text-xs font-mono text-[#00E5FF]">
                      {item.file_location.file_path}:{item.file_location.line_number}
                    </span>
                    <span className="text-xs font-mono text-[#A3ADBF]">({item.category})</span>
                  </div>

                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-[11px] font-mono px-2 py-0.5 rounded border font-semibold ${
                      mi?.migration_priority === 'CRITICAL' ? 'bg-[#EF476F]/20 text-[#EF476F] border-[#EF476F]/40' :
                      mi?.migration_priority === 'HIGH' ? 'bg-[#FFD166]/20 text-[#FFD166] border-[#FFD166]/40' :
                      'bg-[#232B3D] text-[#A3ADBF] border-[#232B3D]'
                    }`}>
                      Priority: {mi?.migration_priority || 'MEDIUM'}
                    </span>

                    <span className="bg-[#7C3AED]/20 text-[#7C3AED] border border-[#7C3AED]/40 text-xs font-mono px-2.5 py-0.5 rounded">
                      Strategy: {rec?.migration_type || 'DIRECT'}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  {/* Primary Target Recommendation */}
                  <div className="bg-[#070B14] border border-[#7C3AED]/40 p-3 rounded space-y-2">
                    <div className="font-mono text-[11px] text-[#A3ADBF] uppercase tracking-wider font-semibold">
                      Recommended PQC Target Standard
                    </div>
                    <div className="text-sm font-bold font-mono text-[#00FFA3]">
                      {rec?.recommended_algorithm} ({rec?.nist_standard})
                    </div>
                    <p className="text-[#A3ADBF] text-[11px]">
                      {rec?.rationale?.[0] || 'Target PQC replacement standard.'}
                    </p>
                    {rec?.alternative_recommendation && (
                      <div className="text-[11px] text-[#00E5FF] font-mono pt-1">
                        Alternative Fallback: <strong>{rec.alternative_recommendation}</strong>
                      </div>
                    )}
                  </div>

                  {/* Hybrid Strategy (if applicable) */}
                  {hybrid ? (
                    <div className="bg-[#070B14] border border-[#00E5FF]/40 p-3 rounded space-y-2">
                      <div className="font-mono text-[11px] text-[#00E5FF] uppercase tracking-wider font-semibold">
                        Dual Classical + PQC Hybrid Construction
                      </div>
                      <div className="text-xs font-mono text-[#F5F7FA]">
                        Classical: <strong>{hybrid.classical_component}</strong> + PQC: <strong>{hybrid.pqc_component}</strong>
                      </div>
                      <p className="text-[#A3ADBF] text-[11px]">{hybrid.rationale}</p>
                      <div className="text-[10px] font-mono text-[#A3ADBF] pt-1">
                        Combined Key Size: {hybrid.combined_public_key_bytes} B | Combined Sig/Ciphertext: {hybrid.combined_ciphertext_or_sig_bytes} B
                      </div>
                    </div>
                  ) : (
                    <div className="bg-[#070B14] border border-[#232B3D] p-3 rounded space-y-2">
                      <div className="font-mono text-[11px] text-[#A3ADBF] uppercase tracking-wider font-semibold">
                        Migration Constraints &amp; Overhead
                      </div>
                      <ul className="list-disc list-inside text-[#F5F7FA] text-[11px] space-y-1 font-mono">
                        {rec?.constraints?.constraint_items?.slice(0, 2).map((c: string, idx: number) => (
                          <li key={idx}>{c}</li>
                        )) || <li>Standard key and signature parameters apply.</li>}
                      </ul>
                    </div>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* TAB 2: WHAT-IF SIMULATOR */}
      {selectedTab === 'simulator' && (
        <Card className="bg-[#0F1523] border border-[#232B3D] p-5 space-y-5">
          <div className="border-b border-[#232B3D] pb-3">
            <h3 className="text-base font-bold text-[#F5F7FA] font-mono flex items-center gap-2">
              <QuantumIcon className="w-5 h-5 text-[#00E5FF]" />
              What-If Migration Simulator
            </h3>
            <p className="text-xs text-[#A3ADBF] mt-1">
              Select a discovered asset and a candidate PQC algorithm to project security posture changes, key/signature size deltas, packet fragmentation risks, and remaining uncertainties without altering production code.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-mono text-[#A3ADBF] mb-1 uppercase">Target Asset</label>
              <select
                value={simAssetId}
                onChange={(e) => setSimAssetId(e.target.value)}
                className="w-full bg-[#070B14] border border-[#232B3D] text-xs font-mono text-[#F5F7FA] p-2.5 rounded focus:border-[#00E5FF] focus:outline-none"
              >
                <option value="">-- Select Discovered Asset --</option>
                {findings.map((f) => (
                  <option key={f.finding_id} value={f.finding_id}>
                    {f.algorithm} ({f.category}) - {f.file_location.file_path}:{f.file_location.line_number}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-mono text-[#A3ADBF] mb-1 uppercase">Candidate PQC Algorithm</label>
              <select
                value={simCandidate}
                onChange={(e) => setSimCandidate(e.target.value)}
                className="w-full bg-[#070B14] border border-[#232B3D] text-xs font-mono text-[#F5F7FA] p-2.5 rounded focus:border-[#00E5FF] focus:outline-none"
              >
                <option value="ML-DSA-65">ML-DSA-65 (FIPS 204 Digital Signature)</option>
                <option value="ML-KEM-768">ML-KEM-768 (FIPS 203 Key Encapsulation)</option>
                <option value="SLH-DSA-128s">SLH-DSA-SHAKE-128s (FIPS 205 Hash Signature)</option>
                <option value="AES-256-GCM">AES-256-GCM (FIPS 197 Quantum-Safe Symmetric)</option>
              </select>
            </div>

            <div className="flex items-end">
              <Button
                variant="primary"
                size="md"
                className="w-full"
                onClick={handleSimulate}
                disabled={simLoading}
              >
                {simLoading ? 'Simulating...' : 'Run What-If Simulation'}
              </Button>
            </div>
          </div>

          {/* Simulation Output Card */}
          {simResult && (
            <div className="bg-[#070B14] border border-[#00E5FF]/40 p-4 rounded-lg space-y-4 text-xs font-mono">
              <div className="flex items-center justify-between border-b border-[#232B3D] pb-2">
                <span className="text-[#00E5FF] font-bold text-sm">
                  Simulation Output: {simResult.current_algorithm} → {simResult.candidate_algorithm}
                </span>
                <span className="text-[10px] bg-[#00E5FF]/10 text-[#00E5FF] px-2 py-0.5 rounded border border-[#00E5FF]/30">
                  {simResult.simulation_disclaimer}
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-[#0F1523] p-2.5 rounded border border-[#232B3D]">
                  <span className="text-[#A3ADBF] block text-[10px]">Projected Posture</span>
                  <span className="text-[#00FFA3] font-bold">{simResult.projected_security_posture}</span>
                </div>

                <div className="bg-[#0F1523] p-2.5 rounded border border-[#232B3D]">
                  <span className="text-[#A3ADBF] block text-[10px]">Public Key Size Delta</span>
                  <span className="text-[#F5F7FA] font-bold">+{simResult.key_size_delta_bytes} Bytes</span>
                </div>

                <div className="bg-[#0F1523] p-2.5 rounded border border-[#232B3D]">
                  <span className="text-[#A3ADBF] block text-[10px]">Sig/Ciphertext Delta</span>
                  <span className="text-[#F5F7FA] font-bold">+{simResult.ciphertext_or_sig_delta_bytes} Bytes</span>
                </div>

                <div className="bg-[#0F1523] p-2.5 rounded border border-[#232B3D]">
                  <span className="text-[#A3ADBF] block text-[10px]">Bandwidth Impact</span>
                  <span className="text-[#FFD166] font-bold">{simResult.bandwidth_latency_impact}</span>
                </div>
              </div>

              {simResult.remaining_uncertainties.length > 0 && (
                <div className="bg-[#FFD166]/10 border border-[#FFD166]/30 p-3 rounded text-[11px]">
                  <div className="text-[#FFD166] font-bold mb-1 flex items-center gap-1">
                    <AlertIcon className="w-3.5 h-3.5" />
                    Remaining Migration Uncertainties
                  </div>
                  <ul className="list-disc list-inside text-[#A3ADBF] space-y-0.5">
                    {simResult.remaining_uncertainties.map((u: string, idx: number) => (
                      <li key={idx}>{u}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </Card>
      )}

      {/* TAB 3: READINESS & CONSTRAINTS */}
      {selectedTab === 'readiness' && (
        <div className="grid grid-cols-1 gap-4">
          {findings.map((item) => {
            const readiness = item.migration_intelligence?.readiness;

            return (
              <Card key={item.finding_id} className="bg-[#0F1523] border border-[#232B3D]">
                <div className="flex items-center justify-between border-b border-[#232B3D] pb-3 mb-3">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-sm text-[#F5F7FA]">{item.algorithm}</span>
                    <span className="text-xs font-mono text-[#00E5FF]">{item.file_location.file_path}</span>
                  </div>
                  <span className={`text-xs font-mono font-bold px-2.5 py-0.5 rounded border ${
                    readiness?.state === 'READY_FOR_MIGRATION' ? 'bg-[#06D6A0]/20 text-[#06D6A0] border-[#06D6A0]/40' :
                    readiness?.state === 'READY_FOR_PLANNING' ? 'bg-[#00E5FF]/20 text-[#00E5FF] border-[#00E5FF]/40' :
                    'bg-[#FFD166]/20 text-[#FFD166] border-[#FFD166]/40'
                  }`}>
                    State: {readiness?.state || 'PARTIALLY_READY'} ({readiness?.overall_score || 75}%)
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-5 gap-2 text-xs font-mono">
                  {readiness && [
                    readiness.discovery_completeness,
                    readiness.context_completeness,
                    readiness.dependency_library_support,
                    readiness.protocol_compatibility,
                    readiness.testing_readiness,
                  ].map((dim, idx) => (
                    <div key={idx} className="bg-[#070B14] p-2.5 rounded border border-[#232B3D] space-y-1">
                      <div className="text-[10px] text-[#A3ADBF] uppercase truncate">{dim.name}</div>
                      <div className={`font-bold ${dim.passed ? 'text-[#06D6A0]' : 'text-[#EF476F]'}`}>
                        {dim.passed ? 'PASSED' : 'CHECK'} ({int(dim.score * 100)}%)
                      </div>
                      <div className="text-[9px] text-[#A3ADBF] leading-tight line-clamp-2">{dim.notes}</div>
                    </div>
                  ))}
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* TAB 4: ROADMAP & LIFECYCLE STATE SWITCHER */}
      {selectedTab === 'roadmap' && (
        <div className="grid grid-cols-1 gap-4">
          {findings.map((item) => {
            const record = item.migration_intelligence?.lifecycle_record;
            const roadmap = item.migration_intelligence?.roadmap || [];
            const currentState = record?.current_state || 'DISCOVERED';

            return (
              <Card key={item.finding_id} className="bg-[#0F1523] border border-[#232B3D]">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#232B3D] pb-3 mb-3">
                  <div>
                    <span className="font-mono font-bold text-sm text-[#F5F7FA]">{item.algorithm}</span>
                    <span className="text-xs font-mono text-[#00E5FF] ml-2">{item.file_location.file_path}</span>
                  </div>

                  {/* Lifecycle State Controls */}
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-xs font-mono text-[#A3ADBF] mr-1">Lifecycle State:</span>
                    {['DISCOVERED', 'ASSESSED', 'PLANNED', 'READY', 'IN_PROGRESS', 'MIGRATED', 'VERIFIED'].map((st) => (
                      <button
                        key={st}
                        disabled={statusUpdating === item.finding_id}
                        onClick={() => handleStateTransition(item.finding_id, st)}
                        className={`text-[10px] font-mono px-2 py-0.5 rounded border transition-colors ${
                          currentState === st
                            ? 'bg-[#7C3AED] text-white border-[#7C3AED] font-bold'
                            : 'bg-[#070B14] text-[#A3ADBF] hover:text-[#F5F7FA] border-[#232B3D]'
                        }`}
                      >
                        {st}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Step-by-Step Roadmap */}
                <div className="space-y-2 text-xs font-mono">
                  <h4 className="text-[11px] text-[#00E5FF] uppercase tracking-wider font-bold">
                    Actionable Remediation Roadmap Steps
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {roadmap.map((step: RoadmapStep) => (
                      <div
                        key={step.step_number}
                        className={`p-2.5 rounded border text-xs ${
                          step.completed
                            ? 'bg-[#06D6A0]/10 border-[#06D6A0]/40 text-[#F5F7FA]'
                            : 'bg-[#070B14] border-[#232B3D] text-[#A3ADBF]'
                        }`}
                      >
                        <div className="flex items-center justify-between font-bold mb-1">
                          <span>
                            Step {step.step_number}: {step.title}
                          </span>
                          <span className="text-[10px]">{step.completed ? '✔ DONE' : 'PENDING'}</span>
                        </div>
                        <div className="text-[11px] text-[#A3ADBF]">{step.description}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

function int(val: number): number {
  return Math.round(val);
}
