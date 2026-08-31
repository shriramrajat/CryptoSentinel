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
          <FolderIcon className="w-5 h-5 text-indigo-400" />
          <h3 className="font-bold text-slate-100 text-sm tracking-wide">Scan Target Configuration</h3>
        </div>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Target Path Input */}
        <div>
          <label htmlFor="target_path" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
            Local Target Directory / File Path <span className="text-red-400">*</span>
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
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
              className="w-full pl-10 pr-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 font-mono focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
              disabled={isScanning}
            />
          </div>
          {validationError && (
            <p className="text-xs text-red-400 mt-1.5 font-medium">{validationError}</p>
          )}
        </div>

        {/* Quick Sample Path Helpers */}
        <div>
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1.5">
            Quick Test Shortcuts:
          </span>
          <div className="flex flex-wrap gap-2 text-xs font-mono">
            <button
              type="button"
              onClick={() => handleSampleSelect('tests/fixtures')}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-slate-700 transition-colors cursor-pointer"
            >
              tests/fixtures
            </button>
            <button
              type="button"
              onClick={() => handleSampleSelect('src')}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-slate-700 transition-colors cursor-pointer"
            >
              src
            </button>
          </div>
        </div>

        {/* Language Filters Selection */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            Language Scope Filters <span className="text-slate-500 font-normal">(Optional — defaults to all)</span>
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
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all cursor-pointer flex items-center gap-1.5 ${
                    selected
                      ? 'bg-indigo-950 text-indigo-200 border-indigo-600 shadow-sm'
                      : 'bg-slate-950 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200'
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
              className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
            >
              Reset Input
            </button>
          )}
        </div>
      </form>
    </Card>
  );
};
