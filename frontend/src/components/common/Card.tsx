import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  header,
  footer,
  hoverable = false,
}) => {
  return (
    <div
      className={`bg-slate-900 border border-slate-800/80 rounded-xl shadow-lg transition-all ${
        hoverable ? 'hover:border-slate-700/80 hover:bg-slate-900/90' : ''
      } ${className}`}
    >
      {header && (
        <div className="px-5 py-4 border-b border-slate-800/80 flex items-center justify-between">
          {header}
        </div>
      )}
      <div className="p-5">{children}</div>
      {footer && (
        <div className="px-5 py-3 border-t border-slate-800/80 bg-slate-950/40 rounded-b-xl">
          {footer}
        </div>
      )}
    </div>
  );
};
