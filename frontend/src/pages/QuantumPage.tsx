import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useScan } from '../context/ScanContext';
import { SectionHeader } from '../components/common/SectionHeader';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';
import { Button } from '../components/common/Button';
import { QuantumIcon, CheckIcon, ShieldIcon, AlertIcon } from '../components/common/Icons';

export default function QuantumPage() {
  const { scanResponse } = useScan();
  const navigate = useNavigate();
  const [selectedTab, setSelectedTab] = useState<'all' | 'hndl' | 'mosca' | 'needs_context'>('all');
  const [expandedAssetId, setExpandedAssetId] = useState<string | null>(null);

  const findings = scanResponse?.findings || [];
  const summary = scanResponse?.summary;

  const shorFindings = findings.filter(
    (f) => f.risk.quantum_threat.toLowerCase() === 'shor' || f.quantum_risk_intelligence?.quantum_threat.threat_type === 'shor'
  );
  const groverFindings = findings.filter(
    (f) => f.risk.quantum_threat.toLowerCase() === 'grover' || f.quantum_risk_intelligence?.quantum_threat.threat_type === 'grover'
  );
  const totalQuantumVulnerable = shorFindings.length + groverFindings.length;

  const hndlCandidates = findings.filter((f) => {
    const status = f.quantum_risk_intelligence?.hndl_assessment?.status;
    return status === 'CRITICAL' || status === 'HIGH' || status === 'MEDIUM' || status === 'UNKNOWN';
  });

  const moscaUrgent = findings.filter((f) => {
    const urgency = f.quantum_risk_intelligence?.lifecycle_assessment?.urgency;
    return urgency === 'CRITICAL' || urgency === 'HIGH';
  });

  const needsContext = findings.filter((f) => {
    const missing = f.quantum_risk_intelligence?.explanation?.missing_information || [];
    return missing.length > 0;
  });

  if (!scanResponse) {
    return (
      <div className="space-y-6">
        <SectionHeader
          title="Post-Quantum Cryptography & Contextual Risk Intelligence"
          subtitle="Evaluation of cryptographic assets against quantum algorithms (Shor's & Grover's), HNDL exposure, and Mosca lifecycle urgency."
        />
        <EmptyState
          title="No Quantum Risk Intelligence Assessment Available"
          description="Execute a scan on the Dashboard to assess your codebase for quantum-vulnerable algorithms and lifecycle risks."
          action={
            <Button variant="primary" size="sm" onClick={() => navigate('/')}>
              Initiate Scan on Dashboard
            </Button>
          }
        />
      </div>
    );
  }

  const displayedFindings = findings.filter((f) => {
    if (selectedTab === 'hndl') {
      const s = f.quantum_risk_intelligence?.hndl_assessment?.status;
      return s === 'CRITICAL' || s === 'HIGH' || s === 'MEDIUM' || s === 'UNKNOWN';
    }
    if (selectedTab === 'mosca') {
      const u = f.quantum_risk_intelligence?.lifecycle_assessment?.urgency;
      return u === 'CRITICAL' || u === 'HIGH';
    }
    if (selectedTab === 'needs_context') {
      const m = f.quantum_risk_intelligence?.explanation?.missing_information || [];
      return m.length > 0;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Post-Quantum Cryptography & Contextual Risk Intelligence"
        subtitle="Multi-dimensional risk engine evaluating Shor's/Grover's algorithms, HNDL harvesting threat, and Mosca (C+M>Y) lifecycle urgency."
        badge={
          <span className="bg-[#7C3AED]/20 text-[#7C3AED] border border-[#7C3AED]/40 text-xs font-mono px-2.5 py-0.5 rounded-full flex items-center gap-1.5">
            <QuantumIcon className="w-3.5 h-3.5" />
            {totalQuantumVulnerable} Quantum Vulnerable
          </span>
        }
      />

      {/* Summary KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <Card className="border-[#8B5CF6]/30 bg-[#8B5CF6]/10 p-3">
          <div className="text-[11px] font-mono text-[#A3ADBF] uppercase">Shor Vulnerable</div>
          <div className="text-2xl font-bold font-mono text-[#8B5CF6] mt-1">{shorFindings.length}</div>
          <div className="text-[10px] text-[#A3ADBF] mt-0.5">RSA, ECC, ECDSA, ECDH</div>
        </Card>

        <Card className="border-[#06D6A0]/30 bg-[#06D6A0]/10 p-3">
          <div className="text-[11px] font-mono text-[#A3ADBF] uppercase">Grover Relevant</div>
          <div className="text-2xl font-bold font-mono text-[#06D6A0] mt-1">{groverFindings.length}</div>
          <div className="text-[10px] text-[#A3ADBF] mt-0.5">AES key size &lt; 256</div>
        </Card>

        <Card className="border-[#FFD166]/30 bg-[#FFD166]/10 p-3">
          <div className="text-[11px] font-mono text-[#A3ADBF] uppercase">HNDL Candidates</div>
          <div className="text-2xl font-bold font-mono text-[#FFD166] mt-1">
            {summary?.hndl_counts?.CRITICAL ? summary.hndl_counts.CRITICAL + (summary.hndl_counts.HIGH || 0) : hndlCandidates.length}
          </div>
          <div className="text-[10px] text-[#A3ADBF] mt-0.5">Harvest-Now-Decrypt-Later</div>
        </Card>

        <Card className="border-[#EF476F]/30 bg-[#EF476F]/10 p-3">
          <div className="text-[11px] font-mono text-[#A3ADBF] uppercase">Mosca Urgency</div>
          <div className="text-2xl font-bold font-mono text-[#EF476F] mt-1">
            {summary?.mosca_urgency_counts?.CRITICAL ? summary.mosca_urgency_counts.CRITICAL + (summary.mosca_urgency_counts.HIGH || 0) : moscaUrgent.length}
          </div>
          <div className="text-[10px] text-[#A3ADBF] mt-0.5">C + M &gt; Y Horizon</div>
        </Card>

        <Card className="border-[#00E5FF]/30 bg-[#00E5FF]/10 p-3 col-span-2 md:col-span-1">
          <div className="text-[11px] font-mono text-[#A3ADBF] uppercase">Needs Context</div>
          <div className="text-2xl font-bold font-mono text-[#00E5FF] mt-1">
            {summary?.unknown_context_count !== undefined ? summary.unknown_context_count : needsContext.length}
          </div>
          <div className="text-[10px] text-[#A3ADBF] mt-0.5">Unknown parameters</div>
        </Card>
      </div>

      {/* Quantum Threat Concept Overview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Shor Threat Card */}
        <Card className="border-[#8B5CF6]/40 bg-[#8B5CF6]/10">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded bg-[#8B5CF6]/20 text-[#8B5CF6] border border-[#8B5CF6]/40">
                <QuantumIcon className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-[#F5F7FA] text-sm">Shor's Algorithm Threat</h3>
            </div>
            <span className="bg-[#8B5CF6] text-white text-xs font-mono font-bold px-2 py-0.5 rounded">
              {shorFindings.length} Assets
            </span>
          </div>
          <p className="text-xs text-[#F5F7FA] leading-relaxed mb-3">
            Shor's algorithm efficiently solves prime factorization and discrete logarithms in polynomial time, completely breaking RSA, ECC, ECDSA, ECDH, and Diffie-Hellman asymmetric primitives.
          </p>
          <div className="bg-[#070B14] border border-[#8B5CF6]/40 p-2.5 rounded-lg text-xs font-mono text-[#8B5CF6] space-y-1">
            <div>Target Standard: <strong>FIPS 203 (ML-KEM)</strong> / <strong>FIPS 204 (ML-DSA)</strong></div>
            <div className="text-[11px] text-[#A3ADBF] font-sans">Action: Direct replacement with Module-Lattice quantum-safe primitives.</div>
          </div>
        </Card>

        {/* Grover Threat Card */}
        <Card className="border-[#06D6A0]/40 bg-[#06D6A0]/10">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded bg-[#06D6A0]/20 text-[#06D6A0] border border-[#06D6A0]/40">
                <ShieldIcon className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-[#F5F7FA] text-sm">Grover's Algorithm Threat</h3>
            </div>
            <span className="bg-[#06D6A0] text-[#070B14] text-xs font-mono font-bold px-2 py-0.5 rounded">
              {groverFindings.length} Assets
            </span>
          </div>
          <p className="text-xs text-[#F5F7FA] leading-relaxed mb-3">
            Grover's algorithm provides a quadratic search speedup, halving effective symmetric key bits (e.g. AES-128 offers 64 bits of security under Grover attack).
          </p>
          <div className="bg-[#070B14] border border-[#06D6A0]/40 p-2.5 rounded-lg text-xs font-mono text-[#06D6A0] space-y-1">
            <div>Target Standard: <strong>FIPS 197 (AES-256-GCM)</strong></div>
            <div className="text-[11px] text-[#A3ADBF] font-sans">Action: Upgrade key length to 256 bits and use authenticated mode.</div>
          </div>
        </Card>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-[#232B3D] pb-3">
        <button
          onClick={() => setSelectedTab('all')}
          className={`px-3 py-1.5 text-xs font-medium rounded-lg font-mono transition-colors ${
            selectedTab === 'all'
              ? 'bg-[#7C3AED] text-white'
              : 'bg-[#0F1523] text-[#A3ADBF] hover:text-[#F5F7FA] border border-[#232B3D]'
          }`}
        >
          All Assets ({findings.length})
        </button>
        <button
          onClick={() => setSelectedTab('hndl')}
          className={`px-3 py-1.5 text-xs font-medium rounded-lg font-mono transition-colors ${
            selectedTab === 'hndl'
              ? 'bg-[#FFD166] text-[#070B14]'
              : 'bg-[#0F1523] text-[#A3ADBF] hover:text-[#F5F7FA] border border-[#232B3D]'
          }`}
        >
          HNDL Candidates ({hndlCandidates.length})
        </button>
        <button
          onClick={() => setSelectedTab('mosca')}
          className={`px-3 py-1.5 text-xs font-medium rounded-lg font-mono transition-colors ${
            selectedTab === 'mosca'
              ? 'bg-[#EF476F] text-white'
              : 'bg-[#0F1523] text-[#A3ADBF] hover:text-[#F5F7FA] border border-[#232B3D]'
          }`}
        >
          Mosca Urgency ({moscaUrgent.length})
        </button>
        <button
          onClick={() => setSelectedTab('needs_context')}
          className={`px-3 py-1.5 text-xs font-medium rounded-lg font-mono transition-colors ${
            selectedTab === 'needs_context'
              ? 'bg-[#00E5FF] text-[#070B14]'
              : 'bg-[#0F1523] text-[#A3ADBF] hover:text-[#F5F7FA] border border-[#232B3D]'
          }`}
        >
          Needs Context ({needsContext.length})
        </button>
      </div>

      {/* Findings Remediation List */}
      {displayedFindings.length === 0 ? (
        <Card className="border-[#10B981]/40 bg-[#10B981]/10 text-center py-8">
          <div className="w-12 h-12 rounded-full bg-[#10B981]/20 border border-[#10B981]/40 flex items-center justify-center text-[#10B981] mx-auto mb-3">
            <CheckIcon className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-[#F5F7FA] mb-1">No Assets Match Selected Filter</h3>
          <p className="text-xs text-[#A3ADBF] max-w-md mx-auto">
            All cryptographic assets evaluated in this scan pass the selected filter criteria.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {displayedFindings.map((item) => {
            const qri = item.quantum_risk_intelligence;
            const hndl = qri?.hndl_assessment;
            const mosca = qri?.lifecycle_assessment;
            const isExpanded = expandedAssetId === item.finding_id;

            return (
              <Card key={item.finding_id} className="hover:border-[#7C3AED]/50 bg-[#0F1523] border border-[#232B3D]">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#232B3D] pb-3 mb-3">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="severity" severity={item.risk.severity as any}>
                      {item.risk.severity}
                    </Badge>
                    <span className="font-mono font-bold text-sm text-[#F5F7FA]">{item.algorithm}</span>
                    <span className="text-xs font-mono text-[#00E5FF]">
                      {item.file_location.file_path}:{item.file_location.line_number}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 flex-wrap">
                    {hndl && hndl.status !== 'NOT_APPLICABLE' && (
                      <span className={`text-[11px] font-mono px-2 py-0.5 rounded border font-semibold ${
                        hndl.status === 'CRITICAL' ? 'bg-[#EF476F]/20 text-[#EF476F] border-[#EF476F]/40' :
                        hndl.status === 'HIGH' ? 'bg-[#FFD166]/20 text-[#FFD166] border-[#FFD166]/40' :
                        'bg-[#232B3D] text-[#A3ADBF] border-[#232B3D]'
                      }`}>
                        HNDL: {hndl.status}
                      </span>
                    )}

                    {mosca && mosca.urgency !== 'UNKNOWN' && (
                      <span className={`text-[11px] font-mono px-2 py-0.5 rounded border font-semibold ${
                        mosca.urgency === 'CRITICAL' ? 'bg-[#EF476F]/20 text-[#EF476F] border-[#EF476F]/40' :
                        mosca.urgency === 'HIGH' ? 'bg-[#FFD166]/20 text-[#FFD166] border-[#FFD166]/40' :
                        'bg-[#232B3D] text-[#A3ADBF] border-[#232B3D]'
                      }`}>
                        Mosca: {mosca.urgency}
                      </span>
                    )}

                    <Badge variant="quantum" quantumThreat={item.risk.quantum_threat as any}>
                      {item.risk.quantum_threat.toUpperCase()} THREAT
                    </Badge>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="text-[#A3ADBF] block text-[11px] font-semibold mb-1 uppercase tracking-wider">
                      Technical &amp; Quantum Threat Reason
                    </span>
                    <p className="text-[#F5F7FA] bg-[#070B14] border border-[#232B3D] p-2.5 rounded">
                      {qri?.explanation?.why_vulnerable?.[0] || item.risk.reason}
                    </p>
                  </div>

                  <div>
                    <span className="text-[#A3ADBF] block text-[11px] font-semibold mb-1 uppercase tracking-wider">
                      NIST PQC Migration Target
                    </span>
                    {item.risk.pqc_recommendation ? (
                      <div className="bg-[#7C3AED]/15 border border-[#7C3AED]/40 p-2.5 rounded font-mono text-[#7C3AED] space-y-1">
                        <div>
                          Target: <strong className="text-[#00FFA3]">{item.risk.pqc_recommendation.target_algorithm}</strong> ({item.risk.pqc_recommendation.nist_standard})
                        </div>
                        <div className="text-[11px] text-[#A3ADBF] font-sans">
                          Strategy: {item.risk.pqc_recommendation.migration_type}
                        </div>
                      </div>
                    ) : (
                      <div className="bg-[#070B14] border border-[#232B3D] p-2.5 rounded text-[#A3ADBF]">
                        Upgrade key size / migration parameters.
                      </div>
                    )}
                  </div>
                </div>

                {/* Expandable Context & Explainability Drawer */}
                <div className="mt-3 pt-3 border-t border-[#232B3D] flex items-center justify-between">
                  <button
                    onClick={() => setExpandedAssetId(isExpanded ? null : item.finding_id)}
                    className="text-xs font-mono text-[#00E5FF] hover:underline flex items-center gap-1"
                  >
                    {isExpanded ? 'Hide Context & Risk Intelligence ▲' : 'View Context & Risk Intelligence ▼'}
                  </button>

                  {qri?.explanation?.missing_information && qri.explanation.missing_information.length > 0 && (
                    <span className="text-[11px] text-[#FFD166] flex items-center gap-1 font-mono">
                      <AlertIcon className="w-3.5 h-3.5" />
                      {qri.explanation.missing_information.length} Context Fields Unknown
                    </span>
                  )}
                </div>

                {isExpanded && (
                  <div className="mt-3 p-3 bg-[#070B14] border border-[#232B3D] rounded-lg text-xs space-y-4">
                    {/* Active Asset Context Grid */}
                    <div>
                      <h4 className="font-mono text-xs font-bold text-[#00E5FF] uppercase tracking-wider mb-2">
                        Active Asset Context (Fact / Derived / User / Unknown)
                      </h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[11px] font-mono">
                        <div className="bg-[#0F1523] p-2 rounded border border-[#232B3D]">
                          <span className="text-[#A3ADBF] block text-[10px]">Data Sensitivity</span>
                          <span className="text-[#F5F7FA] font-bold">
                            {item.context?.data_sensitivity?.value || 'UNKNOWN'}
                          </span>
                          <span className="text-[9px] text-[#A3ADBF] block">
                            [{item.context?.data_sensitivity?.source || 'unknown'}]
                          </span>
                        </div>

                        <div className="bg-[#0F1523] p-2 rounded border border-[#232B3D]">
                          <span className="text-[#A3ADBF] block text-[10px]">Data Lifetime (C)</span>
                          <span className="text-[#F5F7FA] font-bold">
                            {item.context?.data_lifetime_years?.value !== undefined && item.context?.data_lifetime_years?.value !== null
                              ? `${item.context.data_lifetime_years.value} yrs`
                              : 'UNKNOWN'}
                          </span>
                          <span className="text-[9px] text-[#A3ADBF] block">
                            [{item.context?.data_lifetime_years?.source || 'unknown'}]
                          </span>
                        </div>

                        <div className="bg-[#0F1523] p-2 rounded border border-[#232B3D]">
                          <span className="text-[#A3ADBF] block text-[10px]">Internet Exposed</span>
                          <span className="text-[#F5F7FA] font-bold">
                            {item.context?.internet_exposed?.value !== undefined && item.context?.internet_exposed?.value !== null
                              ? (item.context.internet_exposed.value ? 'YES' : 'NO')
                              : 'UNKNOWN'}
                          </span>
                          <span className="text-[9px] text-[#A3ADBF] block">
                            [{item.context?.internet_exposed?.source || 'unknown'}]
                          </span>
                        </div>

                        <div className="bg-[#0F1523] p-2 rounded border border-[#232B3D]">
                          <span className="text-[#A3ADBF] block text-[10px]">Business Criticality</span>
                          <span className="text-[#F5F7FA] font-bold">
                            {item.context?.business_criticality?.value || 'UNKNOWN'}
                          </span>
                          <span className="text-[9px] text-[#A3ADBF] block">
                            [{item.context?.business_criticality?.source || 'unknown'}]
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Mosca Equation & HNDL Summary */}
                    {mosca && (
                      <div className="bg-[#0F1523] p-2.5 rounded border border-[#232B3D] text-[11px] font-mono space-y-1">
                        <div className="text-[#00FFA3] font-bold">Mosca Equation Assessment (C + M &gt; Y)</div>
                        <div className="text-[#F5F7FA]">{mosca.formula}</div>
                        <div className="text-[#A3ADBF]">{mosca.explanation}</div>
                      </div>
                    )}

                    {/* Missing Information Callout */}
                    {qri?.explanation?.missing_information && qri.explanation.missing_information.length > 0 && (
                      <div className="bg-[#FFD166]/10 border border-[#FFD166]/40 p-2.5 rounded text-[11px] space-y-1">
                        <div className="font-mono text-[#FFD166] font-bold flex items-center gap-1">
                          <AlertIcon className="w-3.5 h-3.5" />
                          Missing Context Information (Uncertainty Explicitly Tracked)
                        </div>
                        <ul className="list-disc list-inside text-[#A3ADBF] font-mono space-y-0.5">
                          {qri.explanation.missing_information.map((info, idx) => (
                            <li key={idx}>{info}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
