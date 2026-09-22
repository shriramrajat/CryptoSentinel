import React, { createContext, useContext, useState } from 'react';
import type { ScanResponse, ScanRequest } from '../types/api';
import { scanApi, ApiError } from '../api/client';

interface ScanContextType {
  scanResponse: ScanResponse | null;
  isScanning: boolean;
  scanError: ApiError | Error | null;
  targetPath: string;
  setTargetPath: (path: string) => void;
  languageFilters: string[];
  setLanguageFilters: (filters: string[]) => void;
  executeScan: (pathOverride?: string) => Promise<void>;
  clearScan: () => void;
  backendOnline: boolean | null;
  checkHealth: () => Promise<void>;
}

const ScanContext = createContext<ScanContextType | undefined>(undefined);

export const ScanProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [scanResponse, setScanResponse] = useState<ScanResponse | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [scanError, setScanError] = useState<ApiError | Error | null>(null);
  const [targetPath, setTargetPath] = useState('');
  const [languageFilters, setLanguageFilters] = useState<string[]>([]);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  React.useEffect(() => {
    checkHealth();
    restoreLatestScan();
  }, []);

  const restoreLatestScan = async () => {
    try {
      const res = await scanApi.getLatestScan();
      if (res.status === 'ok' && res.scan && !isScanning) {
        setScanResponse(res.scan);
        if (res.scan.target_path) {
          setTargetPath(res.scan.target_path);
        }
      }
    } catch {
      // Quietly ignore restore errors
    }
  };

  const checkHealth = async () => {
    try {
      const res = await scanApi.getHealth();
      setBackendOnline(res.status === 'ok');
    } catch {
      setBackendOnline(false);
    }
  };


  const executeScan = async (pathOverride?: string) => {
    const path = (pathOverride !== undefined ? pathOverride : targetPath).trim();
    if (!path) {
      setScanError(new Error('Please enter a valid directory path to scan.'));
      setScanResponse(null);
      return;
    }

    setIsScanning(true);
    setScanError(null);
    setScanResponse(null);

    const req: ScanRequest = {
      target_path: path,
      language_filters: languageFilters.length > 0 ? languageFilters : null,
    };

    try {
      const response = await scanApi.runScan(req);
      setScanResponse(response);
      setBackendOnline(true);
    } catch (err: any) {
      setScanError(err);
      setScanResponse(null);
      if (err instanceof ApiError && err.status === 0) {
        setBackendOnline(false);
      }
    } finally {
      setIsScanning(false);
    }
  };


  const clearScan = () => {
    setScanResponse(null);
    setScanError(null);
  };

  return (
    <ScanContext.Provider
      value={{
        scanResponse,
        isScanning,
        scanError,
        targetPath,
        setTargetPath,
        languageFilters,
        setLanguageFilters,
        executeScan,
        clearScan,
        backendOnline,
        checkHealth,
      }}
    >
      {children}
    </ScanContext.Provider>
  );
};

export const useScan = () => {
  const context = useContext(ScanContext);
  if (!context) {
    throw new Error('useScan must be used within a ScanProvider');
  }
  return context;
};
