import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-[#070B14] border-t border-[#232B3D] py-6 mt-12 text-xs text-[#A3ADBF]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <span className="font-mono font-semibold text-[#F5F7FA]">CryptoSentinel (ECDAT)</span> — Static Cryptographic Discovery & Post-Quantum Analysis Engine
        </div>
        <div className="flex items-center gap-6">
          <span className="font-mono text-[#A3ADBF]">NIST PQC Standards: FIPS 203 (ML-KEM) / FIPS 204 (ML-DSA)</span>
          <span className="border-l border-[#232B3D] h-3" />
          <span className="text-[#A3ADBF]">SIH 26164</span>
        </div>
      </div>
    </footer>
  );
};
