import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useScan } from '../context/ScanContext';
import type { Finding } from '../types/api';
import { SectionHeader } from '../components/common/SectionHeader';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';
import { Button } from '../components/common/Button';
import { AnalysisSummaryCard } from '../components/results/AnalysisSummaryCard';
import { FindingCard } from '../components/results/FindingCard';
import { FindingDetailDrawer } from '../components/results/FindingDetailDrawer';
import { RemediationPlanCard } from '../components/results/RemediationPlanCard';
import { OverviewMetrics } from '../components/dashboard/OverviewMetrics';
import { SeverityBreakdown } from '../components/dashboard/SeverityBreakdown';
import { TopAlgorithmsList } from '../components/dashboard/TopAlgorithmsList';
import { SearchIcon, FilterIcon, ShieldIcon, QuantumIcon } from '../components/common/Icons';

export default function ResultsPage() {
  const { scanResponse, targetPath } = useScan();
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [quantumFilter, setQuantumFilter] = useState('all');
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');

  if (!scanResponse) {
    return (
      <div className="space-y-6">
        <SectionHeader
          title="Analysis Results & Security Report"
          subtitle="Comprehensive cryptographic asset inventory, evidence, and post-quantum readiness."
        />
        <EmptyState
          title="No Active Analysis Results"
          description="Initiate a scan from the Dashboard to view cryptographic discovery findings and risk analysis."
          action={
            <Button variant="primary" size="sm" onClick={() => navigate('/')}>
              Go to Dashboard & Scan
            </Button>
          }
        />
      </div>
    );
  }

  const findings = scanResponse.findings || [];

  // Filtered Findings
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

  return (
    <div className="space-y-8">
      {/* 1. What Did We Analyze? */}
      <div className="space-y-3">
        <SectionHeader
          title="Cryptographic Security Analysis Results"
          subtitle="Completed static discovery scan and post-quantum risk assessment."
          action={
            <Button variant="outline" size="sm" onClick={() => navigate('/')}>
              Configure New Scan
            </Button>
          }
        />
        <AnalysisSummaryCard
          targetPath={targetPath}
          summary={scanResponse.summary}
          metadata={scanResponse.metadata}
        />
      </div>

      {/* 2. What Cryptographic Usage Was Discovered? */}
      <div className="space-y-4">
        <h3 className="text-base font-bold text-slate-100 tracking-tight flex items-center gap-2">
          <ShieldIcon className="w-5 h-5 text-indigo-400" />
          Discovery Overview & Risk Profile
        </h3>
        <OverviewMetrics summary={scanResponse.summary} metadata={scanResponse.metadata} />
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <SeverityBreakdown summary={scanResponse.summary} />
          <TopAlgorithmsList algorithmDistribution={scanResponse.summary.algorithm_distribution} />
        </div>
      </div>

      {/* 3 & 4 & 5. What Requires Attention? Evidence & Findings Inspection */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <h3 className="text-base font-bold text-slate-100 tracking-tight flex items-center gap-2">
            <QuantumIcon className="w-5 h-5 text-purple-400" />
            Cryptographic Assets & Evidence Inventory ({filteredFindings.length})
          </h3>

          {/* View Mode Switcher */}
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 p-1 rounded-lg self-start sm:self-auto">
            <button
              onClick={() => setViewMode('table')}
              className={`px-2.5 py-1 text-xs font-mono rounded cursor-pointer ${
                viewMode === 'table' ? 'bg-slate-800 text-slate-100 font-bold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Table View
            </button>
            <button
              onClick={() => setViewMode('cards')}
              className={`px-2.5 py-1 text-xs font-mono rounded cursor-pointer ${
                viewMode === 'cards' ? 'bg-slate-800 text-slate-100 font-bold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Card View
            </button>
          </div>
        </div>

        {/* Filter Controls Bar */}
        <Card>
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                <SearchIcon className="w-4 h-4" />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by algorithm, path, rule ID, or code snippet..."
                className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

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

              <select
                value={quantumFilter}
                onChange={(e) => setQuantumFilter(e.target.value)}
                className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500"
              >
                <option value="all">All Quantum Threats</option>
                <option value="shor">Shor Threat</option>
                <option value="grover">Grover Threat</option>
                <option value="none">Quantum Safe</option>
              </select>
            </div>
          </div>
        </Card>

        {/* View Mode: Card Grid vs Desktop Table */}
        {filteredFindings.length === 0 ? (
          <EmptyState
            title="No Matching Cryptographic Findings"
            description="No assets match your active search filters."
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
        ) : viewMode === 'cards' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredFindings.map((finding) => (
              <FindingCard key={finding.finding_id} finding={finding} onInspect={setSelectedFinding} />
            ))}
          </div>
        ) : (
          <Card className="overflow-hidden p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-950 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                    <th className="py-3 px-4">Severity</th>
                    <th className="py-3 px-4">Algorithm</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Location</th>
                    <th className="py-3 px-4">Quantum Threat</th>
                    <th className="py-3 px-4 text-right">Evidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-sans">
                  {filteredFindings.map((finding) => (
                    <tr
                      key={finding.finding_id}
                      onClick={() => setSelectedFinding(finding)}
                      className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                    >
                      <td className="py-3 px-4">
                        <Badge variant="severity" severity={finding.risk.severity as any}>
                          {finding.risk.severity}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-slate-100">
                        {finding.algorithm}
                        {finding.key_length && (
                          <span className="text-[10px] text-slate-400 font-normal ml-1">({finding.key_length}b)</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-300 font-mono text-[11px]">{finding.category}</td>
                      <td className="py-3 px-4 font-mono text-indigo-300">
                        {finding.file_location.file_path}:{finding.file_location.line_number}
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant="quantum" quantumThreat={finding.risk.quantum_threat as any}>
                          {finding.risk.quantum_threat}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className="text-indigo-400 hover:text-indigo-300 text-xs font-mono">
                          Inspect &rarr;
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>

      {/* 6. What Should the Organization Do Next? */}
      <div className="space-y-4">
        <h3 className="text-base font-bold text-slate-100 tracking-tight">
          Next Steps & PQC Remediation Roadmap
        </h3>
        <RemediationPlanCard findings={findings} onSelectFinding={setSelectedFinding} />
      </div>

      {/* Detail Drawer for Inspecting Technical Evidence */}
      <FindingDetailDrawer finding={selectedFinding} onClose={() => setSelectedFinding(null)} />
    </div>
  );
}
