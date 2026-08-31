import React from 'react';

export type SeverityType = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type QuantumThreatType = 'shor' | 'grover' | 'none';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'severity' | 'quantum' | 'default' | 'outline' | 'success';
  severity?: SeverityType;
  quantumThreat?: QuantumThreatType;
  className?: string;
  dot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  severity,
  quantumThreat,
  className = '',
  dot = true,
}) => {
  let colorClasses = 'bg-slate-800 text-slate-300 border-slate-700';
  let dotColor = 'bg-slate-400';

  if (variant === 'severity' && severity) {
    switch (severity.toLowerCase()) {
      case 'critical':
        colorClasses = 'bg-red-950/80 text-red-300 border-red-800/60';
        dotColor = 'bg-red-500 animate-pulse';
        break;
      case 'high':
        colorClasses = 'bg-amber-950/80 text-amber-300 border-amber-800/60';
        dotColor = 'bg-amber-500';
        break;
      case 'medium':
        colorClasses = 'bg-yellow-950/80 text-yellow-300 border-yellow-800/60';
        dotColor = 'bg-yellow-500';
        break;
      case 'low':
        colorClasses = 'bg-emerald-950/80 text-emerald-300 border-emerald-800/60';
        dotColor = 'bg-emerald-500';
        break;
      case 'info':
        colorClasses = 'bg-cyan-950/80 text-cyan-300 border-cyan-800/60';
        dotColor = 'bg-cyan-500';
        break;
    }
  } else if (variant === 'quantum' && quantumThreat) {
    switch (quantumThreat.toLowerCase()) {
      case 'shor':
        colorClasses = 'bg-purple-950/80 text-purple-300 border-purple-800/60';
        dotColor = 'bg-purple-400';
        break;
      case 'grover':
        colorClasses = 'bg-blue-950/80 text-blue-300 border-blue-800/60';
        dotColor = 'bg-blue-400';
        break;
      case 'none':
        colorClasses = 'bg-slate-900 text-slate-400 border-slate-800';
        dotColor = 'bg-slate-500';
        break;
    }
  } else if (variant === 'success') {
    colorClasses = 'bg-emerald-950/80 text-emerald-300 border-emerald-800/60';
    dotColor = 'bg-emerald-400';
  } else if (variant === 'outline') {
    colorClasses = 'bg-transparent text-slate-300 border-slate-700';
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-medium border ${colorClasses} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />}
      {children}
    </span>
  );
};
