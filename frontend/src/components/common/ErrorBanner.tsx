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
    <div className={`border border-[#FF3B30]/40 bg-[#FF3B30]/10 rounded-xl p-4 text-left flex items-start justify-between gap-4 ${className}`}>
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-[#FF3B30]/20 border border-[#FF3B30]/40 text-[#FF3B30] shrink-0 mt-0.5">
          <AlertIcon className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold text-[#F5F7FA]">Scan Failure</h4>
            <span className="bg-[#FF3B30]/20 border border-[#FF3B30]/40 text-[#FF3B30] font-mono text-[10px] px-1.5 py-0.5 rounded uppercase">
              {errorCode} {statusCode ? `(${statusCode})` : ''}
            </span>
          </div>
          <p className="text-xs text-[#A3ADBF] mt-1 leading-relaxed">{error.message}</p>
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
