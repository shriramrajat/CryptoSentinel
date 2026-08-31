import React, { useEffect } from 'react';
import type { Finding } from '../../types/api';
import { Badge } from '../common/Badge';
import { CodeBlock } from '../common/CodeBlock';
import { XIcon, ShieldIcon, QuantumIcon, CodeIcon, FolderIcon } from '../common/Icons';

interface FindingDetailDrawerProps {
  finding: Finding | null;
  onClose: () => void;
}

export const FindingDetailDrawer: React.FC<FindingDetailDrawerProps> = ({ finding, onClose }) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    if (finding) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [finding, onClose]);

  if (!finding) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-[#070B14]/80 backdrop-blur-sm flex justify-end">
      {/* Backdrop overlay click to close */}
      <div className="absolute inset-0" onClick={onClose} />

      {/* Drawer Content */}
      <div className="relative w-full max-w-2xl bg-[#0F1523] border-l border-[#232B3D] h-full overflow-y-auto shadow-2xl flex flex-col z-10">
        {/* Header */}
        <div className="p-6 border-b border-[#232B3D] sticky top-0 bg-[#0F1523]/95 backdrop-blur-md flex items-start justify-between gap-4 z-10">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="severity" severity={finding.risk.severity as any}>
                {finding.risk.severity}
              </Badge>
              <Badge variant="quantum" quantumThreat={finding.risk.quantum_threat as any}>
                {finding.risk.quantum_threat} threat
              </Badge>
            </div>
            <h2 className="text-xl font-bold font-mono text-[#F5F7FA] flex items-center gap-2">
              <ShieldIcon className="w-5 h-5 text-[#00E5FF] shrink-0" />
              {finding.algorithm}
              {finding.key_length && <span className="text-sm text-[#A3ADBF]">({finding.key_length} bits)</span>}
            </h2>
            <span className="text-xs font-mono text-[#A3ADBF] block">{finding.category}</span>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-[#171E2E] text-[#A3ADBF] hover:text-[#F5F7FA] hover:bg-[#171E2E]/80 border border-[#232B3D] transition-colors cursor-pointer focus:ring-1 focus:ring-[#00E5FF]"
            aria-label="Close drawer"
          >
            <XIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Body Content */}
        <div className="p-6 space-y-6 flex-1">
          {/* Section 1: Affected Component Location */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[#A3ADBF] flex items-center gap-1.5">
              <FolderIcon className="w-4 h-4 text-[#00E5FF]" />
              Affected File Location
            </h3>
            <div className="bg-[#070B14] border border-[#232B3D] rounded-lg p-3 font-mono text-xs text-[#F5F7FA] break-all">
              <span className="text-[#00E5FF]">{finding.file_location.file_path}</span>
              <span className="text-[#FF8A00] font-bold ml-1.5">: Line {finding.file_location.line_number}</span>
            </div>
          </div>

          {/* Section 2: Risk Assessment & Rationale */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[#A3ADBF] flex items-center gap-1.5">
              <ShieldIcon className="w-4 h-4 text-[#FF3B30]" />
              Risk Analysis & Rationale
            </h3>
            <div className="bg-[#070B14] border border-[#232B3D] rounded-lg p-4 space-y-3">
              <p className="text-xs text-[#F5F7FA] leading-relaxed font-sans">{finding.risk.reason}</p>
              
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-2 border-t border-[#232B3D] text-xs font-mono">
                <div>
                  <span className="text-[10px] text-[#A3ADBF] block">CONFIDENCE</span>
                  <span className="text-[#F5F7FA] font-semibold">{Math.round(finding.risk.confidence * 100)}%</span>
                </div>
                <div>
                  <span className="text-[10px] text-[#A3ADBF] block">SEVERITY</span>
                  <span className="text-[#F5F7FA] font-semibold uppercase">{finding.risk.severity}</span>
                </div>
                <div>
                  <span className="text-[10px] text-[#A3ADBF] block">QUANTUM THREAT</span>
                  <span className="text-[#F5F7FA] font-semibold uppercase">{finding.risk.quantum_threat}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Section 3: Technical Primitive Metadata */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[#A3ADBF] flex items-center gap-1.5">
              <CodeIcon className="w-4 h-4 text-[#7C3AED]" />
              Extracted Technical Parameters
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
              <div className="bg-[#070B14] border border-[#232B3D] p-2.5 rounded-lg">
                <span className="text-[#A3ADBF] block text-[10px]">ALGORITHM</span>
                <span className="text-[#00E5FF] font-bold">{finding.algorithm}</span>
              </div>
              <div className="bg-[#070B14] border border-[#232B3D] p-2.5 rounded-lg">
                <span className="text-[#A3ADBF] block text-[10px]">KEY LENGTH</span>
                <span className="text-[#F5F7FA]">{finding.key_length ? `${finding.key_length} bits` : 'Unavailable'}</span>
              </div>
              <div className="bg-[#070B14] border border-[#232B3D] p-2.5 rounded-lg">
                <span className="text-[#A3ADBF] block text-[10px]">CIPHER MODE</span>
                <span className="text-[#F5F7FA]">{finding.mode || 'Unavailable'}</span>
              </div>
              <div className="bg-[#070B14] border border-[#232B3D] p-2.5 rounded-lg">
                <span className="text-[#A3ADBF] block text-[10px]">PADDING</span>
                <span className="text-[#F5F7FA]">{finding.padding || 'Unavailable'}</span>
              </div>
            </div>
          </div>

          {/* Section 4: Code Evidence */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[#A3ADBF] flex items-center gap-1.5">
              <CodeIcon className="w-4 h-4 text-[#00FFA3]" />
              Evidence & Code Snippet
            </h3>
            <CodeBlock
              code={finding.evidence?.code_snippet || ''}
              lineNumber={finding.file_location.line_number}
              detectionMechanism={finding.evidence?.detection_mechanism}
              matchedRuleId={finding.evidence?.matched_rule_id}
            />
          </div>

          {/* Section 5: Actionable PQC Recommendation */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[#A3ADBF] flex items-center gap-1.5">
              <QuantumIcon className="w-4 h-4 text-[#7C3AED]" />
              Recommended Organization Action
            </h3>
            {finding.risk.pqc_recommendation ? (
              <div className="bg-[#7C3AED]/15 border border-[#7C3AED]/40 rounded-xl p-4 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-[#7C3AED] font-mono">
                    NIST Target: {finding.risk.pqc_recommendation.nist_standard}
                  </span>
                  <span className="bg-[#7C3AED]/30 text-[#F5F7FA] text-[10px] font-mono px-2 py-0.5 rounded font-bold border border-[#7C3AED]/50">
                    PQC Standard
                  </span>
                </div>
                <div className="text-sm font-mono text-[#F5F7FA] font-bold">
                  Migration Target: <span className="text-[#00FFA3]">{finding.risk.pqc_recommendation.target_algorithm}</span>
                </div>
                <p className="text-xs text-[#A3ADBF] font-sans">
                  Strategy: {finding.risk.pqc_recommendation.migration_type}
                </p>
              </div>
            ) : (
              <div className="bg-[#070B14] border border-[#232B3D] rounded-lg p-3 text-xs text-[#A3ADBF]">
                Ensure strong symmetric key size (256-bit) and authenticated modes (GCM). No asymmetric PQC algorithm replacement required.
              </div>
            )}
          </div>

          {/* Section 6: Asset Identification Metadata */}
          <div className="pt-4 border-t border-[#232B3D] text-[11px] font-mono text-[#A3ADBF] flex items-center justify-between">
            <span>Deterministic SHA-256 ID:</span>
            <span className="text-[#F5F7FA]">{finding.finding_id}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
