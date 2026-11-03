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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} isLive={isLive} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'overview' && <OverviewTab />}
        {activeTab === 'pipelines' && <PipelinesTab />}
        {activeTab === 'streaming' && <StreamingTab />}
        {activeTab === 'quality' && <DataQualityTab />}
        {activeTab === 'analytics' && <AnalyticsTab />}
      </main>

      <footer className="border-t border-slate-900 bg-slate-950/80 py-4 text-center text-xs text-slate-500">
        Enterprise Real-Time Data Intelligence Platform &copy; 2024. All pipelines, streaming and dbt models active.
      </footer>
    </div>
  );
}

export default App;
