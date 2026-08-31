import React from 'react';
import { Card } from '../common/Card';

interface TopAlgorithmsListProps {
  algorithmDistribution: Record<string, number>;
}

export const TopAlgorithmsList: React.FC<TopAlgorithmsListProps> = ({ algorithmDistribution }) => {
  const entries = Object.entries(algorithmDistribution || {}).sort((a, b) => b[1] - a[1]);

  return (
    <Card
      header={
        <h3 className="font-bold text-[#F5F7FA] text-sm tracking-wide">Detected Cryptographic Primitives</h3>
      }
    >
      {entries.length === 0 ? (
        <p className="text-xs text-[#A3ADBF] italic">No algorithms detected</p>
      ) : (
        <div className="divide-y divide-[#232B3D]">
          {entries.map(([algo, count]) => (
            <div key={algo} className="py-2.5 flex items-center justify-between text-xs">
              <span className="font-mono font-semibold text-[#00E5FF]">{algo}</span>
              <span className="bg-[#171E2E] text-[#F5F7FA] font-mono px-2 py-0.5 rounded border border-[#232B3D]">
                {count} {count === 1 ? 'instance' : 'instances'}
              </span>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};
