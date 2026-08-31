import React from 'react';
import type { ScanSummary } from '../../types/api';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';

interface SeverityBreakdownProps {
  summary: ScanSummary;
}

export const SeverityBreakdown: React.FC<SeverityBreakdownProps> = ({ summary }) => {
  const total = summary.total_crypto_assets || 1;

  const severities = [
    { key: 'critical', label: 'Critical Risk', count: summary.severity_counts?.critical || 0 },
    { key: 'high', label: 'High Risk', count: summary.severity_counts?.high || 0 },
    { key: 'medium', label: 'Medium Risk', count: summary.severity_counts?.medium || 0 },
    { key: 'low', label: 'Low Risk', count: summary.severity_counts?.low || 0 },
    { key: 'info', label: 'Info / Approved', count: summary.severity_counts?.info || 0 },
  ];

  return (
    <Card
      header={
        <h3 className="font-bold text-[#F5F7FA] text-sm tracking-wide">Risk Severity Distribution</h3>
      }
    >
      <div className="space-y-3">
        {severities.map((item) => {
          const pct = Math.round((item.count / total) * 100);
          return (
            <div key={item.key} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <Badge variant="severity" severity={item.key as any}>
                  {item.label}
                </Badge>
                <span className="font-mono text-[#F5F7FA] font-medium">
                  {item.count} ({pct}%)
                </span>
              </div>
              <div className="w-full bg-[#070B14] border border-[#232B3D] rounded-full h-1.5 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    item.key === 'critical'
                      ? 'bg-[#FF3B30]'
                      : item.key === 'high'
                      ? 'bg-[#FF8A00]'
                      : item.key === 'medium'
                      ? 'bg-[#FFD60A]'
                      : item.key === 'low'
                      ? 'bg-[#00C853]'
                      : 'bg-[#3B82F6]'
                  }`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
