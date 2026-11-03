import {
  KPISummary,
  PipelineInfo,
  PipelineRun,
  StreamingStatus,
  DLQMessage,
  DataQualityReport,
  RevenueAnalytics,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function fetchHealth(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/health`);
  return res.json();
}

export async function fetchKPIs(): Promise<KPISummary> {
  const res = await fetch(`${API_BASE}/api/kpis`);
  return res.json();
}

export async function fetchPipelines(): Promise<{ pipelines: PipelineInfo[]; recent_runs: PipelineRun[] }> {
  const res = await fetch(`${API_BASE}/api/pipelines`);
  return res.json();
}

export async function triggerPipeline(dagId: string): Promise<any> {
  // First obtain admin token
  const authRes = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'admin', password: 'adminpassword123' }),
  });
  const authData = await authRes.json();

  const res = await fetch(`${API_BASE}/api/pipelines/${dagId}/trigger`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${authData.access_token}`,
    },
  });
  return res.json();
}

export async function fetchStreamingStatus(): Promise<StreamingStatus> {
  const res = await fetch(`${API_BASE}/api/streaming/status`);
  return res.json();
}

export async function fetchDLQMessages(): Promise<{ count: number; messages: DLQMessage[] }> {
  const res = await fetch(`${API_BASE}/api/streaming/dlq?limit=15`);
  return res.json();
}

export async function fetchDataQuality(): Promise<DataQualityReport> {
  const res = await fetch(`${API_BASE}/api/data-quality`);
  return res.json();
}

export async function fetchRevenueAnalytics(): Promise<RevenueAnalytics> {
  const res = await fetch(`${API_BASE}/api/revenue?days=30`);
  return res.json();
}

export async function fetchOrders(page = 1, pageSize = 15): Promise<any> {
  const res = await fetch(`${API_BASE}/api/orders?page=${page}&page_size=${pageSize}`);
  return res.json();
}
