import React from 'react';
import { Layers, Activity, GitBranch, ShieldCheck, BarChart3, Database } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isLive: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, isLive }) => {
  const tabs = [
    { id: 'overview', label: 'Overview & Sales', icon: Layers },
    { id: 'pipelines', label: 'Automated Pipelines', icon: GitBranch },
    { id: 'streaming', label: 'Live Streaming', icon: Activity },
    { id: 'quality', label: 'Data Quality & Checks', icon: ShieldCheck },
    { id: 'analytics', label: 'Analytics & Reports', icon: BarChart3 },
  ];

  return (
    <header className="border-b border-slate-200 bg-white/95 backdrop-blur-md sticky top-0 z-50 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 border-b border-slate-100">
          <div className="flex items-center space-x-3.5">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-600 to-blue-600 p-[1px] shadow-sm flex items-center justify-center">
              <div className="w-full h-full bg-white rounded-[7px] flex items-center justify-center">
                <Database className="w-5 h-5 text-indigo-600" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-base tracking-tight text-slate-900">
                  E-Commerce Data Intelligence
                </span>
                <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Live System
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">
                Real-time transactional analytics and automated data processing
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="flex items-center px-3 py-1 rounded-full text-xs bg-slate-50 text-slate-700 border border-slate-200 font-medium">
              <span className={`w-2 h-2 rounded-full mr-2 ${isLive ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
              {isLive ? 'Analytics Engine Connected' : 'Connecting to Server...'}
            </div>
          </div>
        </div>

        {/* Intuitive Tab Navigation Bar */}
        <nav className="flex space-x-1 sm:space-x-2 overflow-x-auto py-2.5">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-md text-xs font-semibold transition-all duration-150 whitespace-nowrap ${
                  isActive
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-500'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
