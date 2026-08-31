import React from 'react';
import { AlertIcon, RefreshIcon } from './Icons';
import { ApiError } from '../../api/client';
import { Button } from './Button';

interface ErrorBannerProps {
  error: ApiError | Error;
  onRetry?: () => void;
  className?: string;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ error, onRetry, className = '' }) => {
  const isApiErr = error instanceof ApiError;
  const errorCode = isApiErr ? error.code : 'CLIENT_ERROR';
  const statusCode = isApiErr ? error.status : null;

  return (
    <div className={`border border-red-900/60 bg-red-950/30 rounded-xl p-4 text-left flex items-start justify-between gap-4 ${className}`}>
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-red-900/40 border border-red-800/60 text-red-400 shrink-0 mt-0.5">
          <AlertIcon className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold text-red-200">Scan Failure</h4>
            <span className="bg-red-900/80 border border-red-800 text-red-300 font-mono text-[10px] px-1.5 py-0.5 rounded uppercase">
              {errorCode} {statusCode ? `(${statusCode})` : ''}
            </span>
          </div>
          <p className="text-xs text-red-300/80 mt-1 leading-relaxed">{error.message}</p>
        </div>
      </div>
      {onRetry && (
        <Button variant="danger" size="sm" onClick={onRetry} leftIcon={<RefreshIcon className="w-3.5 h-3.5" />}>
          Retry
        </Button>
      )}
    </div>
  );
};
