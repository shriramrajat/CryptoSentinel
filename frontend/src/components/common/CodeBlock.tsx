import React, { useState } from 'react';
import { CheckIcon } from './Icons';

interface CodeBlockProps {
  code: string;
  language?: string;
  lineNumber?: number;
  matchedRuleId?: string;
  detectionMechanism?: string;
  className?: string;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  language = 'python',
  lineNumber,
  matchedRuleId,
  detectionMechanism,
  className = '',
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`rounded-lg border border-slate-800 bg-slate-950 overflow-hidden ${className}`}>
      <div className="flex items-center justify-between px-3 py-1.5 bg-slate-900/90 border-b border-slate-800 text-xs text-slate-400 font-mono">
        <div className="flex items-center gap-2">
          <span className="uppercase text-slate-500 font-semibold">{language}</span>
          {lineNumber !== undefined && (
            <span className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">Line {lineNumber}</span>
          )}
          {detectionMechanism && (
            <span className="bg-indigo-950/80 text-indigo-300 border border-indigo-800/50 px-1.5 py-0.5 rounded">
              {detectionMechanism}
            </span>
          )}
          {matchedRuleId && (
            <span className="text-slate-500 truncate max-w-[200px]" title={matchedRuleId}>
              rule: {matchedRuleId}
            </span>
          )}
        </div>
        <button
          onClick={handleCopy}
          className="hover:text-white transition-colors p-1 rounded hover:bg-slate-800 flex items-center gap-1"
          title="Copy code snippet"
        >
          {copied ? (
            <>
              <CheckIcon className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <span>Copy</span>
          )}
        </button>
      </div>
      <div className="p-3 overflow-x-auto text-xs font-mono text-slate-200 leading-relaxed">
        <code>{code || '// Snippet unavailable'}</code>
      </div>
    </div>
  );
};
