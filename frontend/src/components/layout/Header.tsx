import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ShieldIcon, ServerIcon, RefreshIcon } from '../common/Icons';
import { useScan } from '../../context/ScanContext';

export const Header: React.FC = () => {
  const { backendOnline, checkHealth, scanResponse } = useScan();

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  const skippedCount = scanResponse?.skipped_files?.length || 0;
  const errorCount = scanResponse?.errors?.length || 0;

  return (
    <header className="bg-[#0F1523]/90 border-b border-[#232B3D] backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Header */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-lg bg-[#00E5FF]/10 border border-[#00E5FF]/40 flex items-center justify-center text-[#00E5FF] group-hover:border-[#00E5FF] transition-colors">
            <ShieldIcon className="w-5 h-5 text-[#00E5FF]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-[#F5F7FA] text-base tracking-wide font-mono">CryptoSentinel</span>
              <span className="bg-[#171E2E] text-[#A3ADBF] border border-[#232B3D] text-[10px] font-mono px-1.5 py-0.2 rounded">
                v0.1.0
              </span>
            </div>
            <p className="text-[11px] text-[#A3ADBF] hidden sm:block">Enterprise Cryptographic Discovery & PQC Engine</p>
          </div>
        </Link>

        {/* Status Indicators */}
        <div className="flex items-center gap-3">
          {/* Diagnostic alert badge if scan ran and has skipped/error files */}
          {(skippedCount > 0 || errorCount > 0) && (
            <Link
              to="/diagnostics"
              className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#FF8A00]/10 border border-[#FF8A00]/30 text-[#FF8A00] text-xs font-medium hover:bg-[#FF8A00]/20 transition-colors"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-[#FF8A00] animate-pulse" />
              <span>
                {skippedCount + errorCount} Scan Warning{skippedCount + errorCount > 1 ? 's' : ''}
              </span>
            </Link>
          )}

          {/* Backend Status Pill */}
          <div
            onClick={checkHealth}
            className="flex items-center gap-2 px-3 py-1 rounded-full bg-[#070B14] border border-[#232B3D] text-xs text-[#A3ADBF] cursor-pointer hover:border-[#00E5FF]/50 transition-colors"
            title="Click to re-check backend liveness"
          >
            <ServerIcon className="w-3.5 h-3.5 text-[#A3ADBF]" />
            {backendOnline === true && (
              <span className="flex items-center gap-1.5 text-[#00FFA3] font-medium">
                <span className="w-2 h-2 rounded-full bg-[#00FFA3]" />
                API Connected
              </span>
            )}
            {backendOnline === false && (
              <span className="flex items-center gap-1.5 text-[#FF3B30] font-medium">
                <span className="w-2 h-2 rounded-full bg-[#FF3B30]" />
                Backend Offline
              </span>
            )}
            {backendOnline === null && (
              <span className="flex items-center gap-1.5 text-[#A3ADBF]">
                <RefreshIcon className="w-3 h-3 animate-spin" />
                Checking API
              </span>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
