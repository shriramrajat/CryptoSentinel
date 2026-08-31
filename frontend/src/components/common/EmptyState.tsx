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
      className={`border border-dashed border-slate-800 rounded-xl p-8 text-center flex flex-col items-center justify-center bg-slate-900/30 ${className}`}
    >
      <div className="w-12 h-12 rounded-full bg-slate-800/80 border border-slate-700 flex items-center justify-center text-slate-400 mb-4">
        {icon || <ShieldIcon className="w-6 h-6 text-slate-400" />}
      </div>
      <h3 className="text-base font-semibold text-slate-200 mb-1">{title}</h3>
      <p className="text-sm text-slate-400 max-w-md mb-6">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
};
