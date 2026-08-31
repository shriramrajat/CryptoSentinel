import { useNavigate } from 'react-router-dom';
import { useScan } from '../context/ScanContext';
import { ScanConfigForm } from '../components/scan/ScanConfigForm';
import { OverviewMetrics } from '../components/dashboard/OverviewMetrics';
import { SeverityBreakdown } from '../components/dashboard/SeverityBreakdown';
import { TopAlgorithmsList } from '../components/dashboard/TopAlgorithmsList';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { EmptyState } from '../components/common/EmptyState';
import { SectionHeader } from '../components/common/SectionHeader';
import { Button } from '../components/common/Button';
import { ShieldIcon, QuantumIcon, SearchIcon, ChevronRightIcon, CodeIcon } from '../components/common/Icons';

export default function Home() {
  const { scanResponse, isScanning, scanError, executeScan } = useScan();
  const navigate = useNavigate();

  return (
    <div className="space-y-8">
      {/* Intro Hero / Capabilities Overview Header */}
      <div className="bg-[#0F1523] border border-[#232B3D] rounded-xl p-6 sm:p-8 relative overflow-hidden">
        <div className="max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#00E5FF]/10 border border-[#00E5FF]/30 text-[#00E5FF] text-xs font-mono font-medium">
            <ShieldIcon className="w-3.5 h-3.5 text-[#00E5FF]" />
            Static Cryptographic Discovery Engine
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#F5F7FA] tracking-tight">
            Cryptographic Inventory & Post-Quantum Risk Analysis
          </h1>
          <p className="text-sm text-[#A3ADBF] leading-relaxed">
            CryptoSentinel recursively scans Python (AST + regex), Java, C/C++, and PEM certificate files to build a precise inventory of cryptographic primitives, key lengths, cipher modes, and NIST PQC migration targets.
          </p>
        </div>

        {/* Technical Features Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6 pt-6 border-t border-[#232B3D] text-xs">
          <div className="flex items-start gap-2.5">
            <div className="p-1.5 rounded bg-[#171E2E] text-[#00E5FF] border border-[#232B3D] shrink-0">
              <CodeIcon className="w-4 h-4" />
            </div>
            <div>
              <span className="font-semibold text-[#F5F7FA] block">AST & Regex Parsing</span>
              <span className="text-[#A3ADBF]">Context-aware comment filtering & Python AST call graph detection.</span>
            </div>
          </div>
          <div className="flex items-start gap-2.5">
            <div className="p-1.5 rounded bg-[#171E2E] text-[#7C3AED] border border-[#232B3D] shrink-0">
              <QuantumIcon className="w-4 h-4" />
            </div>
            <div>
              <span className="font-semibold text-[#F5F7FA] block">Post-Quantum Audit</span>
              <span className="text-[#A3ADBF]">Evaluates Shor's & Grover's threats against FIPS 203 & 204 standards.</span>
            </div>
          </div>
          <div className="flex items-start gap-2.5">
            <div className="p-1.5 rounded bg-[#171E2E] text-[#00FFA3] border border-[#232B3D] shrink-0">
              <ShieldIcon className="w-4 h-4" />
            </div>
            <div>
              <span className="font-semibold text-[#F5F7FA] block">Deterministic Evidence</span>
              <span className="text-[#A3ADBF]">SHA-256 asset IDs, repo-relative paths, and code snippets.</span>
            </div>
          </div>
        </div>
      </div>

      {/* Target Scan Configuration Form */}
      <ScanConfigForm />

      {/* Error Display */}
      {scanError && <ErrorBanner error={scanError} onRetry={() => executeScan()} />}

      {/* Active Scan Loading State */}
      {isScanning && <LoadingState />}

      {/* Scan Results Display */}
      {!isScanning && scanResponse && (
        <div className="space-y-6">
          <SectionHeader
            title="Scan Executive Summary"
            subtitle={`Analyzed ${scanResponse.summary.total_files_scanned} files in ${scanResponse.metadata.scan_duration_ms}ms.`}
            action={
              <Button
                variant="primary"
                size="sm"
                onClick={() => navigate('/findings')}
                rightIcon={<ChevronRightIcon className="w-4 h-4" />}
              >
                Inspect All {scanResponse.summary.total_crypto_assets} Findings
              </Button>
            }
          />

          {/* Overview Metrics Cards */}
          <OverviewMetrics summary={scanResponse.summary} metadata={scanResponse.metadata} />

          {/* Distribution Split Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <SeverityBreakdown summary={scanResponse.summary} />
            <TopAlgorithmsList algorithmDistribution={scanResponse.summary.algorithm_distribution} />
          </div>
        </div>
      )}

      {/* Empty State before any scan executed */}
      {!isScanning && !scanResponse && !scanError && (
        <EmptyState
          title="No Active Cryptographic Scan Loaded"
          description="Specify a repository directory or test path above (e.g. tests/fixtures) to execute a static discovery scan."
          action={
            <Button
              variant="outline"
              size="sm"
              onClick={() => executeScan('tests/fixtures')}
              leftIcon={<SearchIcon className="w-4 h-4" />}
            >
              Run Fixtures Demo Scan
            </Button>
          }
        />
      )}
    </div>
  );
}
