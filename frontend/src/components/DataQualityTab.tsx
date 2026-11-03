import React, { useEffect, useState } from 'react';
import { 
  ShieldCheck, 
  AlertOctagon, 
  FileSpreadsheet, 
  RefreshCw, 
  CheckCircle2, 
  Download, 
  Check, 
  Terminal,
  Filter
} from 'lucide-react';
import { DataQualityReport } from '../types';
import { fetchDataQuality, rerunDataQualityAudit } from '../services/api';

export const DataQualityTab: React.FC = () => {
  const [report, setReport] = useState<DataQualityReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuditing, setIsAuditing] = useState(false);
  const [auditNotice, setAuditNotice] = useState<string | null>(null);
  const [selectedEntityFilter, setSelectedEntityFilter] = useState<string>('ALL');

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

  const handleRerunAudit = async () => {
    setIsAuditing(true);
    setAuditNotice('Executing Great Expectations validation suites across Bronze and Silver layers...');
    try {
      const updated = await rerunDataQualityAudit();
      setReport(updated);
      setAuditNotice(`Great Expectations validation complete: ${updated.silver_audit.passed_checks}/${updated.silver_audit.total_checks} assertions passed (${updated.silver_audit.quality_score_pct}% score).`);
    } catch (err: any) {
      setAuditNotice(`Audit execution failed: ${err.message}`);
    } finally {
      setIsAuditing(false);
    }
  };

  const handleDownloadReport = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `great_expectations_audit_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (loading && !report) {
    return <div className="p-8 text-center text-slate-500 font-mono text-xs">Loading Great Expectations quality audits...</div>;
  }

  const silverScore = report?.silver_audit.quality_score_pct ?? 0;
  const bronzeScore = report?.bronze_audit.quality_score_pct ?? 0;
  const totalQuarantined = report?.quarantine_summary.total_quarantined_records ?? 0;

  const entitiesList = report ? Object.entries(report.quarantine_summary.entities) : [];
  const filteredEntities = selectedEntityFilter === 'ALL'
    ? entitiesList
    : entitiesList.filter(([ent]) => ent === selectedEntityFilter);

  return (
    <div className="space-y-6">
      {/* Top Header & Interactive Action Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Great Expectations Quality &amp; Quarantine Audit</h2>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold">
              100% SLA PASS
            </span>
          </div>
          <p className="text-xs text-slate-500 font-mono mt-0.5">
            AUTOMATED EXPECTATION SUITES | ANOMALY DETECTION GATES | RECORD QUARANTINE ISOLATION
          </p>
        </div>

        {/* Action Buttons Toolbar */}
        <div className="flex items-center space-x-2.5">
          <button
            onClick={handleRerunAudit}
            disabled={isAuditing}
            className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-md bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs disabled:opacity-60 transition"
            title="Execute Great Expectations validation suite right now"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-white ${isAuditing ? 'animate-spin' : ''}`} />
            <span>{isAuditing ? 'Auditing Suite...' : 'Re-run Audit'}</span>
          </button>

          <button
            onClick={handleDownloadReport}
            className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-md bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 text-xs font-medium shadow-xs transition"
            title="Export validation report as JSON"
          >
            <Download className="w-3.5 h-3.5 text-slate-600" />
            <span>Export Report</span>
          </button>
        </div>
      </div>

      {/* Audit Notification Banner */}
      {auditNotice && (
        <div className="p-3.5 rounded-lg bg-indigo-50/80 border border-indigo-200 text-indigo-900 text-xs font-mono flex items-center justify-between shadow-xs">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-indigo-600 shrink-0" />
            <span>{auditNotice}</span>
          </div>
          <button
            onClick={() => setAuditNotice(null)}
            className="text-xs text-indigo-700 hover:text-indigo-900 font-bold ml-4 underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Quality Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white border border-slate-200 rounded-lg p-5 relative overflow-hidden shadow-xs hover:shadow-md transition-shadow">
          <div className="absolute top-0 left-0 right-0 h-[3px] bg-emerald-600" />
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono font-bold text-slate-500 uppercase tracking-wider">
              Silver Layer SLA Conformance
            </span>
            <div className="p-1.5 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-700">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-emerald-700 font-mono">{silverScore}%</div>
          <p className="text-[11px] text-slate-500 mt-2 font-mono font-medium">
            {report?.silver_audit.passed_checks} of {report?.silver_audit.total_checks} Great Expectations assertions passed
          </p>
          <div className="w-full bg-slate-100 rounded-full h-2 mt-3">
            <div className="bg-emerald-600 h-2 rounded-full transition-all duration-500" style={{ width: `${silverScore}%` }} />
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-5 relative overflow-hidden shadow-xs hover:shadow-md transition-shadow">
          <div className="absolute top-0 left-0 right-0 h-[3px] bg-amber-500" />
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono font-bold text-slate-500 uppercase tracking-wider">
              Raw Bronze Anomaly Catch Rate
            </span>
            <div className="p-1.5 rounded-md bg-amber-50 border border-amber-200 text-amber-700">
              <AlertOctagon className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-amber-700 font-mono">
            {report?.bronze_audit.failed_checks} Anomaly Types Intercepted
          </div>
          <p className="text-[11px] text-slate-500 mt-2 font-mono font-medium">
            Duplicates, negative order bounds, and malformed emails quarantined
          </p>
          <div className="w-full bg-slate-100 rounded-full h-2 mt-3">
            <div className="bg-amber-500 h-2 rounded-full" style={{ width: `100%` }} />
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-5 relative overflow-hidden shadow-xs hover:shadow-md transition-shadow">
          <div className="absolute top-0 left-0 right-0 h-[3px] bg-rose-600" />
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono font-bold text-slate-500 uppercase tracking-wider">
              Total Quarantined Records
            </span>
            <div className="p-1.5 rounded-md bg-rose-50 border border-rose-200 text-rose-700">
              <FileSpreadsheet className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-rose-700 font-mono">
            {totalQuarantined.toLocaleString()}
          </div>
          <p className="text-[11px] text-slate-500 mt-2 font-mono font-medium">
            Isolated in S3 / MinIO quarantine directory with failure tags
          </p>
          <div className="w-full bg-slate-100 rounded-full h-2 mt-3">
            <div className="bg-rose-600 h-2 rounded-full" style={{ width: `100%` }} />
          </div>
        </div>
      </div>

      {/* Quarantined Records Breakdown by Entity */}
      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-xs">
        <div className="px-5 py-4 border-b border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider font-mono">
              Quarantined Records Diagnostics by Entity
            </h3>
            <p className="text-[11px] text-slate-500 mt-0.5 font-mono">
              Breakdown of contaminated records purged from production analytical tables
            </p>
          </div>

          {/* Entity Filter Tabs */}
          <div className="flex items-center space-x-1.5 overflow-x-auto">
            <button
              onClick={() => setSelectedEntityFilter('ALL')}
              className={`px-2.5 py-1 rounded text-[11px] font-mono font-bold transition ${
                selectedEntityFilter === 'ALL'
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              All Entities ({entitiesList.length})
            </button>
            {entitiesList.map(([ent]) => (
              <button
                key={ent}
                onClick={() => setSelectedEntityFilter(ent)}
                className={`px-2.5 py-1 rounded text-[11px] font-mono font-bold uppercase transition ${
                  selectedEntityFilter === ent
                    ? 'bg-indigo-600 text-white shadow-xs'
                    : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
                }`}
              >
                {ent}
              </button>
            ))}
          </div>
        </div>

        <div className="p-5 grid grid-cols-1 md:grid-cols-3 gap-4">
          {filteredEntities.map(([ent, val]) => (
            <div key={ent} className="p-4 rounded-lg bg-slate-50/60 border border-slate-200 font-mono hover:border-indigo-300 transition-colors">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-indigo-700 uppercase">{ent}</span>
                <span className="text-sm font-bold text-rose-700">{val.count.toLocaleString()}</span>
              </div>
              <div className="mt-2 text-[11px] text-slate-600">
                Primary Anomaly: <span className="text-slate-900 font-bold">{Object.keys(val.top_rejection_reasons)[0] || 'Schema assertion failure'}</span>
              </div>
              <div className="mt-2 text-[11px] text-emerald-700 font-semibold flex items-center space-x-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Production lake protected</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
