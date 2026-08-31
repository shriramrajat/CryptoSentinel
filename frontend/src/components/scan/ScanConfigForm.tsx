import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useScan } from '../../context/ScanContext';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { FolderIcon, SearchIcon, CodeIcon } from '../common/Icons';

export const ScanConfigForm: React.FC = () => {
  const {
    targetPath,
    setTargetPath,
    languageFilters,
    setLanguageFilters,
    executeScan,
    isScanning,
  } = useScan();

  const navigate = useNavigate();
  const [validationError, setValidationError] = useState<string | null>(null);

  const availableLanguages = [
    { id: 'python', label: 'Python (.py)' },
    { id: 'java', label: 'Java (.java)' },
    { id: 'c', label: 'C (.c, .h)' },
    { id: 'cpp', label: 'C++ (.cpp, .hpp)' },
    { id: 'pem', label: 'PEM Keys & Certs' },
  ];

  const handleLanguageToggle = (id: string) => {
    if (languageFilters.includes(id)) {
      setLanguageFilters(languageFilters.filter((l) => l !== id));
    } else {
      setLanguageFilters([...languageFilters, id]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetPath.trim()) {
      setValidationError('Please enter a target path to scan (e.g. absolute folder path or test fixture).');
      return;
    }
    setValidationError(null);
    await executeScan();
    navigate('/results');
  };

  const handleSampleSelect = (samplePath: string) => {
    setTargetPath(samplePath);
    setValidationError(null);
  };

  return (
    <Card
      header={
        <div className="flex items-center gap-2">
          <FolderIcon className="w-5 h-5 text-[#00E5FF]" />
          <h3 className="font-bold text-[#F5F7FA] text-sm tracking-wide">Scan Target Configuration</h3>
        </div>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Target Path Input */}
        <div>
          <label htmlFor="target_path" className="block text-xs font-semibold text-[#A3ADBF] uppercase tracking-wider mb-1.5">
            Local Target Directory / File Path <span className="text-[#FF3B30]">*</span>
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#A3ADBF]">
              <FolderIcon className="w-4 h-4" />
            </div>
            <input
              id="target_path"
              type="text"
              value={targetPath}
              onChange={(e) => {
                setTargetPath(e.target.value);
                if (validationError) setValidationError(null);
              }}
              placeholder="e.g. C:\Users\ROHAN\Desktop\CryptoSentinel\tests\fixtures"
              className="w-full pl-10 pr-4 py-2.5 bg-[#070B14] border border-[#232B3D] rounded-lg text-sm text-[#F5F7FA] placeholder-[#A3ADBF]/60 font-mono focus:outline-none focus:border-[#00E5FF] focus:ring-1 focus:ring-[#00E5FF] transition-colors"
              disabled={isScanning}
            />
          </div>
          {validationError && (
            <p className="text-xs text-[#FF3B30] mt-1.5 font-medium">{validationError}</p>
          )}
        </div>

        {/* Quick Sample Path Helpers */}
        <div>
          <span className="text-[11px] font-semibold text-[#A3ADBF] uppercase tracking-wider block mb-1.5">
            Quick Test Shortcuts:
          </span>
          <div className="flex flex-wrap gap-2 text-xs font-mono">
            <button
              type="button"
              onClick={() => handleSampleSelect('tests/fixtures')}
              className="px-2.5 py-1 rounded bg-[#171E2E] hover:bg-[#171E2E]/80 text-[#00E5FF] border border-[#232B3D] focus:ring-1 focus:ring-[#00E5FF] transition-colors cursor-pointer"
            >
              tests/fixtures
            </button>
            <button
              type="button"
              onClick={() => handleSampleSelect('src')}
              className="px-2.5 py-1 rounded bg-[#171E2E] hover:bg-[#171E2E]/80 text-[#00E5FF] border border-[#232B3D] focus:ring-1 focus:ring-[#00E5FF] transition-colors cursor-pointer"
            >
              src
            </button>
          </div>
        </div>

        {/* Language Filters Selection */}
        <div>
          <label className="block text-xs font-semibold text-[#A3ADBF] uppercase tracking-wider mb-2">
            Language Scope Filters <span className="text-[#A3ADBF]/70 font-normal">(Optional — defaults to all)</span>
          </label>
          <div className="flex flex-wrap gap-2">
            {availableLanguages.map((lang) => {
              const selected = languageFilters.includes(lang.id);
              return (
                <button
                  key={lang.id}
                  type="button"
                  onClick={() => handleLanguageToggle(lang.id)}
                  disabled={isScanning}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all cursor-pointer flex items-center gap-1.5 focus:ring-1 focus:ring-[#00E5FF] ${
                    selected
                      ? 'bg-[#00E5FF]/10 text-[#00E5FF] border-[#00E5FF]/40 shadow-sm'
                      : 'bg-[#070B14] text-[#A3ADBF] border-[#232B3D] hover:border-[#00E5FF]/30 hover:text-[#F5F7FA]'
                  }`}
                >
                  <CodeIcon className="w-3.5 h-3.5" />
                  <span>{lang.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Action Controls */}
        <div className="pt-2 flex items-center justify-between">
          <Button
            type="submit"
            variant="primary"
            size="md"
            isLoading={isScanning}
            leftIcon={<SearchIcon className="w-4 h-4" />}
            className="w-full sm:w-auto"
          >
            {isScanning ? 'Executing Static Analysis...' : 'Initiate Cryptographic Scan'}
          </Button>
          {targetPath && !isScanning && (
            <button
              type="button"
              onClick={() => setTargetPath('')}
              className="text-xs text-[#A3ADBF] hover:text-[#F5F7FA] transition-colors focus:ring-1 focus:ring-[#00E5FF] rounded px-1"
            >
              Reset Input
            </button>
          )}
        </div>
      </form>
    </Card>
  );
};
