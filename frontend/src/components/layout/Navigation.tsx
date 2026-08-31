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
      badgeColor: 'bg-emerald-950 text-emerald-300 border-emerald-800',
    },
    {
      to: '/findings',
      label: 'Cryptographic Inventory',
      icon: <SearchIcon className="w-4 h-4" />,
      badge: findingsCount > 0 ? findingsCount : null,
      badgeColor: 'bg-indigo-950 text-indigo-300 border-indigo-800',
    },
    {
      to: '/quantum',
      label: 'Quantum & PQC Readiness',
      icon: <QuantumIcon className="w-4 h-4" />,
      badge: quantumCount > 0 ? quantumCount : null,
      badgeColor: 'bg-purple-950 text-purple-300 border-purple-800',
    },
    {
      to: '/diagnostics',
      label: 'Diagnostics',
      icon: <CpuIcon className="w-4 h-4" />,
      badge: warningsCount > 0 ? warningsCount : null,
      badgeColor: 'bg-amber-950 text-amber-300 border-amber-800',
    },
  ];

  return (
    <nav className="bg-slate-900/80 border-b border-slate-800/80">
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
                    ? 'bg-slate-800 text-slate-100 border border-slate-700 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
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
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Navigation</span>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-lg bg-slate-800 text-slate-300 border border-slate-700 focus:outline-none"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <XIcon className="w-5 h-5" /> : <MenuIcon className="w-5 h-5" />}
          </button>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden py-3 border-t border-slate-800 flex flex-col space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  `flex items-center justify-between px-4 py-2.5 rounded-lg text-sm font-medium ${
                    isActive
                      ? 'bg-slate-800 text-slate-100 border border-slate-700'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
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
