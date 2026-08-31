import React from 'react';
import type { ScanSummary, ScanMetadata } from '../../types/api';
import { Card } from '../common/Card';
import { ShieldIcon, QuantumIcon, AlertIcon, ClockIcon } from '../common/Icons';

interface OverviewMetricsProps {
  summary: ScanSummary;
  metadata: ScanMetadata;
}

export const OverviewMetrics: React.FC<OverviewMetricsProps> = ({ summary, metadata }) => {
  const criticalHighCount = (summary.severity_counts?.critical || 0) + (summary.severity_counts?.high || 0);

  const metrics = [
    {
      title: 'Total Crypto Assets',
      value: summary.total_crypto_assets,
      sub: `${summary.total_files_scanned} files scanned`,
      icon: <ShieldIcon className="w-5 h-5 text-indigo-400" />,
      color: 'border-indigo-800/40 bg-indigo-950/20',
    },
    {
      title: 'Quantum Vulnerable Assets',
      value: summary.quantum_vulnerable_assets,
      sub: `Shor: ${summary.quantum_threat_counts?.shor || 0} | Grover: ${summary.quantum_threat_counts?.grover || 0}`,
      icon: <QuantumIcon className="w-5 h-5 text-purple-400" />,
      color: 'border-purple-800/40 bg-purple-950/20',
    },
    {
      title: 'Critical & High Risks',
      value: criticalHighCount,
      sub: `Critical: ${summary.severity_counts?.critical || 0} | High: ${summary.severity_counts?.high || 0}`,
      icon: <AlertIcon className="w-5 h-5 text-red-400" />,
      color: 'border-red-800/40 bg-red-950/20',
    },
    {
      title: 'Scan Duration',
      value: `${metadata.scan_duration_ms} ms`,
      sub: `Engine v${metadata.scanner_version}`,
      icon: <ClockIcon className="w-5 h-5 text-emerald-400" />,
      color: 'border-emerald-800/40 bg-emerald-950/20',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric, idx) => (
        <Card key={idx} className={`${metric.color}`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{metric.title}</span>
            <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">{metric.icon}</div>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold font-mono text-slate-100">{metric.value}</div>
            <p className="text-xs text-slate-400 mt-1">{metric.sub}</p>
          </div>
        </Card>
      ))}
    </div>
  );
};
