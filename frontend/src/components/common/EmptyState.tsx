import React from 'react';
import { ShieldIcon } from './Icons';

interface EmptyStateProps {
  title: string;
  description: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  action,
  icon,
  className = '',
}) => {
  return (
    <div
      className={`border border-dashed border-[#232B3D] rounded-xl p-8 text-center flex flex-col items-center justify-center bg-[#0F1523]/50 ${className}`}
    >
      <div className="w-12 h-12 rounded-full bg-[#171E2E] border border-[#232B3D] flex items-center justify-center text-[#00E5FF] mb-4">
        {icon || <ShieldIcon className="w-6 h-6 text-[#00E5FF]" />}
      </div>
      <h3 className="text-base font-semibold text-[#F5F7FA] mb-1">{title}</h3>
      <p className="text-sm text-[#A3ADBF] max-w-md mb-6">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
};
