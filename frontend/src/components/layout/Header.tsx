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
    <header className="bg-slate-950/90 border-b border-slate-800/80 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Header */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-lg bg-indigo-950/80 border border-indigo-500/40 flex items-center justify-center text-indigo-400 group-hover:border-indigo-400 transition-colors">
            <ShieldIcon className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-100 text-base tracking-wide font-mono">CryptoSentinel</span>
              <span className="bg-slate-800 text-slate-400 border border-slate-700 text-[10px] font-mono px-1.5 py-0.2 rounded">
                v0.1.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">Enterprise Cryptographic Discovery & PQC Engine</p>
          </div>
        </Link>

        {/* Status Indicators */}
        <div className="flex items-center gap-3">
          {/* Diagnostic alert badge if scan ran and has skipped/error files */}
          {(skippedCount > 0 || errorCount > 0) && (
            <Link
              to="/diagnostics"
              className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-950/60 border border-amber-800/60 text-amber-300 text-xs font-medium hover:bg-amber-900/60 transition-colors"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
              <span>
                {skippedCount + errorCount} Scan Warning{skippedCount + errorCount > 1 ? 's' : ''}
              </span>
            </Link>
          )}

          {/* Backend Status Pill */}
          <div
            onClick={checkHealth}
            className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs text-slate-300 cursor-pointer hover:border-slate-700 transition-colors"
            title="Click to re-check backend liveness"
          >
            <ServerIcon className="w-3.5 h-3.5 text-slate-400" />
            {backendOnline === true && (
              <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                API Connected
              </span>
            )}
            {backendOnline === false && (
              <span className="flex items-center gap-1.5 text-red-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-red-500" />
                Backend Offline
              </span>
            )}
            {backendOnline === null && (
              <span className="flex items-center gap-1.5 text-slate-400">
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
