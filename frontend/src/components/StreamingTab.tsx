import React, { useEffect, useState } from 'react';
import { 
  Activity, 
  AlertTriangle, 
  AlertCircle,
  Radio, 
  Server, 
  RefreshCw, 
  Eye, 
  CheckCircle2, 
  Copy, 
  Check, 
  Terminal,
  Database
} from 'lucide-react';
import { StreamingStatus, DLQMessage } from '../types';
import { 
  fetchStreamingStatus, 
  fetchDLQMessages, 
  simulateStreamEvents, 
  simulatePoisonEvent 
} from '../services/api';

export const StreamingTab: React.FC = () => {
  const [status, setStatus] = useState<StreamingStatus | null>(null);
  const [dlq, setDlq] = useState<DLQMessage[]>([]);
  const [selectedMsg, setSelectedMsg] = useState<DLQMessage | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [isInjectingPoison, setIsInjectingPoison] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [copiedPayload, setCopiedPayload] = useState(false);

  const loadData = async () => {
    setIsRefreshing(true);
    try {
      const [sData, dData] = await Promise.all([fetchStreamingStatus(), fetchDLQMessages()]);
      setStatus(sData);
      const messages = dData.messages || [];
      setDlq(messages);
      // Auto-select the first message if none is selected yet
      if (!selectedMsg && messages.length > 0) {
        setSelectedMsg(messages[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSimulateTraffic = async (count = 25) => {
    setIsSimulating(true);
    setActionNotice(`Publishing ${count} high-throughput events across Kafka topics...`);
    try {
      const res = await simulateStreamEvents(count);
      setActionNotice(`Successfully published ${res.events_published} events to Kafka brokers.`);
      await loadData();
    } catch (err: any) {
      setActionNotice(`Simulation failed: ${err.message}`);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleInjectPoison = async () => {
    setIsInjectingPoison(true);
    setActionNotice('Publishing invalid negative order payload to trigger DLQ schema gate...');
    try {
      const res = await simulatePoisonEvent();
      setActionNotice(`Poison message rejected and routed to DLQ: ${res.reason}`);
      await loadData();
    } catch (err: any) {
      setActionNotice(`DLQ injection failed: ${err.message}`);
    } finally {
      setIsInjectingPoison(false);
    }
  };

  const handleCopyPayload = () => {
    if (!selectedMsg) return;
    navigator.clipboard.writeText(JSON.stringify(selectedMsg.raw_payload, null, 2));
    setCopiedPayload(true);
    setTimeout(() => setCopiedPayload(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Interactive Action Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
        <div>
          <div className="flex items-center space-x-2.5">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Apache Kafka Streaming &amp; Dead-Letter Queue</h2>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
              <Radio className="w-3 h-3 mr-1 animate-pulse text-emerald-600" />
              BROKER ACTIVE
            </span>
          </div>
          <p className="text-xs text-slate-500 font-mono mt-1">
            HIGH-THROUGHPUT EVENT STREAMING | CONSUMER GROUP SLIDING DEDUPLICATION | POISON ISOLATION
          </p>
        </div>

        {/* Action Buttons Toolbar */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Button 1: Simulate Traffic */}
          <button
            onClick={() => handleSimulateTraffic(25)}
            disabled={isSimulating}
            className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-md bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs disabled:opacity-60 transition"
            title="Generate 25 real-time e-commerce transactions across topics"
          >
            <Activity className={`w-3.5 h-3.5 text-white ${isSimulating ? 'animate-pulse' : ''}`} />
            <span>{isSimulating ? 'Publishing Events...' : 'Simulate 25 Live Events'}</span>
          </button>

          {/* Button 2: Inject Poison Payload */}
          <button
            onClick={handleInjectPoison}
            disabled={isInjectingPoison}
            className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-md bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-300 text-xs font-semibold shadow-xs disabled:opacity-60 transition"
            title="Inject an invalid negative amount transaction to test DLQ isolation"
          >
            <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
            <span>{isInjectingPoison ? 'Injecting Anomaly...' : 'Inject Poison to DLQ'}</span>
          </button>

          {/* Button 3: Refresh State */}
          <button
            onClick={loadData}
            disabled={isRefreshing}
            className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-md bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 text-xs font-medium shadow-xs disabled:opacity-60 transition"
            title="Refresh stream counters and DLQ list"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-slate-600 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Action Notification Banner */}
      {actionNotice && (
        <div className="p-3.5 rounded-lg bg-indigo-50/80 border border-indigo-200 text-indigo-900 text-xs font-mono flex items-center justify-between shadow-xs">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-indigo-600 shrink-0" />
            <span>{actionNotice}</span>
          </div>
          <button
            onClick={() => setActionNotice(null)}
            className="text-xs text-indigo-700 hover:text-indigo-900 font-bold ml-4 underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Kafka Topic Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {status &&
          Object.entries(status.topics).map(([topic, count]) => (
            <div key={topic} className="bg-white border border-slate-200 rounded-lg p-4 relative overflow-hidden shadow-xs hover:shadow-md transition-shadow">
              <div className="absolute top-0 left-0 right-0 h-[3px] bg-indigo-600" />
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono font-bold text-slate-500 uppercase tracking-wider">{topic}</span>
                <div className="p-1.5 rounded-md bg-indigo-50 border border-indigo-200 text-indigo-700">
                  <Server className="w-3.5 h-3.5" />
                </div>
              </div>
              <div className="mt-2.5">
                <div className="text-2xl font-bold text-slate-900 font-mono">{count.toLocaleString()}</div>
                <div className="text-[11px] text-slate-500 mt-0.5 font-mono">Stream Events</div>
              </div>
            </div>
          ))}

        {/* DLQ Quarantined Card */}
        <div className="bg-white border border-rose-200 rounded-lg p-4 relative overflow-hidden shadow-xs hover:shadow-md transition-shadow">
          <div className="absolute top-0 left-0 right-0 h-[3px] bg-rose-600" />
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono font-bold text-rose-700 uppercase tracking-wider">Dead-Letter Queue</span>
            <div className="p-1.5 rounded-md bg-rose-50 border border-rose-200 text-rose-700">
              <AlertTriangle className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="mt-2.5">
            <div className="text-2xl font-bold text-rose-700 font-mono">
              {status ? status.dlq_message_count.toLocaleString() : dlq.length}
            </div>
            <div className="text-[11px] text-rose-600 mt-0.5 font-mono font-semibold">Quarantined Poison Events</div>
          </div>
        </div>
      </div>

      {/* DLQ Message Inspector & Diagnostic Payload Viewer */}
      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs">
        <div className="px-5 py-4 border-b border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider font-mono">
              Dead-Letter Queue (DLQ) Poison Message Inspector
            </h3>
            <p className="text-[11px] text-slate-500 mt-0.5 font-mono">
              Rejected payloads isolated with diagnostic failure reasons and schema validation traces
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono text-slate-500">
              {dlq.length} Quarantined Messages
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-slate-200">
          {/* DLQ Table */}
          <div className="overflow-x-auto max-h-[420px] overflow-y-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 sticky top-0 uppercase font-mono font-bold text-slate-500 border-b border-slate-200 z-10">
                <tr>
                  <th className="px-4 py-3 tracking-wider">Topic</th>
                  <th className="px-4 py-3 tracking-wider">Failure Reason</th>
                  <th className="px-4 py-3 tracking-wider">Timestamp</th>
                  <th className="px-3 py-3 text-center tracking-wider">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                {dlq.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-slate-400 font-mono">
                      No poison messages in DLQ. Click &quot;Inject Poison to DLQ&quot; above to test.
                    </td>
                  </tr>
                ) : (
                  dlq.map((msg, index) => {
                    const isSelected = selectedMsg?.dlq_id === msg.dlq_id || (!selectedMsg && index === 0);
                    return (
                      <tr
                        key={msg.dlq_id || index}
                        onClick={() => setSelectedMsg(msg)}
                        className={`cursor-pointer transition-colors ${
                          isSelected
                            ? 'bg-indigo-50/90 text-indigo-950 font-semibold border-l-4 border-l-indigo-600'
                            : 'hover:bg-slate-50 text-slate-700'
                        }`}
                      >
                        <td className="px-4 py-3 text-indigo-700 font-bold whitespace-nowrap">{msg.topic}</td>
                        <td className="px-4 py-3 text-rose-700 font-medium max-w-xs truncate" title={msg.error_reason}>
                          {msg.error_reason}
                        </td>
                        <td className="px-4 py-3 text-slate-500 whitespace-nowrap">
                          {new Date(msg.failed_at).toLocaleTimeString()}
                        </td>
                        <td className="px-3 py-3 text-center">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedMsg(msg);
                            }}
                            className={`inline-flex items-center space-x-1 px-2 py-1 rounded text-[10px] font-mono font-bold border transition ${
                              isSelected
                                ? 'bg-indigo-600 text-white border-indigo-700'
                                : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'
                            }`}
                          >
                            <Eye className="w-3 h-3" />
                            <span>View</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Message Payload Viewer */}
          <div className="p-5 font-mono text-xs overflow-y-auto max-h-[420px] bg-slate-900 text-slate-100 flex flex-col justify-between">
            {selectedMsg ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">Poison Message ID:</span>
                    <span className="text-cyan-400 font-bold text-xs">{selectedMsg.dlq_id}</span>
                  </div>
                  <button
                    onClick={handleCopyPayload}
                    className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-[11px] font-mono transition"
                    title="Copy payload to clipboard"
                  >
                    {copiedPayload ? (
                      <>
                        <Check className="w-3 h-3 text-emerald-400" />
                        <span className="text-emerald-400">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3 text-slate-300" />
                        <span>Copy JSON</span>
                      </>
                    )}
                  </button>
                </div>

                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Validation Error Diagnostic:</span>
                  <p className="text-rose-400 bg-rose-950/40 p-2.5 rounded border border-rose-900/60 font-semibold leading-relaxed">
                    {selectedMsg.error_reason}
                  </p>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] uppercase font-bold text-slate-400">Raw Rejected Ingested Payload:</span>
                    <span className="text-[10px] text-slate-400">Topic: {selectedMsg.topic}</span>
                  </div>
                  <pre className="p-3 bg-black/60 rounded border border-slate-800 text-slate-300 text-[11px] overflow-x-auto whitespace-pre-wrap leading-relaxed font-mono">
                    {JSON.stringify(selectedMsg.raw_payload, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="py-20 text-center text-slate-400">
                <AlertTriangle className="w-8 h-8 mx-auto text-amber-500 mb-2 opacity-80" />
                <p className="font-semibold text-slate-300">Select a quarantined event to inspect diagnostic payload</p>
                <p className="text-[11px] text-slate-500 mt-1">Or click &quot;Inject Poison to DLQ&quot; above to simulate an invalid record.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
