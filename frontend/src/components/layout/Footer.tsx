import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-950 border-t border-slate-800/80 py-6 mt-12 text-xs text-slate-500">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <span className="font-mono font-semibold text-slate-400">CryptoSentinel (ECDAT)</span> — Static Cryptographic Discovery & Post-Quantum Analysis Engine
        </div>
        <div className="flex items-center gap-6">
          <span className="font-mono text-slate-500">NIST PQC Standards: FIPS 203 (ML-KEM) / FIPS 204 (ML-DSA)</span>
          <span className="border-l border-slate-800 h-3" />
          <span className="text-slate-400">SIH 26164</span>
        </div>
      </div>
    </footer>
  );
};
