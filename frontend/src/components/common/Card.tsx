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
      className={`bg-[#0F1523] border border-[#232B3D] rounded-xl transition-all ${
        hoverable ? 'hover:border-[#00E5FF]/40 hover:bg-[#171E2E]' : ''
      } ${className}`}
    >
      {header && (
        <div className="px-5 py-4 border-b border-[#232B3D] flex items-center justify-between">
          {header}
        </div>
      )}
      <div className="p-5">{children}</div>
      {footer && (
        <div className="px-5 py-3 border-t border-[#232B3D] bg-[#070B14]/40 rounded-b-xl">
          {footer}
        </div>
      )}
    </div>
  );
};
