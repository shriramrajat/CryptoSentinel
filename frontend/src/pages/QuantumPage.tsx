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
          <span className="bg-[#7C3AED]/20 text-[#7C3AED] border border-[#7C3AED]/40 text-xs font-mono px-2.5 py-0.5 rounded-full flex items-center gap-1.5">
            <QuantumIcon className="w-3.5 h-3.5" />
            {totalQuantumVulnerable} Quantum Vulnerable
          </span>
        }
      />

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
            Shor's algorithm efficiently solves prime factorization and discrete logarithms, completely breaking RSA, ECC, ECDSA, ECDH, and Diffie-Hellman asymmetric primitives.
          </p>
          <div className="bg-[#070B14] border border-[#8B5CF6]/40 p-2.5 rounded-lg text-xs font-mono text-[#8B5CF6] space-y-1">
            <div>Target Standard: <strong>FIPS 203 (ML-KEM)</strong> / <strong>FIPS 204 (ML-DSA)</strong></div>
            <div className="text-[11px] text-[#A3ADBF] font-sans">Action: Algorithm replacement with Module-Lattice primitives.</div>
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
            Grover's algorithm provides a quadratic speedup for unstructured searching, reducing effective key strength by half (e.g. AES-128 offers 64 bits of security).
          </p>
          <div className="bg-[#070B14] border border-[#06D6A0]/40 p-2.5 rounded-lg text-xs font-mono text-[#06D6A0] space-y-1">
            <div>Target Standard: <strong>FIPS 197 (AES-256-GCM)</strong></div>
            <div className="text-[11px] text-[#A3ADBF] font-sans">Action: Upgrade key length to 256 bits and use authenticated mode.</div>
          </div>
        </Card>
      </div>

      {/* Zero Quantum Threat Banner if Clean */}
      {totalQuantumVulnerable === 0 ? (
        <Card className="border-[#10B981]/40 bg-[#10B981]/10 text-center py-8">
          <div className="w-12 h-12 rounded-full bg-[#10B981]/20 border border-[#10B981]/40 flex items-center justify-center text-[#10B981] mx-auto mb-3">
            <CheckIcon className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-[#F5F7FA] mb-1">Zero Quantum Threats Detected</h3>
          <p className="text-xs text-[#A3ADBF] max-w-md mx-auto">
            No asymmetric primitives vulnerable to Shor's algorithm or reduced symmetric key sizes vulnerable to Grover's algorithm were found in the scanned files.
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          <h3 className="text-base font-bold text-[#F5F7FA] tracking-tight">
            Quantum Vulnerable Asset Remediation Plan ({totalQuantumVulnerable})
          </h3>

          <div className="grid grid-cols-1 gap-4">
            {shorFindings.concat(groverFindings).map((item) => (
              <Card key={item.finding_id} className="hover:border-[#7C3AED]/50 bg-[#0F1523] border border-[#232B3D]">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#232B3D] pb-3 mb-3">
                  <div className="flex items-center gap-2">
                    <Badge variant="severity" severity={item.risk.severity as any}>
                      {item.risk.severity}
                    </Badge>
                    <span className="font-mono font-bold text-sm text-[#F5F7FA]">{item.algorithm}</span>
                    <span className="text-xs font-mono text-[#00E5FF]">
                      {item.file_location.file_path}:{item.file_location.line_number}
                    </span>
                  </div>
                  <Badge variant="quantum" quantumThreat={item.risk.quantum_threat as any}>
                    {item.risk.quantum_threat.toUpperCase()} THREAT
                  </Badge>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="text-[#A3ADBF] block text-[11px] font-semibold mb-1 uppercase tracking-wider">
                      Threat Reason
                    </span>
                    <p className="text-[#F5F7FA] bg-[#070B14] border border-[#232B3D] p-2.5 rounded">
                      {item.risk.reason}
                    </p>
                  </div>

                  <div>
                    <span className="text-[#A3ADBF] block text-[11px] font-semibold mb-1 uppercase tracking-wider">
                      Recommended NIST Migration Path
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
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
