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
    <div className={`rounded-lg border border-[#232B3D] bg-[#070B14] overflow-hidden ${className}`}>
      <div className="flex items-center justify-between px-3 py-1.5 bg-[#0F1523] border-b border-[#232B3D] text-xs text-[#A3ADBF] font-mono">
        <div className="flex items-center gap-2">
          <span className="uppercase text-[#A3ADBF] font-semibold">{language}</span>
          {lineNumber !== undefined && (
            <span className="bg-[#171E2E] px-1.5 py-0.5 rounded text-[#F5F7FA] border border-[#232B3D]">Line {lineNumber}</span>
          )}
          {detectionMechanism && (
            <span className="bg-[#171E2E] text-[#00E5FF] border border-[#00E5FF]/30 px-1.5 py-0.5 rounded">
              {detectionMechanism}
            </span>
          )}
          {matchedRuleId && (
            <span className="text-[#00E5FF]/90 truncate max-w-[200px]" title={matchedRuleId}>
              rule: {matchedRuleId}
            </span>
          )}
        </div>
        <button
          onClick={handleCopy}
          className="hover:text-white transition-colors p-1 rounded hover:bg-[#171E2E] flex items-center gap-1 focus:outline-none focus:ring-1 focus:ring-[#00E5FF]"
          title="Copy code snippet"
        >
          {copied ? (
            <>
              <CheckIcon className="w-3.5 h-3.5 text-[#00FFA3]" />
              <span className="text-[#00FFA3]">Copied</span>
            </>
          ) : (
            <span>Copy</span>
          )}
        </button>
      </div>
      <div className="p-3 overflow-x-auto text-xs font-mono text-[#F5F7FA] leading-relaxed">
        <code>{code || '// Snippet unavailable'}</code>
      </div>
    </div>
  );
};
