import React from 'react';
import type { Finding } from '../../types/api';
import { Card } from '../common/Card';
import { QuantumIcon, CheckIcon } from '../common/Icons';

interface RemediationPlanCardProps {
  findings: Finding[];
  onSelectFinding: (finding: Finding) => void;
}

export const RemediationPlanCard: React.FC<RemediationPlanCardProps> = ({
  findings,
  onSelectFinding,
}) => {
  const pqcFindings = findings.filter((f) => f.risk.pqc_recommendation !== null);

  if (pqcFindings.length === 0) {
    return (
      <Card className="border-[#00FFA3]/40 bg-[#00FFA3]/10 text-center py-6">
        <div className="w-10 h-10 rounded-full bg-[#00FFA3]/20 border border-[#00FFA3]/40 flex items-center justify-center text-[#00FFA3] mx-auto mb-2">
          <CheckIcon className="w-5 h-5" />
        </div>
        <h4 className="text-sm font-bold text-[#F5F7FA]">No Post-Quantum Remediation Required</h4>
        <p className="text-xs text-[#A3ADBF] max-w-md mx-auto mt-1">
          No asymmetric cryptographic algorithms or weak key sizes requiring NIST PQC migration were discovered.
        </p>
      </Card>
    );
  }

  return (
    <Card
      header={
        <div className="flex items-center gap-2">
          <QuantumIcon className="w-5 h-5 text-[#7C3AED]" />
          <h3 className="font-bold text-[#F5F7FA] text-sm tracking-wide">
            Actionable PQC Remediation Roadmap ({pqcFindings.length} Items)
          </h3>
        </div>
      }
    >
      <div className="space-y-3">
        {pqcFindings.map((finding) => {
          const rec = finding.risk.pqc_recommendation!;
          return (
            <div
              key={finding.finding_id}
              onClick={() => onSelectFinding(finding)}
              className="bg-[#070B14] border border-[#232B3D] hover:border-[#7C3AED]/80 p-3.5 rounded-lg transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
                  <span className="bg-[#7C3AED]/20 text-[#7C3AED] border border-[#7C3AED]/40 px-2 py-0.5 rounded font-bold">
                    {rec.nist_standard}
                  </span>
                  <span className="font-bold text-[#F5F7FA]">
                    Replace {finding.algorithm} &rarr; <span className="text-[#00FFA3]">{rec.target_algorithm}</span>
                  </span>
                </div>
                <div className="text-xs font-mono text-[#00E5FF]">
                  {finding.file_location.file_path}:{finding.file_location.line_number}
                </div>
                <p className="text-[11px] text-[#A3ADBF] font-sans">{rec.migration_type}</p>
              </div>

              <button className="text-xs font-mono text-[#00E5FF] hover:text-[#00B8D4] shrink-0 text-left sm:text-right focus:ring-1 focus:ring-[#00E5FF] rounded px-1">
                View Evidence &rarr;
              </button>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
