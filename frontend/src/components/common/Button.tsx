import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost' | 'quantum';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center justify-center font-medium rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#070B14] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer';

  const sizeStyles = {
    sm: 'px-3 py-1.5 text-xs gap-1.5',
    md: 'px-4 py-2 text-sm gap-2',
    lg: 'px-5 py-2.5 text-base gap-2.5',
  };

  const variantStyles = {
    primary:
      'bg-[#00E5FF] hover:bg-[#00B8D4] text-[#070B14] font-semibold border border-[#00E5FF] shadow-sm hover:shadow-[#00E5FF]/20 focus:ring-[#00E5FF]',
    secondary:
      'bg-[#171E2E] hover:bg-[#171E2E]/80 text-[#F5F7FA] border border-[#232B3D] hover:border-[#00E5FF]/50 focus:ring-[#00E5FF]',
    outline:
      'bg-transparent hover:bg-[#171E2E] text-[#F5F7FA] border border-[#232B3D] hover:border-[#00E5FF]/40 focus:ring-[#00E5FF]',
    danger:
      'bg-[#FF3B30] hover:bg-[#FF3B30]/90 text-white border border-[#FF3B30] focus:ring-[#FF3B30]',
    quantum:
      'bg-[#7C3AED] hover:bg-[#7C3AED]/90 text-white border border-[#7C3AED] focus:ring-[#7C3AED]',
    ghost:
      'bg-transparent hover:bg-[#171E2E]/60 text-[#A3ADBF] hover:text-[#F5F7FA] focus:ring-[#00E5FF]',
  };

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <svg
          className="animate-spin h-4 w-4 text-current"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      ) : (
        leftIcon
      )}
      <span>{children}</span>
      {!isLoading && rightIcon}
    </button>
  );
};
