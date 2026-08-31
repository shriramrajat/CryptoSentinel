import React from 'react';
import type { ScanSummary, ScanMetadata } from '../../types/api';
import { Card } from '../common/Card';
import { CpuIcon, ClockIcon, FolderIcon, AlertIcon, CheckIcon } from '../common/Icons';

interface AnalysisSummaryCardProps {
  targetPath: string;
  summary: ScanSummary;
  metadata: ScanMetadata;
}

export const AnalysisSummaryCard: React.FC<AnalysisSummaryCardProps> = ({
  targetPath,
  summary,
  metadata,
}) => {
  return (
    <Card className="border-indigo-900/40 bg-indigo-950/10">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400">Target Path Analyzed</span>
            <span className="bg-indigo-950 text-indigo-300 border border-indigo-800/80 text-[10px] font-mono px-2 py-0.5 rounded">
              Engine v{metadata.scanner_version}
            </span>
          </div>
          <p className="font-mono text-sm text-slate-100 font-semibold mt-1 break-all flex items-center gap-2">
            <FolderIcon className="w-4 h-4 text-indigo-400 shrink-0" />
            {targetPath || 'Local Repository Target'}
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono text-slate-300 bg-slate-900 border border-slate-800 p-2.5 rounded-lg shrink-0">
          <div className="flex items-center gap-1.5">
            <ClockIcon className="w-4 h-4 text-indigo-400" />
            <span>Duration: <strong className="text-white">{metadata.scan_duration_ms} ms</strong></span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="bg-slate-900/80 border border-slate-800 p-3 rounded-lg">
          <span className="text-slate-400 block text-[10px] font-semibold uppercase tracking-wider">Discovered Files</span>
          <div className="text-lg font-bold font-mono text-slate-100 mt-0.5 flex items-center gap-1.5">
            <CpuIcon className="w-4 h-4 text-slate-400" />
            {summary.total_files_discovered}
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-3 rounded-lg">
          <span className="text-slate-400 block text-[10px] font-semibold uppercase tracking-wider">Scanned Files</span>
          <div className="text-lg font-bold font-mono text-emerald-400 mt-0.5 flex items-center gap-1.5">
            <CheckIcon className="w-4 h-4 text-emerald-400" />
            {summary.total_files_scanned}
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-3 rounded-lg">
          <span className="text-slate-400 block text-[10px] font-semibold uppercase tracking-wider">Skipped Files</span>
          <div className="text-lg font-bold font-mono text-amber-400 mt-0.5 flex items-center gap-1.5">
            <AlertIcon className="w-4 h-4 text-amber-400" />
            {summary.files_skipped}
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-3 rounded-lg">
          <span className="text-slate-400 block text-[10px] font-semibold uppercase tracking-wider">Discovered Primitives</span>
          <div className="text-lg font-bold font-mono text-indigo-300 mt-0.5">
            {summary.total_crypto_assets}
          </div>
        </div>
      </div>
    </Card>
  );
};
