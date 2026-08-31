import { useNavigate } from 'react-router-dom';
import { useScan } from '../context/ScanContext';
import { SectionHeader } from '../components/common/SectionHeader';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';
import { Button } from '../components/common/Button';
import { QuantumIcon, CheckIcon, ShieldIcon } from '../components/common/Icons';

export default function QuantumPage() {
  const { scanResponse } = useScan();
  const navigate = useNavigate();

  const findings = scanResponse?.findings || [];

  const shorFindings = findings.filter((f) => f.risk.quantum_threat.toLowerCase() === 'shor');
  const groverFindings = findings.filter((f) => f.risk.quantum_threat.toLowerCase() === 'grover');
  const totalQuantumVulnerable = shorFindings.length + groverFindings.length;

  if (!scanResponse) {
    return (
      <div className="space-y-6">
        <SectionHeader
          title="Post-Quantum Cryptography (PQC) Readiness"
          subtitle="Evaluation of cryptographic primitives against quantum computing algorithms (Shor's & Grover's)."
        />
        <EmptyState
          title="No Quantum Readiness Assessment Available"
          description="Execute a scan on the Dashboard to assess your codebase for quantum-vulnerable cryptographic algorithms."
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
        title="Post-Quantum Cryptography (PQC) Readiness"
        subtitle="Mapping legacy asymmetric and symmetric algorithms to NIST FIPS 203 / 204 post-quantum standards."
        badge={
          <span className="bg-purple-950 text-purple-300 border border-purple-800 text-xs font-mono px-2.5 py-0.5 rounded-full flex items-center gap-1.5">
            <QuantumIcon className="w-3.5 h-3.5" />
            {totalQuantumVulnerable} Quantum Vulnerable
          </span>
        }
      />

      {/* Quantum Threat Concept Overview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Shor Threat Card */}
        <Card className="border-purple-900/60 bg-purple-950/20">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded bg-purple-900/50 text-purple-300 border border-purple-700/50">
                <QuantumIcon className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-slate-100 text-sm">Shor's Algorithm Threat</h3>
            </div>
            <span className="bg-purple-900 text-purple-200 text-xs font-mono font-bold px-2 py-0.5 rounded">
              {shorFindings.length} Assets
            </span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed mb-3">
            Shor's algorithm efficiently solves prime factorization and discrete logarithms, completely breaking RSA, ECC, ECDSA, ECDH, and Diffie-Hellman asymmetric primitives.
          </p>
          <div className="bg-slate-950 border border-purple-900/50 p-2.5 rounded-lg text-xs font-mono text-purple-300 space-y-1">
            <div>Target Standard: <strong>FIPS 203 (ML-KEM)</strong> / <strong>FIPS 204 (ML-DSA)</strong></div>
            <div className="text-[11px] text-slate-400 font-sans">Action: Algorithm replacement with Module-Lattice primitives.</div>
          </div>
        </Card>

        {/* Grover Threat Card */}
        <Card className="border-blue-900/60 bg-blue-950/20">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded bg-blue-900/50 text-blue-300 border border-blue-700/50">
                <ShieldIcon className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-slate-100 text-sm">Grover's Algorithm Threat</h3>
            </div>
            <span className="bg-blue-900 text-blue-200 text-xs font-mono font-bold px-2 py-0.5 rounded">
              {groverFindings.length} Assets
            </span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed mb-3">
            Grover's algorithm provides a quadratic speedup for unstructured searching, reducing effective key strength by half (e.g. AES-128 offers 64 bits of security).
          </p>
          <div className="bg-slate-950 border border-blue-900/50 p-2.5 rounded-lg text-xs font-mono text-blue-300 space-y-1">
            <div>Target Standard: <strong>FIPS 197 (AES-256-GCM)</strong></div>
            <div className="text-[11px] text-slate-400 font-sans">Action: Upgrade key length to 256 bits and use authenticated mode.</div>
          </div>
        </Card>
      </div>

      {/* Zero Quantum Threat Banner if Clean */}
      {totalQuantumVulnerable === 0 ? (
        <Card className="border-emerald-900/60 bg-emerald-950/20 text-center py-8">
          <div className="w-12 h-12 rounded-full bg-emerald-900/40 border border-emerald-500/50 flex items-center justify-center text-emerald-400 mx-auto mb-3">
            <CheckIcon className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-emerald-200 mb-1">Zero Quantum Threats Detected</h3>
          <p className="text-xs text-slate-300 max-w-md mx-auto">
            No asymmetric primitives vulnerable to Shor's algorithm or reduced symmetric key sizes vulnerable to Grover's algorithm were found in the scanned files.
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          <h3 className="text-base font-bold text-slate-100 tracking-tight">
            Quantum Vulnerable Asset Remediation Plan ({totalQuantumVulnerable})
          </h3>

          <div className="grid grid-cols-1 gap-4">
            {shorFindings.concat(groverFindings).map((item) => (
              <Card key={item.finding_id} className="hover:border-slate-700">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3 mb-3">
                  <div className="flex items-center gap-2">
                    <Badge variant="severity" severity={item.risk.severity as any}>
                      {item.risk.severity}
                    </Badge>
                    <span className="font-mono font-bold text-sm text-slate-100">{item.algorithm}</span>
                    <span className="text-xs font-mono text-slate-400">
                      {item.file_location.file_path}:{item.file_location.line_number}
                    </span>
                  </div>
                  <Badge variant="quantum" quantumThreat={item.risk.quantum_threat as any}>
                    {item.risk.quantum_threat.toUpperCase()} THREAT
                  </Badge>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="text-slate-400 block text-[11px] font-semibold mb-1 uppercase tracking-wider">
                      Threat Reason
                    </span>
                    <p className="text-slate-300 bg-slate-950 border border-slate-800 p-2.5 rounded">
                      {item.risk.reason}
                    </p>
                  </div>

                  <div>
                    <span className="text-slate-400 block text-[11px] font-semibold mb-1 uppercase tracking-wider">
                      Recommended NIST Migration Path
                    </span>
                    {item.risk.pqc_recommendation ? (
                      <div className="bg-purple-950/40 border border-purple-800/60 p-2.5 rounded font-mono text-purple-200 space-y-1">
                        <div>
                          Target: <strong className="text-white">{item.risk.pqc_recommendation.target_algorithm}</strong> ({item.risk.pqc_recommendation.nist_standard})
                        </div>
                        <div className="text-[11px] text-purple-300/80 font-sans">
                          Strategy: {item.risk.pqc_recommendation.migration_type}
                        </div>
                      </div>
                    ) : (
                      <div className="bg-slate-950 border border-slate-800 p-2.5 rounded text-slate-400">
                        Upgrade key size / migration parameters.
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
