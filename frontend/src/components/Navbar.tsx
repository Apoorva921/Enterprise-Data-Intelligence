import React from 'react';
import { Layers, Activity, GitBranch, ShieldCheck, BarChart3, Database } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isLive: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, isLive }) => {
  const tabs = [
    { id: 'overview', label: 'Executive Overview', icon: Layers },
    { id: 'pipelines', label: 'Pipeline Orchestration', icon: GitBranch },
    { id: 'streaming', label: 'Kafka Streaming & DLQ', icon: Activity },
    { id: 'quality', label: 'Data Quality & Quarantine', icon: ShieldCheck },
    { id: 'analytics', label: 'Business Intelligence', icon: BarChart3 },
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-tr from-blue-600 to-indigo-500 rounded-lg shadow-md shadow-blue-500/20">
              <Database className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg text-white tracking-tight">Enterprise Data Intelligence</span>
              <span className="ml-2 text-xs font-mono uppercase px-2 py-0.5 rounded bg-blue-900/50 text-blue-400 border border-blue-700/50">
                v1.0 Medallion
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <div className="flex items-center mr-4 px-3 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
              <span className={`w-2 h-2 rounded-full mr-2 ${isLive ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              {isLive ? 'Connected to FastAPI' : 'Connecting...'}
            </div>
          </div>
        </div>

        {/* Tab navigation */}
        <nav className="flex space-x-1 sm:space-x-4 overflow-x-auto py-2">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};

