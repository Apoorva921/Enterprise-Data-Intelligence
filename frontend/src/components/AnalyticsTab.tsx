import React, { useEffect, useState } from 'react';
import { BarChart3, Globe, Layers, Download, ExternalLink } from 'lucide-react';
import { RevenueAnalytics } from '../types';
import { fetchRevenueAnalytics } from '../services/api';

export const AnalyticsTab: React.FC = () => {
  const [data, setData] = useState<RevenueAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetchRevenueAnalytics();
        setData(res);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading && !data) {
    return <div className="p-8 text-center text-slate-400">Loading business analytics...</div>;
  }

  const maxRevenue = data?.daily_trends.reduce((max, d) => Math.max(max, d.total_gross_revenue), 1) ?? 1;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white">Business Intelligence & Dimensional Analytics</h2>
          <p className="text-xs text-slate-400">Curated revenue data marts, regional sales heat, and Power BI DAX integration</p>
        </div>
        <div className="flex items-center space-x-2">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-white text-xs font-medium transition"
          >
            <span>FastAPI Docs</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* Revenue Trend Visualizer */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-base font-semibold text-white">30-Day Daily Gross Revenue Mart</h3>
            <p className="text-xs text-slate-400">Aggregated by dbt and DuckDB analytical warehouse</p>
          </div>
          <span className="text-xs px-2.5 py-1 rounded bg-blue-950 text-blue-300 border border-blue-800">
            mart_daily_revenue
          </span>
        </div>

        {/* CSS-based Bar Chart */}
        <div className="space-y-3">
          {data?.daily_trends.slice(0, 10).map((d) => {
            const widthPct = Math.round((d.total_gross_revenue / maxRevenue) * 100);
            return (
              <div key={d.order_day} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-mono text-slate-300">{d.order_day}</span>
                  <div className="flex items-center space-x-4">
                    <span className="text-slate-400">{d.total_orders.toLocaleString()} orders</span>
                    <span className="font-mono font-bold text-emerald-400">
                      ${d.total_gross_revenue.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>
                <div className="w-full bg-slate-800/80 rounded-full h-2.5 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-emerald-400 h-2.5 rounded-full transition-all duration-500"
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
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white flex items-center">
              <Globe className="w-4 h-4 mr-2 text-blue-400" />
              Regional Sales Distribution
            </h3>
            <span className="text-xs text-slate-400">Total Volume</span>
          </div>
          <div className="divide-y divide-slate-800">
            {data?.regional_breakdown.map((r) => (
              <div key={r.region} className="py-2.5 flex items-center justify-between text-xs">
                <span className="text-slate-300 font-medium">{r.region}</span>
                <div className="flex items-center space-x-4">
                  <span className="text-slate-400">{r.total_orders.toLocaleString()} orders</span>
                  <span className="font-mono font-semibold text-white">
                    ${r.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Product Category Margins */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white flex items-center">
              <Layers className="w-4 h-4 mr-2 text-violet-400" />
              Category Gross Margin %
            </h3>
            <span className="text-xs text-slate-400">Average Profitability</span>
          </div>
          <div className="divide-y divide-slate-800">
            {data?.category_breakdown.map((c) => (
              <div key={c.category} className="py-2.5 flex items-center justify-between text-xs">
                <div>
                  <span className="text-slate-300 font-medium">{c.category}</span>
                  <span className="text-slate-500 ml-2">({c.product_count} SKUs)</span>
                </div>
                <span className="font-mono font-bold text-emerald-400 px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800">
                  {c.avg_margin_pct}% Margin
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Power BI Integration Banner */}
      <div className="bg-gradient-to-r from-blue-950/40 via-slate-900 to-indigo-950/40 border border-blue-900/40 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h4 className="text-sm font-bold text-white">Power BI Desktop Integration Layer Ready</h4>
          <p className="text-xs text-slate-400 mt-1">
            25+ DAX measures and pre-aggregated views available in <code className="text-blue-300">powerbi/dax_measures.dax</code>
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono text-emerald-400 px-3 py-1 rounded bg-emerald-950 border border-emerald-800">
            DirectQuery Enabled
          </span>
        </div>
      </div>
    </div>
  );
};
