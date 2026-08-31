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
      <div className="flex items-start justify-between gap-2 border-b border-[#232B3D] pb-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="severity" severity={finding.risk.severity as any}>
              {finding.risk.severity}
            </Badge>
            <span className="font-mono font-bold text-base text-[#F5F7FA]">{finding.algorithm}</span>
            {finding.key_length && (
              <span className="bg-[#171E2E] text-[#A3ADBF] font-mono text-[11px] px-1.5 py-0.2 rounded border border-[#232B3D]">
                {finding.key_length} bits
              </span>
            )}
          </div>
          <span className="text-xs font-mono text-[#A3ADBF] block">{finding.category}</span>
        </div>

        <Badge variant="quantum" quantumThreat={finding.risk.quantum_threat as any}>
          {finding.risk.quantum_threat}
        </Badge>
      </div>

      {/* Affected Component Location */}
      <div className="text-xs font-mono bg-[#070B14] border border-[#232B3D] p-2.5 rounded-lg flex items-center justify-between gap-2">
        <div className="truncate text-[#00E5FF]">
          {finding.file_location.file_path}
          <span className="text-[#FF8A00] font-bold ml-1">:{finding.file_location.line_number}</span>
        </div>
        <span className="text-[10px] text-[#A3ADBF] uppercase shrink-0 font-sans font-medium">
          Line {finding.file_location.line_number}
        </span>
      </div>

      {/* Risk Explanation */}
      <p className="text-xs text-[#F5F7FA] leading-relaxed line-clamp-2">
        {finding.risk.reason}
      </p>

      {/* Code Snippet Preview */}
      {finding.evidence?.code_snippet && (
        <div className="bg-[#070B14] border border-[#232B3D] rounded p-2 text-xs font-mono text-[#A3ADBF] truncate">
          <span className="text-[#00E5FF] mr-2">&gt;</span>
          {finding.evidence.code_snippet.trim()}
        </div>
      )}

      {/* Footer Inspect Trigger */}
      <div className="pt-1 flex items-center justify-between">
        <span className="text-[11px] text-[#A3ADBF] font-mono">
          ID: {finding.finding_id.substring(0, 15)}...
        </span>
        <button
          onClick={() => onInspect(finding)}
          className="text-xs font-medium text-[#00E5FF] hover:text-[#00B8D4] transition-colors flex items-center gap-1 cursor-pointer focus:ring-1 focus:ring-[#00E5FF] rounded px-1"
        >
          <span>Inspect Technical Evidence</span>
          <ChevronRightIcon className="w-4 h-4" />
        </button>
      </div>
    </Card>
  );
};
