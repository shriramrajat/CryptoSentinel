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
        <h3 className="font-bold text-slate-100 text-sm tracking-wide">Detected Cryptographic Primitives</h3>
      }
    >
      {entries.length === 0 ? (
        <p className="text-xs text-slate-500 italic">No algorithms detected</p>
      ) : (
        <div className="divide-y divide-slate-800/60">
          {entries.map(([algo, count]) => (
            <div key={algo} className="py-2.5 flex items-center justify-between text-xs">
              <span className="font-mono font-semibold text-indigo-300">{algo}</span>
              <span className="bg-slate-800 text-slate-300 font-mono px-2 py-0.5 rounded border border-slate-700">
                {count} {count === 1 ? 'instance' : 'instances'}
              </span>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};
