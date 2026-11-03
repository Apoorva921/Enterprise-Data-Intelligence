import React, { useEffect, useState } from 'react';
import { Activity, AlertTriangle, Radio, Server, RefreshCw } from 'lucide-react';
import { StreamingStatus, DLQMessage } from '../types';
import { fetchStreamingStatus, fetchDLQMessages } from '../services/api';

export const StreamingTab: React.FC = () => {
  const [status, setStatus] = useState<StreamingStatus | null>(null);
  const [dlq, setDlq] = useState<DLQMessage[]>([]);
  const [selectedMsg, setSelectedMsg] = useState<DLQMessage | null>(null);

  const loadData = async () => {
    try {
      const [sData, dData] = await Promise.all([fetchStreamingStatus(), fetchDLQMessages()]);
      setStatus(sData);
      setDlq(dData.messages || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Apache Kafka Streaming & Dead-Letter Queue</h2>
          <p className="text-xs text-slate-400">Real-time event stream monitoring, consumer group lag, and poison message isolation</p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800">
            <Radio className="w-3 h-3 mr-1 animate-pulse" />
            {status?.live_kafka_active ? 'Live Kafka Cluster' : 'High-Throughput Streaming Engine'}
          </span>
        </div>
      </div>

      {/* Kafka Topic Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {status &&
          Object.entries(status.topics).map(([topic, count]) => (
            <div key={topic} className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-semibold text-slate-400 uppercase">{topic}</span>
                <Server className="w-4 h-4 text-blue-400" />
              </div>
              <div className="mt-3">
                <div className="text-2xl font-bold text-white font-mono">{count.toLocaleString()}</div>
                <div className="text-[11px] text-slate-400 mt-1">Published Stream Events</div>
              </div>
            </div>
          ))}

        <div className="bg-slate-900 border border-rose-900/40 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-semibold text-rose-400 uppercase">Dead-Letter Queue (DLQ)</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-rose-300 font-mono">
              {status ? status.dlq_message_count.toLocaleString() : 0}
            </div>
            <div className="text-[11px] text-rose-400/80 mt-1">Poison / Schema-Invalid Events</div>
          </div>
        </div>
      </div>

      {/* DLQ Message Inspector */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-5 border-b border-slate-800 bg-slate-950/50 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white">Dead-Letter Queue (DLQ) Diagnostics</h3>
            <p className="text-xs text-slate-400">Rejected messages quarantined with strict validation failure reasons</p>
          </div>
          <button
            onClick={loadData}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-slate-800">
          {/* DLQ Table */}
          <div className="overflow-x-auto max-h-96 overflow-y-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 sticky top-0 uppercase font-medium text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Topic</th>
                  <th className="px-4 py-3">Reason</th>
                  <th className="px-4 py-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {dlq.map((msg) => (
                  <tr
                    key={msg.dlq_id}
                    onClick={() => setSelectedMsg(msg)}
                    className={`cursor-pointer transition hover:bg-slate-800/40 ${
                      selectedMsg?.dlq_id === msg.dlq_id ? 'bg-blue-950/40 text-blue-200' : ''
                    }`}
                  >
                    <td className="px-4 py-2.5 font-bold text-amber-400">{msg.topic}</td>
                    <td className="px-4 py-2.5 text-rose-400 truncate max-w-xs">{msg.error_reason}</td>
                    <td className="px-4 py-2.5 text-slate-400">{new Date(msg.failed_at).toLocaleTimeString()}</td>
                  </tr>
                ))}
                {dlq.length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-4 py-6 text-center text-slate-500 font-sans">
                      No rejected events in Dead-Letter Queue. Streaming is 100% healthy.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Payload Inspector Pane */}
          <div className="p-5 bg-slate-950/40">
            <h4 className="text-xs font-semibold uppercase text-slate-400 mb-3 tracking-wider">
              Diagnostic Payload Inspector
            </h4>
            {selectedMsg ? (
              <div className="space-y-3 font-mono text-xs">
                <div>
                  <span className="text-slate-500">DLQ ID: </span>
                  <span className="text-slate-300">{selectedMsg.dlq_id}</span>
                </div>
                <div>
                  <span className="text-slate-500">Failure Reason: </span>
                  <div className="p-2.5 rounded bg-rose-950/60 border border-rose-800 text-rose-200 mt-1 whitespace-pre-wrap">
                    {selectedMsg.error_reason}
                  </div>
                </div>
                <div>
                  <span className="text-slate-500">Raw Payload Envelope: </span>
                  <pre className="p-3 rounded bg-slate-900 border border-slate-800 text-emerald-400 mt-1 overflow-x-auto text-[11px]">
                    {JSON.stringify(selectedMsg.raw_payload, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-slate-500 text-xs text-center">
                Select a message from the DLQ list to inspect full payload & stacktrace
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

