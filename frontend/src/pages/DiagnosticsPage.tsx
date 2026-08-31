import { useNavigate } from 'react-router-dom';
import { useScan } from '../context/ScanContext';
import { SectionHeader } from '../components/common/SectionHeader';
import { Card } from '../components/common/Card';
import { EmptyState } from '../components/common/EmptyState';
import { Button } from '../components/common/Button';
import { CpuIcon, CheckIcon, AlertIcon, ClockIcon } from '../components/common/Icons';

export default function DiagnosticsPage() {
  const { scanResponse } = useScan();
  const navigate = useNavigate();

  const skippedFiles = scanResponse?.skipped_files || [];
  const errors = scanResponse?.errors || [];
  const metadata = scanResponse?.metadata;
  const summary = scanResponse?.summary;

  if (!scanResponse) {
    return (
      <div className="space-y-6">
        <SectionHeader
          title="Scan Execution Diagnostics & Logs"
          subtitle="Audit trail for skipped files, engine exceptions, file discovery counts, and performance."
        />
        <EmptyState
          title="No Diagnostics Log Loaded"
          description="Initiate a scan on the Dashboard to inspect file discovery metrics and engine diagnostics."
          action={
            <Button variant="primary" size="sm" onClick={() => navigate('/')}>
              Initiate Scan
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Scan Execution Diagnostics & Logs"
        subtitle="Transparency audit trail for scanner file traversal, skipped files, and execution exceptions."
        badge={
          <span className="bg-slate-800 text-slate-300 border border-slate-700 text-xs font-mono px-2.5 py-0.5 rounded-full flex items-center gap-1.5">
            <CpuIcon className="w-3.5 h-3.5" />
            Scanner v{metadata?.scanner_version}
          </span>
        }
      />

      {/* Engine Diagnostics Stats Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center justify-between text-xs text-slate-400 font-semibold uppercase">
            <span>Files Discovered</span>
            <CpuIcon className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-xl font-bold font-mono text-slate-100 mt-2">{summary?.total_files_discovered}</div>
          <p className="text-xs text-slate-500 mt-1">Recursive traversal count</p>
        </Card>

        <Card>
          <div className="flex items-center justify-between text-xs text-slate-400 font-semibold uppercase">
            <span>Files Scanned</span>
            <CheckIcon className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold font-mono text-slate-100 mt-2">{summary?.total_files_scanned}</div>
          <p className="text-xs text-slate-500 mt-1">Comment stripped & parsed</p>
        </Card>

        <Card>
          <div className="flex items-center justify-between text-xs text-slate-400 font-semibold uppercase">
            <span>Skipped Files</span>
            <AlertIcon className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-xl font-bold font-mono text-slate-100 mt-2">{summary?.files_skipped}</div>
          <p className="text-xs text-slate-500 mt-1">Oversized (&gt;10MB) or excluded</p>
        </Card>

        <Card>
          <div className="flex items-center justify-between text-xs text-slate-400 font-semibold uppercase">
            <span>Execution Duration</span>
            <ClockIcon className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-xl font-bold font-mono text-slate-100 mt-2">{metadata?.scan_duration_ms} ms</div>
          <p className="text-xs text-slate-500 mt-1">Static traversal time</p>
        </Card>
      </div>

      {/* Skipped Files Table */}
      <Card
        header={
          <div className="flex items-center justify-between w-full">
            <h3 className="font-bold text-slate-100 text-sm tracking-wide">Skipped Files Log ({skippedFiles.length})</h3>
            {skippedFiles.length > 0 && (
              <span className="bg-amber-950 text-amber-300 border border-amber-800 text-[11px] font-mono px-2 py-0.5 rounded">
                Oversized Threshold Exceeded
              </span>
            )}
          </div>
        }
      >
        {skippedFiles.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-2">No files were skipped during this scan.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase font-semibold">
                  <th className="py-2.5 px-3">File Path</th>
                  <th className="py-2.5 px-3">Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {skippedFiles.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30">
                    <td className="py-2.5 px-3 text-indigo-300">{item.file}</td>
                    <td className="py-2.5 px-3">
                      <span className="bg-amber-950 text-amber-300 border border-amber-800 text-[10px] px-1.5 py-0.5 rounded uppercase">
                        {item.reason}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Engine Errors Log */}
      <Card
        header={
          <h3 className="font-bold text-slate-100 text-sm tracking-wide">Scanner Errors Log ({errors.length})</h3>
        }
      >
        {errors.length === 0 ? (
          <div className="flex items-center gap-2 text-xs text-emerald-400 py-2">
            <CheckIcon className="w-4 h-4" />
            <span>Zero engine execution exceptions recorded during scan.</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase font-semibold">
                  <th className="py-2.5 px-3">Target File</th>
                  <th className="py-2.5 px-3">Exception Detail</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {errors.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30">
                    <td className="py-2.5 px-3 text-red-300">{item.file}</td>
                    <td className="py-2.5 px-3 text-red-400/90">{item.error}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
