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
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-950/80 backdrop-blur-sm flex justify-end">
      {/* Backdrop overlay click to close */}
      <div className="absolute inset-0" onClick={onClose} />

      {/* Drawer Content */}
      <div className="relative w-full max-w-2xl bg-slate-900 border-l border-slate-800 h-full overflow-y-auto shadow-2xl flex flex-col z-10">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 sticky top-0 bg-slate-900/95 backdrop-blur-md flex items-start justify-between gap-4 z-10">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="severity" severity={finding.risk.severity as any}>
                {finding.risk.severity}
              </Badge>
              <Badge variant="quantum" quantumThreat={finding.risk.quantum_threat as any}>
                {finding.risk.quantum_threat} threat
              </Badge>
            </div>
            <h2 className="text-xl font-bold font-mono text-slate-100 flex items-center gap-2">
              <ShieldIcon className="w-5 h-5 text-indigo-400 shrink-0" />
              {finding.algorithm}
              {finding.key_length && <span className="text-sm text-slate-400">({finding.key_length} bits)</span>}
            </h2>
            <span className="text-xs font-mono text-slate-400 block">{finding.category}</span>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors cursor-pointer"
            aria-label="Close drawer"
          >
            <XIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Body Content */}
        <div className="p-6 space-y-6 flex-1">
          {/* Section 1: Affected Component Location */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <FolderIcon className="w-4 h-4 text-indigo-400" />
              Affected File Location
            </h3>
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 font-mono text-xs text-slate-200 break-all">
              <span className="text-indigo-300">{finding.file_location.file_path}</span>
              <span className="text-amber-400 font-bold ml-1.5">: Line {finding.file_location.line_number}</span>
            </div>
          </div>

          {/* Section 2: Risk Assessment & Rationale */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <ShieldIcon className="w-4 h-4 text-red-400" />
              Risk Analysis & Rationale
            </h3>
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 space-y-3">
              <p className="text-xs text-slate-200 leading-relaxed font-sans">{finding.risk.reason}</p>
              
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-2 border-t border-slate-800 text-xs font-mono">
                <div>
                  <span className="text-[10px] text-slate-500 block">CONFIDENCE</span>
                  <span className="text-slate-200 font-semibold">{Math.round(finding.risk.confidence * 100)}%</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block">SEVERITY</span>
                  <span className="text-slate-200 font-semibold uppercase">{finding.risk.severity}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block">QUANTUM THREAT</span>
                  <span className="text-slate-200 font-semibold uppercase">{finding.risk.quantum_threat}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Section 3: Technical Primitive Metadata */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <CodeIcon className="w-4 h-4 text-purple-400" />
              Extracted Technical Parameters
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
              <div className="bg-slate-950 border border-slate-800 p-2.5 rounded-lg">
                <span className="text-slate-500 block text-[10px]">ALGORITHM</span>
                <span className="text-indigo-300 font-bold">{finding.algorithm}</span>
              </div>
              <div className="bg-slate-950 border border-slate-800 p-2.5 rounded-lg">
                <span className="text-slate-500 block text-[10px]">KEY LENGTH</span>
                <span className="text-slate-200">{finding.key_length ? `${finding.key_length} bits` : 'Unavailable'}</span>
              </div>
              <div className="bg-slate-950 border border-slate-800 p-2.5 rounded-lg">
                <span className="text-slate-500 block text-[10px]">CIPHER MODE</span>
                <span className="text-slate-200">{finding.mode || 'Unavailable'}</span>
              </div>
              <div className="bg-slate-950 border border-slate-800 p-2.5 rounded-lg">
                <span className="text-slate-500 block text-[10px]">PADDING</span>
                <span className="text-slate-200">{finding.padding || 'Unavailable'}</span>
              </div>
            </div>
          </div>

          {/* Section 4: Code Evidence */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <CodeIcon className="w-4 h-4 text-emerald-400" />
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
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <QuantumIcon className="w-4 h-4 text-purple-400" />
              Recommended Organization Action
            </h3>
            {finding.risk.pqc_recommendation ? (
              <div className="bg-purple-950/40 border border-purple-800/60 rounded-xl p-4 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-purple-200 font-mono">
                    NIST Target: {finding.risk.pqc_recommendation.nist_standard}
                  </span>
                  <span className="bg-purple-900 text-purple-200 text-[10px] font-mono px-2 py-0.5 rounded font-bold">
                    PQC Standard
                  </span>
                </div>
                <div className="text-sm font-mono text-slate-100 font-bold">
                  Migration Target: <span className="text-purple-300">{finding.risk.pqc_recommendation.target_algorithm}</span>
                </div>
                <p className="text-xs text-purple-300/80 font-sans">
                  Strategy: {finding.risk.pqc_recommendation.migration_type}
                </p>
              </div>
            ) : (
              <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-400">
                Ensure strong symmetric key size (256-bit) and authenticated modes (GCM). No asymmetric PQC algorithm replacement required.
              </div>
            )}
          </div>

          {/* Section 6: Asset Identification Metadata */}
          <div className="pt-4 border-t border-slate-800 text-[11px] font-mono text-slate-500 flex items-center justify-between">
            <span>Deterministic SHA-256 ID:</span>
            <span className="text-slate-400">{finding.finding_id}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
