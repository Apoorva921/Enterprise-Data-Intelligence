import React, { useEffect, useState } from 'react';
import { Play, CheckCircle2, XCircle, Clock, RefreshCw, GitCommit } from 'lucide-react';
import { PipelineInfo, PipelineRun } from '../types';
import { fetchPipelines, triggerPipeline } from '../services/api';

export const PipelinesTab: React.FC = () => {
  const [pipelines, setPipelines] = useState<PipelineInfo[]>([]);
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [triggering, setTriggering] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const data = await fetchPipelines();
      setPipelines(data.pipelines);
      setRuns(data.recent_runs);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleTrigger = async (dagId: string) => {
    setTriggering(dagId);
    setStatusMsg(`Triggering DAG '${dagId}'...`);
    try {
      const res = await triggerPipeline(dagId);
      setStatusMsg(`DAG '${dagId}' triggered successfully! State: ${res.state} (${res.duration_seconds}s)`);
      await loadData();
    } catch (err: any) {
      setStatusMsg(`Failed to trigger DAG '${dagId}': ${err.message}`);
    } finally {
      setTriggering(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and status notification */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white">Apache Airflow Pipeline Orchestration</h2>
          <p className="text-xs text-slate-400">Manage, trigger, and inspect 7 production Medallion workflow DAGs</p>
        </div>
        <button
          onClick={loadData}
          className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-800 text-slate-200 text-xs font-medium hover:bg-slate-700 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh State</span>
        </button>
      </div>

      {statusMsg && (
        <div className="p-3 rounded-lg bg-blue-950/80 border border-blue-800 text-blue-200 text-xs font-mono">
          {statusMsg}
        </div>
      )}

      {/* DAG Catalog Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="px-5 py-4 border-b border-slate-800 bg-slate-950/50">
          <h3 className="text-sm font-semibold text-white">Active Airflow Workflows</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/80 text-xs uppercase font-medium text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-5 py-3">DAG Identifier</th>
                <th className="px-5 py-3">Workflow Name</th>
                <th className="px-5 py-3">Medallion Layer</th>
                <th className="px-5 py-3">Schedule</th>
                <th className="px-5 py-3">Last State</th>
                <th className="px-5 py-3">Duration</th>
                <th className="px-5 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {pipelines.map((pipe) => (
                <tr key={pipe.id} className="hover:bg-slate-800/30 transition">
                  <td className="px-5 py-3 font-mono text-xs font-semibold text-blue-400">{pipe.id}</td>
                  <td className="px-5 py-3 text-white font-medium">{pipe.name}</td>
                  <td className="px-5 py-3">
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {pipe.layer}
                    </span>
                  </td>
                  <td className="px-5 py-3 font-mono text-xs text-slate-400">{pipe.schedule}</td>
                  <td className="px-5 py-3">
                    <span
                      className={`inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        pipe.last_status === 'SUCCESS'
                          ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                          : pipe.last_status === 'FAILED'
                          ? 'bg-rose-950 text-rose-300 border border-rose-800'
                          : 'bg-slate-800 text-slate-400 border border-slate-700'
                      }`}
                    >
                      {pipe.last_status === 'SUCCESS' ? (
                        <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      ) : (
                        <Clock className="w-3 h-3 text-slate-400" />
                      )}
                      <span>{pipe.last_status}</span>
                    </span>
                  </td>
                  <td className="px-5 py-3 font-mono text-xs text-slate-400">
                    {pipe.last_duration_seconds ? `${pipe.last_duration_seconds}s` : '-'}
                  </td>
                  <td className="px-5 py-3 text-right">
                    <button
                      onClick={() => handleTrigger(pipe.id)}
                      disabled={triggering === pipe.id}
                      className="inline-flex items-center space-x-1 px-3 py-1 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-medium transition"
                    >
                      <Play className="w-3 h-3" />
                      <span>{triggering === pipe.id ? 'Running...' : 'Trigger'}</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Execution Run History */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="px-5 py-4 border-b border-slate-800 bg-slate-950/50 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">Pipeline Execution Audit Log</h3>
          <span className="text-xs text-slate-400">{runs.length} runs recorded</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 uppercase font-medium text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-5 py-3">Run ID</th>
                <th className="px-5 py-3">DAG</th>
                <th className="px-5 py-3">Execution Time (UTC)</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Duration</th>
                <th className="px-5 py-3">Tasks</th>
                <th className="px-5 py-3">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {runs.map((run) => (
                <tr key={run.run_id} className="hover:bg-slate-800/30">
                  <td className="px-5 py-2.5 text-slate-400">{run.run_id}</td>
                  <td className="px-5 py-2.5 text-blue-400 font-semibold">{run.dag_id}</td>
                  <td className="px-5 py-2.5 text-slate-300">{new Date(run.execution_date).toLocaleString()}</td>
                  <td className="px-5 py-2.5">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        run.state === 'SUCCESS' ? 'bg-emerald-950 text-emerald-300' : 'bg-rose-950 text-rose-300'
                      }`}
                    >
                      {run.state}
                    </span>
                  </td>
                  <td className="px-5 py-2.5 text-white">{run.duration_seconds}s</td>
                  <td className="px-5 py-2.5 text-slate-300">{run.tasks_executed} tasks</td>
                  <td className="px-5 py-2.5 text-slate-400 font-sans">{run.details || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

