import React from 'react';
import type { Finding } from '../../types/api';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { ChevronRightIcon } from '../common/Icons';

interface FindingCardProps {
  finding: Finding;
  onInspect: (finding: Finding) => void;
}

export const FindingCard: React.FC<FindingCardProps> = ({ finding, onInspect }) => {
  return (
    <Card hoverable className="space-y-3">
      {/* Header Row: Severity Badge, Algorithm, Quantum Threat */}
      <div className="flex items-start justify-between gap-2 border-b border-slate-800 pb-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="severity" severity={finding.risk.severity as any}>
              {finding.risk.severity}
            </Badge>
            <span className="font-mono font-bold text-base text-slate-100">{finding.algorithm}</span>
            {finding.key_length && (
              <span className="bg-slate-800 text-slate-300 font-mono text-[11px] px-1.5 py-0.2 rounded border border-slate-700">
                {finding.key_length} bits
              </span>
            )}
          </div>
          <span className="text-xs font-mono text-slate-400 block">{finding.category}</span>
        </div>

        <Badge variant="quantum" quantumThreat={finding.risk.quantum_threat as any}>
          {finding.risk.quantum_threat}
        </Badge>
      </div>

      {/* Affected Component Location */}
      <div className="text-xs font-mono bg-slate-950 border border-slate-800/80 p-2.5 rounded-lg flex items-center justify-between gap-2">
        <div className="truncate text-indigo-300">
          {finding.file_location.file_path}
          <span className="text-slate-500 font-bold ml-1">:{finding.file_location.line_number}</span>
        </div>
        <span className="text-[10px] text-slate-500 uppercase shrink-0 font-sans font-medium">
          Line {finding.file_location.line_number}
        </span>
      </div>

      {/* Risk Explanation */}
      <p className="text-xs text-slate-300 leading-relaxed line-clamp-2">
        {finding.risk.reason}
      </p>

      {/* Code Snippet Preview */}
      {finding.evidence?.code_snippet && (
        <div className="bg-slate-950 border border-slate-800/60 rounded p-2 text-xs font-mono text-slate-400 truncate">
          <span className="text-slate-600 mr-2">&gt;</span>
          {finding.evidence.code_snippet.trim()}
        </div>
      )}

      {/* Footer Inspect Trigger */}
      <div className="pt-1 flex items-center justify-between">
        <span className="text-[11px] text-slate-500 font-mono">
          ID: {finding.finding_id.substring(0, 15)}...
        </span>
        <button
          onClick={() => onInspect(finding)}
          className="text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1 cursor-pointer"
        >
          <span>Inspect Technical Evidence</span>
          <ChevronRightIcon className="w-4 h-4" />
        </button>
      </div>
    </Card>
  );
};
