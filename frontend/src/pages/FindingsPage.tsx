import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useScan } from '../context/ScanContext';
import type { Finding } from '../types/api';
import { SectionHeader } from '../components/common/SectionHeader';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { CodeBlock } from '../components/common/CodeBlock';
import { EmptyState } from '../components/common/EmptyState';
import { Button } from '../components/common/Button';
import { SearchIcon, FilterIcon, ChevronRightIcon } from '../components/common/Icons';

export default function FindingsPage() {
  const { scanResponse } = useScan();
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [quantumFilter, setQuantumFilter] = useState<string>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const findings: Finding[] = scanResponse?.findings || [];

  // Filter Logic
  const filteredFindings = findings.filter((item) => {
    const matchesSearch =
      searchQuery.trim() === '' ||
      item.algorithm.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.file_location.file_path.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.evidence?.matched_rule_id || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.evidence?.code_snippet || '').toLowerCase().includes(searchQuery.toLowerCase());

    const matchesSeverity =
      severityFilter === 'all' || item.risk.severity.toLowerCase() === severityFilter.toLowerCase();

    const matchesQuantum =
      quantumFilter === 'all' || item.risk.quantum_threat.toLowerCase() === quantumFilter.toLowerCase();

    return matchesSearch && matchesSeverity && matchesQuantum;
  });

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  if (!scanResponse) {
    return (
      <div className="space-y-6">
        <SectionHeader
          title="Cryptographic Assets Inventory"
          subtitle="Detailed discovery breakdown of detected algorithms, libraries, line locations, and snippets."
        />
        <EmptyState
          title="No Cryptographic Inventory Loaded"
          description="Initiate a repository scan on the Dashboard to populate the cryptographic inventory."
          action={
            <Button variant="primary" size="sm" onClick={() => navigate('/')}>
              Go to Dashboard & Scan
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Cryptographic Assets Inventory"
        subtitle={`Showing ${filteredFindings.length} of ${findings.length} total discovered assets.`}
        badge={
          <span className="bg-indigo-950 text-indigo-300 border border-indigo-800 text-xs font-mono px-2 py-0.5 rounded-full">
            {findings.length} Assets
          </span>
        }
      />

      {/* Filter & Search Toolbar */}
      <Card>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
          {/* Keyword Search Input */}
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
              <SearchIcon className="w-4 h-4" />
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter by algorithm, file path, rule ID, or snippet..."
              className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          {/* Severity Select */}
          <div className="flex items-center gap-2">
            <FilterIcon className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
              <option value="info">Info</option>
            </select>

            {/* Quantum Threat Select */}
            <select
              value={quantumFilter}
              onChange={(e) => setQuantumFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Quantum Threats</option>
              <option value="shor">Shor Threat (Asymmetric)</option>
              <option value="grover">Grover Threat (Symmetric)</option>
              <option value="none">Quantum Safe / None</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Findings Table */}
      {filteredFindings.length === 0 ? (
        <EmptyState
          title="No Matching Cryptographic Assets"
          description="Try clearing your search query or relaxing your filter selection."
          action={
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSearchQuery('');
                setSeverityFilter('all');
                setQuantumFilter('all');
              }}
            >
              Reset Filters
            </Button>
          }
        />
      ) : (
        <Card className="overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-950 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4">Algorithm</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">File Location</th>
                  <th className="py-3 px-4">Quantum Threat</th>
                  <th className="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {filteredFindings.map((item) => {
                  const isExpanded = expandedId === item.finding_id;
                  return (
                    <React.Fragment key={item.finding_id}>
                      <tr
                        onClick={() => toggleExpand(item.finding_id)}
                        className={`hover:bg-slate-800/40 cursor-pointer transition-colors ${
                          isExpanded ? 'bg-slate-800/50' : ''
                        }`}
                      >
                        <td className="py-3 px-4">
                          <Badge variant="severity" severity={item.risk.severity as any}>
                            {item.risk.severity}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 font-mono font-bold text-slate-100">
                          {item.algorithm}
                          {item.key_length && (
                            <span className="text-[10px] text-slate-400 font-normal ml-1">
                              ({item.key_length} bits)
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-slate-300 font-mono text-[11px]">{item.category}</td>
                        <td className="py-3 px-4 font-mono text-slate-300">
                          <span className="text-indigo-300">{item.file_location.file_path}</span>
                          <span className="text-slate-500 ml-1">:{item.file_location.line_number}</span>
                        </td>
                        <td className="py-3 px-4">
                          <Badge variant="quantum" quantumThreat={item.risk.quantum_threat as any}>
                            {item.risk.quantum_threat}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <span className="text-slate-500 hover:text-slate-300 text-xs font-mono inline-flex items-center gap-1">
                            {isExpanded ? 'Collapse' : 'Inspect'}
                            <ChevronRightIcon
                              className={`w-3.5 h-3.5 transform transition-transform ${
                                isExpanded ? 'rotate-90' : ''
                              }`}
                            />
                          </span>
                        </td>
                      </tr>

                      {/* Expanded Evidence & PQC Drawer */}
                      {isExpanded && (
                        <tr className="bg-slate-950/80 border-b border-slate-800">
                          <td colSpan={6} className="p-4 space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {/* Left Pane: Finding Reasoning & Attributes */}
                              <div className="space-y-3">
                                <div>
                                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                                    Risk Rationale & Analysis
                                  </span>
                                  <p className="text-xs text-slate-200 bg-slate-900 border border-slate-800 p-2.5 rounded-lg leading-relaxed">
                                    {item.risk.reason}
                                  </p>
                                </div>

                                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                                  <div className="bg-slate-900 border border-slate-800 p-2 rounded">
                                    <span className="text-slate-500 block text-[10px]">ASSET ID</span>
                                    <span className="text-slate-300 truncate block" title={item.finding_id}>
                                      {item.finding_id}
                                    </span>
                                  </div>
                                  <div className="bg-slate-900 border border-slate-800 p-2 rounded">
                                    <span className="text-slate-500 block text-[10px]">CONFIDENCE</span>
                                    <span className="text-slate-300 block">{Math.round(item.risk.confidence * 100)}%</span>
                                  </div>
                                  {item.mode && (
                                    <div className="bg-slate-900 border border-slate-800 p-2 rounded">
                                      <span className="text-slate-500 block text-[10px]">CIPHER MODE</span>
                                      <span className="text-slate-300 block">{item.mode}</span>
                                    </div>
                                  )}
                                  {item.padding && (
                                    <div className="bg-slate-900 border border-slate-800 p-2 rounded">
                                      <span className="text-slate-500 block text-[10px]">PADDING</span>
                                      <span className="text-slate-300 block">{item.padding}</span>
                                    </div>
                                  )}
                                </div>
                              </div>

                              {/* Right Pane: Code Snippet & PQC Target */}
                              <div className="space-y-3">
                                <div>
                                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                                    Code Evidence Line
                                  </span>
                                  <CodeBlock
                                    code={item.evidence?.code_snippet || ''}
                                    lineNumber={item.file_location.line_number}
                                    detectionMechanism={item.evidence?.detection_mechanism}
                                    matchedRuleId={item.evidence?.matched_rule_id}
                                  />
                                </div>

                                {item.risk.pqc_recommendation && (
                                  <div className="bg-purple-950/40 border border-purple-900/60 rounded-lg p-3 space-y-1">
                                    <div className="flex items-center justify-between text-xs">
                                      <span className="font-semibold text-purple-200">
                                        NIST PQC Migration Path
                                      </span>
                                      <span className="bg-purple-900 text-purple-300 text-[10px] font-mono px-1.5 py-0.2 rounded">
                                        {item.risk.pqc_recommendation.nist_standard}
                                      </span>
                                    </div>
                                    <p className="text-xs text-purple-300 font-mono">
                                      Target Algorithm: <strong className="text-white">{item.risk.pqc_recommendation.target_algorithm}</strong>
                                    </p>
                                    <p className="text-[11px] text-purple-300/80">
                                      Migration Strategy: {item.risk.pqc_recommendation.migration_type}
                                    </p>
                                  </div>
                                )}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
