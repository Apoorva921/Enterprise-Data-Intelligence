import React, { useEffect, useState } from 'react';
import { 
  BarChart3, 
  Globe, 
  Layers, 
  ExternalLink, 
  Database, 
  RefreshCw, 
  Download, 
  Calendar 
} from 'lucide-react';
import { RevenueAnalytics } from '../types';
import { fetchRevenueAnalytics } from '../services/api';

export const AnalyticsTab: React.FC = () => {
  const [data, setData] = useState<RevenueAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDays, setSelectedDays] = useState<number>(30);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadData = async (days = selectedDays) => {
    setIsRefreshing(true);
    try {
      const res = await fetchRevenueAnalytics(days);
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData(selectedDays);
  }, [selectedDays]);

  const handleExportData = () => {
    if (!data) return;
    const csvRows = [
      ['Date', 'Total Orders', 'Gross Revenue (USD)'],
      ...data.daily_trends.map((d) => [d.order_day, d.total_orders, d.total_gross_revenue.toFixed(2)]),
    ];
    const csvContent = 'data:text/csv;charset=utf-8,' + csvRows.map((r) => r.join(',')).join('\n');
    const encoded = encodeURI(csvContent);
    const link = document.createElement('a');
    link.href = encoded;
    link.download = `revenue_trends_${selectedDays}d.csv`;
    link.click();
  };

  if (loading && !data) {
    return <div className="p-8 text-center text-slate-500 font-mono text-xs">Loading warehouse analytical marts...</div>;
  }

  const maxRevenue = data?.daily_trends.reduce((max, d) => Math.max(max, d.total_gross_revenue), 1) ?? 1;

  return (
    <div className="space-y-6">
      {/* Top Header & Interactive Timeframe Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Warehouse Marts &amp; Dimensional Analytics</h2>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200 font-bold">
              STAR SCHEMA
            </span>
          </div>
          <p className="text-xs text-slate-500 font-mono mt-0.5">
            KIMBALL STAR SCHEMA | AGGREGATED DAILY REVENUE MARTS | GEOGRAPHICAL DISTRIBUTION
          </p>
        </div>

        {/* Action Buttons Toolbar */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Timeframe Toggle Buttons */}
          <div className="flex items-center rounded-md p-1 bg-slate-100 border border-slate-200">
            <span className="text-[11px] text-slate-500 font-mono px-2 flex items-center">
              <Calendar className="w-3 h-3 mr-1" />
              Window:
            </span>
            {[7, 14, 30, 90].map((d) => (
              <button
                key={d}
                onClick={() => setSelectedDays(d)}
                className={`px-2.5 py-1 rounded text-xs font-semibold font-mono transition ${
                  selectedDays === d
                    ? 'bg-white text-indigo-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {d}d
              </button>
            ))}
          </div>

          {/* Export Button */}
          <button
            onClick={handleExportData}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 text-xs font-semibold shadow-xs transition"
            title="Export trend series to CSV"
          >
            <Download className="w-3.5 h-3.5 text-indigo-600" />
            <span>Export CSV</span>
          </button>

          {/* Refresh Button */}
          <button
            onClick={() => loadData(selectedDays)}
            disabled={isRefreshing}
            className="p-1.5 rounded-md bg-white border border-slate-300 text-slate-600 hover:text-slate-900 shadow-xs transition"
            title="Refresh Mart metrics"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-indigo-600' : ''}`} />
          </button>

          {/* Docs Link */}
          <a
            href="/docs"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium shadow-xs transition"
          >
            <span>API Docs</span>
            <ExternalLink className="w-3.5 h-3.5 text-slate-300" />
          </a>
        </div>
      </div>

      {/* Revenue Trend Visualizer */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-xs">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider font-mono">
              {selectedDays}-Day Daily Gross Revenue Mart (DuckDB / dbt)
            </h3>
            <p className="text-[11px] text-slate-500 font-mono mt-0.5">Aggregated from Gold layer fact_orders</p>
          </div>
          <span className="text-[10px] font-mono px-2.5 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200 font-bold">
            MART_DAILY_REVENUE ({data?.daily_trends.length || 0} Days Returned)
          </span>
        </div>

        {/* CSS-based Bar Chart */}
        <div className="space-y-3.5 font-mono">
          {data?.daily_trends.slice(0, 15).map((d) => {
            const widthPct = Math.round((d.total_gross_revenue / maxRevenue) * 100);
            return (
              <div key={d.order_day} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-800 font-bold">{d.order_day}</span>
                  <div className="flex items-center space-x-4">
                    <span className="text-slate-500 text-[11px] font-medium">{d.total_orders.toLocaleString()} orders</span>
                    <span className="font-bold text-amber-800">
                      ${d.total_gross_revenue.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-indigo-600 via-blue-600 to-emerald-500 h-2.5 rounded-full transition-all duration-500"
                    style={{ width: `${Math.max(5, widthPct)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2-Column: Regional & Product Category Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Regional Revenue Breakdown */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider font-mono flex items-center space-x-2">
              <Globe className="w-4 h-4 text-indigo-600" />
              <span>Regional Fulfillment Distribution</span>
            </h3>
            <span className="text-[10px] font-mono text-slate-500 uppercase font-semibold">Gross Volume</span>
          </div>
          <div className="divide-y divide-slate-100">
            {data?.regional_breakdown.map((r) => (
              <div key={r.region} className="py-3 flex items-center justify-between font-mono text-xs">
                <div>
                  <div className="text-slate-900 font-bold font-sans">{r.region}</div>
                  <div className="text-[11px] text-slate-500">{r.total_orders.toLocaleString()} fulfilled orders</div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-indigo-700">
                    ${r.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Product Category Breakdown */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider font-mono flex items-center space-x-2">
              <Layers className="w-4 h-4 text-purple-600" />
              <span>Category Margin &amp; Catalog Breadth</span>
            </h3>
            <span className="text-[10px] font-mono text-slate-500 uppercase font-semibold">Avg Margin</span>
          </div>
          <div className="space-y-3 font-mono">
            {data?.category_breakdown.map((c) => (
              <div key={c.category} className="p-3 rounded-md bg-slate-50/60 border border-slate-200 flex items-center justify-between">
                <div>
                  <div className="text-xs font-bold text-slate-900 font-sans">{c.category}</div>
                  <div className="text-[11px] text-slate-500">{c.product_count} active catalog SKUs</div>
                </div>
                <span className="font-bold text-emerald-800 px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-xs">
                  {c.avg_margin_pct}% Margin
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Warehouse Marts & dbt Semantic Layer Banner */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 shadow-xs font-mono text-xs">
        <div>
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4 text-indigo-600" />
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              DuckDB &amp; BigQuery Star Schema Analytical Layer
            </h4>
          </div>
          <p className="text-[11px] text-slate-600 mt-1 font-medium">
            Curated dimensional marts and fact aggregations compiled via <code className="text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-200 font-bold">dbt/models/marts/</code>
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-[11px] text-emerald-800 px-3 py-1 rounded bg-emerald-50 border border-emerald-200 font-bold">
            DBT RUN: CLEAN
          </span>
        </div>
      </div>
    </div>
  );
};
