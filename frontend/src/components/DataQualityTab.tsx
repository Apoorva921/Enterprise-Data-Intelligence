import React, { useEffect, useState } from 'react';
import { ShieldCheck, AlertOctagon, CheckCircle2, XCircle, FileSpreadsheet, RefreshCw } from 'lucide-react';
import { DataQualityReport } from '../types';
import { fetchDataQuality } from '../services/api';

export const DataQualityTab: React.FC = () => {
  const [report, setReport] = useState<DataQualityReport | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const data = await fetchDataQuality();
      setReport(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading && !report) {
    return <div className="p-8 text-center text-slate-400">Loading Great Expectations quality reports...</div>;
  }

  const silverScore = report?.silver_audit.quality_score_pct ?? 0;
  const bronzeScore = report?.bronze_audit.quality_score_pct ?? 0;
  const totalQuarantined = report?.quarantine_summary.total_quarantined_records ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Great Expectations Quality & Quarantine</h2>
          <p className="text-xs text-slate-400">Automated expectation suites, anomaly detection, and quarantined record diagnostics</p>
        </div>
        <button
          onClick={loadData}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-white text-xs font-medium transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Re-run Audit</span>
        </button>
      </div>

      {/* Quality Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase">Silver Layer Conformance</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400 font-mono">{silverScore}%</div>
          <p className="text-xs text-slate-400 mt-2">
            {report?.silver_audit.passed_checks} of {report?.silver_audit.total_checks} Great Expectations assertions passed
          </p>
          <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3">
            <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${silverScore}%` }} />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase">Raw Bronze Anomaly Catch Rate</span>
            <AlertOctagon className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-extrabold text-amber-400 font-mono">
            {report?.bronze_audit.failed_checks} Anomaly Types Detected
          </div>
          <p className="text-xs text-slate-400 mt-2">
            Duplicates, negative prices, and invalid emails intercepted
          </p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase">Total Quarantined Records</span>
            <FileSpreadsheet className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-3xl font-extrabold text-rose-300 font-mono">
            {totalQuarantined.toLocaleString()}
          </div>
          <p className="text-xs text-slate-400 mt-2">
            Isolated in S3 / MinIO quarantine bucket with failure diagnostics
          </p>
        </div>
      </div>

      {/* Quarantined Records Breakdown by Entity */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-800 bg-slate-950/50">
          <h3 className="text-sm font-semibold text-white">Quarantined Records by Entity</h3>
          <p className="text-xs text-slate-400">Diagnostic summary of quarantined anomalies</p>
        </div>
        <div className="p-5 grid grid-cols-1 md:grid-cols-3 gap-4">
          {report &&
            Object.entries(report.quarantine_summary.entities).map(([ent, val]) => (
              <div key={ent} className="p-4 rounded-lg bg-slate-950 border border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs uppercase font-bold text-blue-400">{ent}</span>
                  <span className="text-xs font-bold font-mono px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800">
                    {val.count.toLocaleString()} quarantined
                  </span>
                </div>
                <div className="text-xs text-slate-400 space-y-1">
                  {Object.entries(val.top_rejection_reasons).map(([reason, count]) => (
                    <div key={reason} className="truncate">
                      • {reason} ({count})
                    </div>
                  ))}
                  {val.count === 0 && <span className="text-slate-500 italic">No quarantined records</span>}
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Great Expectations Assertions Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-800 bg-slate-950/50">
          <h3 className="text-sm font-semibold text-white">Silver Conformance Expectation Suite Assertions</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300 font-mono">
            <thead className="bg-slate-950 uppercase font-medium text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-5 py-3 font-sans">Status</th>
                <th className="px-5 py-3">Expectation Name</th>
                <th className="px-5 py-3">Target Column</th>
                <th className="px-5 py-3 font-sans">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {report?.silver_audit.expectations.map((exp, idx) => (
                <tr key={idx} className="hover:bg-slate-800/30">
                  <td className="px-5 py-3 font-sans">
                    {exp.success ? (
                      <span className="inline-flex items-center space-x-1 text-emerald-400 font-semibold">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>PASSED</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center space-x-1 text-rose-400 font-semibold">
                        <XCircle className="w-4 h-4" />
                        <span>FAILED</span>
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-white font-semibold">{exp.expectation}</td>
                  <td className="px-5 py-3 text-blue-400">{exp.column}</td>
                  <td className="px-5 py-3 font-sans text-slate-400">{exp.details || 'Assertion satisfied'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

