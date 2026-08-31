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
  let colorClasses = 'bg-[#171E2E] text-[#A3ADBF] border-[#232B3D]';
  let dotColor = 'bg-[#A3ADBF]';

  if (variant === 'severity' && severity) {
    switch (severity.toLowerCase()) {
      case 'critical':
        colorClasses = 'bg-[#FF3B30]/10 text-[#FF3B30] border-[#FF3B30]/30';
        dotColor = 'bg-[#FF3B30] animate-pulse';
        break;
      case 'high':
        colorClasses = 'bg-[#FF8A00]/10 text-[#FF8A00] border-[#FF8A00]/30';
        dotColor = 'bg-[#FF8A00]';
        break;
      case 'medium':
        colorClasses = 'bg-[#FFD60A]/10 text-[#FFD60A] border-[#FFD60A]/30';
        dotColor = 'bg-[#FFD60A]';
        break;
      case 'low':
        colorClasses = 'bg-[#00C853]/10 text-[#00C853] border-[#00C853]/30';
        dotColor = 'bg-[#00C853]';
        break;
      case 'info':
        colorClasses = 'bg-[#3B82F6]/10 text-[#3B82F6] border-[#3B82F6]/30';
        dotColor = 'bg-[#3B82F6]';
        break;
    }
  } else if (variant === 'quantum' && quantumThreat) {
    switch (quantumThreat.toLowerCase()) {
      case 'shor':
        colorClasses = 'bg-[#8B5CF6]/15 text-[#8B5CF6] border-[#8B5CF6]/40';
        dotColor = 'bg-[#8B5CF6]';
        break;
      case 'grover':
        colorClasses = 'bg-[#06D6A0]/15 text-[#06D6A0] border-[#06D6A0]/40';
        dotColor = 'bg-[#06D6A0]';
        break;
      case 'none':
        colorClasses = 'bg-[#10B981]/15 text-[#10B981] border-[#10B981]/40';
        dotColor = 'bg-[#10B981]';
        break;
    }
  } else if (variant === 'success') {
    colorClasses = 'bg-[#00FFA3]/10 text-[#00FFA3] border-[#00FFA3]/30';
    dotColor = 'bg-[#00FFA3]';
  } else if (variant === 'outline') {
    colorClasses = 'bg-transparent text-[#A3ADBF] border-[#232B3D]';
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
