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
      <Card className="border-emerald-900/60 bg-emerald-950/20 text-center py-6">
        <div className="w-10 h-10 rounded-full bg-emerald-900/40 border border-emerald-500/50 flex items-center justify-center text-emerald-400 mx-auto mb-2">
          <CheckIcon className="w-5 h-5" />
        </div>
        <h4 className="text-sm font-bold text-emerald-200">No Post-Quantum Remediation Required</h4>
        <p className="text-xs text-slate-300 max-w-md mx-auto mt-1">
          No asymmetric cryptographic algorithms or weak key sizes requiring NIST PQC migration were discovered.
        </p>
      </Card>
    );
  }

  return (
    <Card
      header={
        <div className="flex items-center gap-2">
          <QuantumIcon className="w-5 h-5 text-purple-400" />
          <h3 className="font-bold text-slate-100 text-sm tracking-wide">
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
              className="bg-slate-950 border border-slate-800 hover:border-purple-800/80 p-3.5 rounded-lg transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
                  <span className="bg-purple-950 text-purple-300 border border-purple-800 px-2 py-0.5 rounded font-bold">
                    {rec.nist_standard}
                  </span>
                  <span className="font-bold text-slate-100">
                    Replace {finding.algorithm} &rarr; <span className="text-purple-300">{rec.target_algorithm}</span>
                  </span>
                </div>
                <div className="text-xs font-mono text-indigo-300">
                  {finding.file_location.file_path}:{finding.file_location.line_number}
                </div>
                <p className="text-[11px] text-slate-400 font-sans">{rec.migration_type}</p>
              </div>

              <button className="text-xs font-mono text-indigo-400 hover:text-indigo-300 shrink-0 text-left sm:text-right">
                View Evidence &rarr;
              </button>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
