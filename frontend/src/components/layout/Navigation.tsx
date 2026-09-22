import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { ShieldIcon, SearchIcon, QuantumIcon, CpuIcon, MenuIcon, XIcon, FileTextIcon } from '../common/Icons';
import { useScan } from '../../context/ScanContext';

export const Navigation: React.FC = () => {
  const { scanResponse } = useScan();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const findingsCount = scanResponse?.summary?.total_crypto_assets || 0;
  const quantumCount = scanResponse?.summary?.quantum_vulnerable_assets || 0;
  const warningsCount = (scanResponse?.skipped_files?.length || 0) + (scanResponse?.errors?.length || 0);

  const navItems = [
    {
      to: '/',
      label: 'Dashboard & Scan',
      icon: <ShieldIcon className="w-4 h-4" />,
      badge: null,
    },
    {
      to: '/results',
      label: 'Analysis Results',
      icon: <FileTextIcon className="w-4 h-4" />,
      badge: findingsCount > 0 ? findingsCount : null,
      badgeColor: 'bg-[#00FFA3]/10 text-[#00FFA3] border-[#00FFA3]/30',
    },
    {
      to: '/findings',
      label: 'Cryptographic Inventory',
      icon: <SearchIcon className="w-4 h-4" />,
      badge: findingsCount > 0 ? findingsCount : null,
      badgeColor: 'bg-[#00E5FF]/10 text-[#00E5FF] border-[#00E5FF]/30',
    },
    {
      to: '/quantum',
      label: 'Quantum & PQC Readiness',
      icon: <QuantumIcon className="w-4 h-4" />,
      badge: quantumCount > 0 ? quantumCount : null,
      badgeColor: 'bg-[#7C3AED]/20 text-[#7C3AED] border-[#7C3AED]/40',
    },
    {
      to: '/migration',
      label: 'PQC Migration Intelligence',
      icon: <ShieldIcon className="w-4 h-4" />,
      badge: findingsCount > 0 ? findingsCount : null,
      badgeColor: 'bg-[#00E5FF]/20 text-[#00E5FF] border-[#00E5FF]/40',
    },
    {
      to: '/enterprise-inventory',
      label: 'Enterprise Inventory',
      icon: <ShieldIcon className="w-4 h-4" />,
      badge: 'P4',
      badgeColor: 'bg-[#7C3AED]/20 text-[#7C3AED] border-[#7C3AED]/40',
    },
    {
      to: '/discovery',
      label: 'Advanced Discovery',
      icon: <SearchIcon className="w-4 h-4" />,
      badge: null,
      badgeColor: 'bg-[#00E5FF]/20 text-[#00E5FF] border-[#00E5FF]/40',
    },
    {
      to: '/diagnostics',
      label: 'Diagnostics',
      icon: <CpuIcon className="w-4 h-4" />,
      badge: warningsCount > 0 ? warningsCount : null,
      badgeColor: 'bg-[#FF8A00]/10 text-[#FF8A00] border-[#FF8A00]/30',
    },
  ];

  return (
    <nav className="bg-[#0F1523]/80 border-b border-[#232B3D]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Desktop Navigation */}
        <div className="hidden md:flex space-x-1 py-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-[#171E2E] text-[#00E5FF] border border-[#00E5FF]/40 shadow-sm'
                    : 'text-[#A3ADBF] hover:text-[#F5F7FA] hover:bg-[#171E2E]/50'
                }`
              }
            >
              {item.icon}
              <span>{item.label}</span>
              {item.badge !== null && (
                <span
                  className={`text-[11px] font-mono font-semibold px-2 py-0.2 rounded-full border ${item.badgeColor}`}
                >
                  {item.badge}
                </span>
              )}
            </NavLink>
          ))}
        </div>

        {/* Mobile Navigation Bar */}
        <div className="flex md:hidden items-center justify-between py-3">
          <span className="text-xs font-semibold text-[#A3ADBF] uppercase tracking-wider">Navigation</span>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-lg bg-[#171E2E] text-[#F5F7FA] border border-[#232B3D] focus:outline-none focus:ring-2 focus:ring-[#00E5FF]"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <XIcon className="w-5 h-5" /> : <MenuIcon className="w-5 h-5" />}
          </button>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden py-3 border-t border-[#232B3D] flex flex-col space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  `flex items-center justify-between px-4 py-2.5 rounded-lg text-sm font-medium ${
                    isActive
                      ? 'bg-[#171E2E] text-[#00E5FF] border border-[#00E5FF]/40'
                      : 'text-[#A3ADBF] hover:text-[#F5F7FA] hover:bg-[#171E2E]/40'
                  }`
                }
              >
                <div className="flex items-center gap-2">
                  {item.icon}
                  <span>{item.label}</span>
                </div>
                {item.badge !== null && (
                  <span
                    className={`text-[11px] font-mono font-semibold px-2 py-0.2 rounded-full border ${item.badgeColor}`}
                  >
                    {item.badge}
                  </span>
                )}
              </NavLink>
            ))}
          </div>
        )}
      </div>
    </nav>
  );
};
