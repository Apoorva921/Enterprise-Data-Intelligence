import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { OverviewTab } from './components/OverviewTab';
import { PipelinesTab } from './components/PipelinesTab';
import { StreamingTab } from './components/StreamingTab';
import { DataQualityTab } from './components/DataQualityTab';
import { AnalyticsTab } from './components/AnalyticsTab';
import { fetchHealth } from './services/api';

export function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [isLive, setIsLive] = useState(false);

  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await fetchHealth();
        setIsLive(res.status === 'UP');
      } catch {
        setIsLive(false);
      }
    }
    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#f8fafc] bg-grid-pattern text-slate-900 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} isLive={isLive} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && <OverviewTab />}
        {activeTab === 'pipelines' && <PipelinesTab />}
        {activeTab === 'streaming' && <StreamingTab />}
        {activeTab === 'quality' && <DataQualityTab />}
        {activeTab === 'analytics' && <AnalyticsTab />}
      </main>

      <footer className="border-t border-slate-200 bg-white py-4 px-6 shadow-xs">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] font-mono text-slate-600">
          <div className="flex items-center space-x-3">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-500"></span>
            <span className="font-semibold text-slate-800">DATA LAKEHOUSE CLUSTER: PRODUCTION</span>
            <span className="text-slate-300">|</span>
            <span>ENGINE: DUCKDB / BIGQUERY</span>
            <span className="text-slate-300">|</span>
            <span>STREAM: KAFKA V3.7</span>
          </div>
          <div>
            <span className="font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded">
              SYSTEM AUDIT: 100% SLA COMPLIANT
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
