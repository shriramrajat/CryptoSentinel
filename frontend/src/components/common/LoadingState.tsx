import React, { useState, useEffect } from 'react';
import { CpuIcon } from './Icons';

interface LoadingStateProps {
  message?: string;
  subtext?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Scanning repository for cryptographic assets...',
  subtext = 'Analyzing AST call graphs, comment stripping, and regular expression patterns.',
  className = '',
}) => {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div
      className={`border border-[#00E5FF]/30 bg-[#0F1523] rounded-xl p-8 text-center flex flex-col items-center justify-center ${className}`}
    >
      <div className="relative mb-5">
        <div className="w-14 h-14 rounded-full bg-[#171E2E] border border-[#00E5FF]/40 flex items-center justify-center text-[#00E5FF] animate-pulse">
          <CpuIcon className="w-7 h-7 text-[#00E5FF]" />
        </div>
        <div className="absolute -bottom-1 -right-1 bg-[#00E5FF] text-[#070B14] text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-full">
          {elapsedSeconds}s
        </div>
      </div>
      <h3 className="text-base font-semibold text-[#F5F7FA] mb-1">{message}</h3>
      <p className="text-xs text-[#A3ADBF] max-w-lg mb-4">{subtext}</p>
      
      {/* Dynamic Progress Bar Placeholder */}
      <div className="w-full max-w-md bg-[#070B14] border border-[#232B3D] rounded-full h-2 overflow-hidden">
        <div className="bg-[#00E5FF] h-full rounded-full animate-pulse w-3/4" />
      </div>
    </div>
  );
};
