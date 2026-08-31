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
      className={`border border-indigo-900/50 bg-indigo-950/20 rounded-xl p-8 text-center flex flex-col items-center justify-center ${className}`}
    >
      <div className="relative mb-5">
        <div className="w-14 h-14 rounded-full bg-indigo-900/40 border border-indigo-500/50 flex items-center justify-center text-indigo-400 animate-pulse">
          <CpuIcon className="w-7 h-7 text-indigo-400" />
        </div>
        <div className="absolute -bottom-1 -right-1 bg-indigo-600 text-white text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-full">
          {elapsedSeconds}s
        </div>
      </div>
      <h3 className="text-base font-semibold text-slate-100 mb-1">{message}</h3>
      <p className="text-xs text-slate-400 max-w-lg mb-4">{subtext}</p>
      
      {/* Dynamic Progress Bar Placeholder */}
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-full h-2 overflow-hidden">
        <div className="bg-indigo-500 h-full rounded-full animate-pulse w-3/4" />
      </div>
    </div>
  );
};
