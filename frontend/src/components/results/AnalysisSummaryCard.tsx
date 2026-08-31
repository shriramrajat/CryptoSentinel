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
    <Card className="border-[#232B3D] bg-[#0F1523]">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#232B3D] pb-4 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-[#00E5FF]">Target Path Analyzed</span>
            <span className="bg-[#171E2E] text-[#00E5FF] border border-[#00E5FF]/30 text-[10px] font-mono px-2 py-0.5 rounded">
              Engine v{metadata.scanner_version}
            </span>
          </div>
          <p className="font-mono text-sm text-[#F5F7FA] font-semibold mt-1 break-all flex items-center gap-2">
            <FolderIcon className="w-4 h-4 text-[#00E5FF] shrink-0" />
            {targetPath || 'Local Repository Target'}
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono text-[#A3ADBF] bg-[#070B14] border border-[#232B3D] p-2.5 rounded-lg shrink-0">
          <div className="flex items-center gap-1.5">
            <ClockIcon className="w-4 h-4 text-[#00E5FF]" />
            <span>Duration: <strong className="text-[#F5F7FA]">{metadata.scan_duration_ms} ms</strong></span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="bg-[#070B14] border border-[#232B3D] p-3 rounded-lg">
          <span className="text-[#A3ADBF] block text-[10px] font-semibold uppercase tracking-wider">Discovered Files</span>
          <div className="text-lg font-bold font-mono text-[#F5F7FA] mt-0.5 flex items-center gap-1.5">
            <CpuIcon className="w-4 h-4 text-[#A3ADBF]" />
            {summary.total_files_discovered}
          </div>
        </div>

        <div className="bg-[#070B14] border border-[#232B3D] p-3 rounded-lg">
          <span className="text-[#A3ADBF] block text-[10px] font-semibold uppercase tracking-wider">Scanned Files</span>
          <div className="text-lg font-bold font-mono text-[#00FFA3] mt-0.5 flex items-center gap-1.5">
            <CheckIcon className="w-4 h-4 text-[#00FFA3]" />
            {summary.total_files_scanned}
          </div>
        </div>

        <div className="bg-[#070B14] border border-[#232B3D] p-3 rounded-lg">
          <span className="text-[#A3ADBF] block text-[10px] font-semibold uppercase tracking-wider">Skipped Files</span>
          <div className="text-lg font-bold font-mono text-[#FF8A00] mt-0.5 flex items-center gap-1.5">
            <AlertIcon className="w-4 h-4 text-[#FF8A00]" />
            {summary.files_skipped}
          </div>
        </div>

        <div className="bg-[#070B14] border border-[#232B3D] p-3 rounded-lg">
          <span className="text-[#A3ADBF] block text-[10px] font-semibold uppercase tracking-wider">Discovered Primitives</span>
          <div className="text-lg font-bold font-mono text-[#00E5FF] mt-0.5">
            {summary.total_crypto_assets}
          </div>
        </div>
      </div>
    </Card>
  );
};
