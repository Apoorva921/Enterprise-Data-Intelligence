import React, { useEffect, useState } from 'react';
import { 
  Play, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  RefreshCw, 
  GitBranch, 
  Terminal, 
  Layers, 
  FastForward,
  Check
} from 'lucide-react';
import { PipelineInfo, PipelineRun } from '../types';
import { fetchPipelines, triggerPipeline } from '../services/api';

export const PipelinesTab: React.FC = () => {
  const [pipelines, setPipelines] = useState<PipelineInfo[]>([]);
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [triggering, setTriggering] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<{ type: 'info' | 'success' | 'error'; text: string } | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadData = async () => {
    setIsRefreshing(true);
    try {
      const data = await fetchPipelines();
      setPipelines(data.pipelines || []);
      setRuns(data.recent_runs || []);
    } catch (e: any) {
      console.error(e);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleTrigger = async (dagId: string) => {
    setTriggering(dagId);
    setStatusMsg({ type: 'info', text: `Triggering execution for DAG '${dagId}'...` });
    try {
      const res = await triggerPipeline(dagId);
      const state = res.state || 'SUCCESS';
      const duration = res.duration_seconds || '0.5';
      setStatusMsg({
        type: state === 'SUCCESS' ? 'success' : 'error',
        text: `DAG '${dagId}' completed with status: ${state} (${duration}s). Run ID: ${res.run_id || 'manual'}`,
      });
      await loadData();
    } catch (err: any) {
      setStatusMsg({
        type: 'error',
        text: `Trigger failed for DAG '${dagId}': ${err.message || 'Server error'}`,
      });
    } finally {
      setTriggering(null);
    }
  };

  const handleTriggerAll = async () => {
    setTriggering('all');
    setStatusMsg({ type: 'info', text: 'Executing all 7 Medallion Architecture workflows in sequence...' });
    try {
      const res = await triggerPipeline('all');
      setStatusMsg({
        type: 'success',
        text: `All 7 workflows executed successfully in ${res.duration_seconds}s. Total Medallion lake updated.`,
      });
      await loadData();
    } catch (err: any) {
      setStatusMsg({
        type: 'error',
        text: `Sequential execution failed: ${err.message || 'Server error'}`,
      });
    } finally {
      setTriggering(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Orchestration Control Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Apache Airflow Pipeline Orchestration</h2>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold">
              SCHEDULER HEALTHY
            </span>
          </div>
          <p className="text-xs text-slate-500 font-mono mt-0.5">
            MANAGING 7 PRODUCTION MEDALLION WORKFLOW DAGS WITH AUTOMATED RETRIES &amp; BACKFILLS
          </p>
        </div>

        {/* Global Pipeline Action Buttons */}
        <div className="flex items-center space-x-2.5">
          <button
            onClick={handleTriggerAll}
            disabled={triggering !== null}
            className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-md bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs disabled:opacity-50 transition"
            title="Execute all 7 Medallion pipelines sequentially"
          >
            <FastForward className="w-3.5 h-3.5 text-white" />
            <span>{triggering === 'all' ? 'Running All DAGs...' : 'Run All 7 Pipelines'}</span>
          </button>

          <button
            onClick={loadData}
            disabled={isRefreshing}
            className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-md bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 text-xs font-medium shadow-xs disabled:opacity-50 transition"
            title="Refresh DAG states"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-slate-600 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Status Notice Banner */}
      {statusMsg && (
        <div
          className={`p-3.5 rounded-lg text-xs font-mono flex items-center justify-between shadow-xs border ${
            statusMsg.type === 'success'
              ? 'bg-emerald-50/90 border-emerald-200 text-emerald-950'
              : statusMsg.type === 'error'
              ? 'bg-rose-50/90 border-rose-200 text-rose-950'
              : 'bg-indigo-50/90 border-indigo-200 text-indigo-950'
          }`}
        >
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 shrink-0" />
            <span className="font-medium">{statusMsg.text}</span>
          </div>
          <button
            onClick={() => setStatusMsg(null)}
            className="text-xs font-bold underline ml-4 hover:opacity-80"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* DAG Catalog Table */}
      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs">
        <div className="px-5 py-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider font-mono flex items-center space-x-2">
            <GitBranch className="w-4 h-4 text-indigo-600" />
            <span>Active Airflow Workflows ({pipelines.length} Registered DAGs)</span>
          </h3>
          <span className="text-[11px] font-mono text-slate-500 font-medium">Click Trigger to run any DAG manually</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 uppercase font-mono font-bold text-slate-500 border-b border-slate-200">
              <tr>
                <th className="px-5 py-3 tracking-wider">DAG Identifier</th>
                <th className="px-5 py-3 tracking-wider">Workflow Description</th>
                <th className="px-5 py-3 tracking-wider">Layer</th>
                <th className="px-5 py-3 tracking-wider">Schedule</th>
                <th className="px-5 py-3 tracking-wider">State</th>
                <th className="px-5 py-3 tracking-wider">Duration</th>
                <th className="px-5 py-3 text-right tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {pipelines.map((pipe) => {
                const isThisTriggering = triggering === pipe.id;
                return (
                  <tr key={pipe.id} className="hover:bg-slate-50 transition-colors duration-100 font-mono">
                    <td className="px-5 py-3.5 text-indigo-600 font-bold whitespace-nowrap">{pipe.id}</td>
                    <td className="px-5 py-3.5 text-slate-900 font-sans font-medium">{pipe.name}</td>
                    <td className="px-5 py-3.5">
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 font-semibold">
                        {pipe.layer}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-slate-500 whitespace-nowrap">{pipe.schedule}</td>
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded text-[10px] font-bold uppercase ${
                          pipe.last_status === 'SUCCESS'
                            ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                            : 'bg-rose-50 text-rose-800 border border-rose-200'
                        }`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${pipe.last_status === 'SUCCESS' ? 'bg-emerald-600' : 'bg-rose-600'}`} />
                        <span>{pipe.last_status}</span>
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-slate-500 font-semibold whitespace-nowrap">{pipe.last_duration_seconds}s</td>
                    <td className="px-5 py-3.5 text-right whitespace-nowrap">
                      <button
                        onClick={() => handleTrigger(pipe.id)}
                        disabled={triggering !== null}
                        className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded bg-indigo-600 hover:bg-indigo-700 text-white text-[11px] font-mono transition shadow-xs disabled:opacity-50"
                        title={`Run ${pipe.name} right now`}
                      >
                        {isThisTriggering ? (
                          <>
                            <RefreshCw className="w-3 h-3 text-white animate-spin" />
                            <span>Running...</span>
                          </>
                        ) : (
                          <>
                            <Play className="w-3 h-3 text-white fill-white" />
                            <span>Trigger</span>
                          </>
                        )}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Pipeline Runs Audit */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider font-mono">
            Recent Workflow Execution Audit Trail
          </h3>
          <span className="text-[11px] font-mono text-slate-500 font-medium">{runs.length} Recorded Runs</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {runs.slice(0, 6).map((run) => (
            <div
              key={run.run_id}
              className="p-3.5 rounded-lg bg-slate-50/60 border border-slate-200 hover:border-slate-300 transition text-xs font-mono"
            >
              <div className="flex items-center justify-between">
                <span className="text-indigo-600 font-bold truncate max-w-[180px]" title={run.dag_id}>
                  {run.dag_id}
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold">
                  {run.state}
                </span>
              </div>
              <div className="text-[11px] text-slate-600 mt-2">
                Tasks Executed: <span className="text-slate-900 font-bold">{run.tasks_executed}</span>
              </div>
              <div className="text-[10px] text-slate-500 mt-1 flex items-center justify-between">
                <span>Duration: {run.duration_seconds}s</span>
                <span>{new Date(run.execution_date).toLocaleTimeString()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
