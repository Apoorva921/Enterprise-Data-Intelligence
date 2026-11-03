import {
  KPISummary,
  PipelineInfo,
  PipelineRun,
  StreamingStatus,
  DLQMessage,
  DataQualityReport,
  RevenueAnalytics,
} from '../types';

const API_BASE = (typeof window !== 'undefined' && window.location.port === '3000')
  ? 'http://localhost:8000'
  : '';

let cachedToken: string | null = null;

async function getAdminToken(): Promise<string> {
  if (cachedToken) return cachedToken;
  const authRes = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'admin', password: 'adminpassword123' }),
  });
  if (!authRes.ok) {
    throw new Error(`Authentication failed with status: ${authRes.status}`);
  }
  const authData = await authRes.json();
  cachedToken = authData.access_token;
  return cachedToken!;
}

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
  let token = await getAdminToken();
  let res = await fetch(`${API_BASE}/api/pipelines/${dagId}/trigger`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (res.status === 401) {
    cachedToken = null;
    token = await getAdminToken();
    res = await fetch(`${API_BASE}/api/pipelines/${dagId}/trigger`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  if (!res.ok) {
    let errDetail = 'Failed to execute pipeline';
    try {
      const errJson = await res.json();
      errDetail = errJson.detail || errDetail;
    } catch {
      // fallback
    }
    throw new Error(errDetail);
  }

  return res.json();
}

export async function fetchStreamingStatus(): Promise<StreamingStatus> {
  const res = await fetch(`${API_BASE}/api/streaming/status`);
  return res.json();
}

export async function fetchDLQMessages(): Promise<{ count: number; messages: DLQMessage[] }> {
  const res = await fetch(`${API_BASE}/api/streaming/dlq?limit=25`);
  return res.json();
}

export async function simulateStreamEvents(count = 25): Promise<{ status: string; events_published: number }> {
  const res = await fetch(`${API_BASE}/api/streaming/simulate?count=${count}`, {
    method: 'POST',
  });
  if (!res.ok) {
    throw new Error('Failed to simulate stream traffic');
  }
  return res.json();
}

export async function simulatePoisonEvent(): Promise<{ status: string; reason: string }> {
  const res = await fetch(`${API_BASE}/api/streaming/simulate-poison`, {
    method: 'POST',
  });
  if (!res.ok) {
    throw new Error('Failed to inject poison anomaly');
  }
  return res.json();
}

export async function fetchDataQuality(): Promise<DataQualityReport> {
  const res = await fetch(`${API_BASE}/api/data-quality`);
  return res.json();
}

export async function rerunDataQualityAudit(): Promise<DataQualityReport> {
  const res = await fetch(`${API_BASE}/api/data-quality/run`, {
    method: 'POST',
  });
  if (!res.ok) {
    throw new Error('Failed to re-run quality audit');
  }
  return res.json();
}

export async function fetchRevenueAnalytics(days = 30): Promise<RevenueAnalytics> {
  const res = await fetch(`${API_BASE}/api/revenue?days=${days}`);
  return res.json();
}

export async function fetchOrders(page = 1, pageSize = 15, status?: string, region?: string): Promise<any> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (status && status !== 'ALL') params.append('status', status);
  if (region && region !== 'ALL') params.append('region', region);
  const res = await fetch(`${API_BASE}/api/orders?${params.toString()}`);
  return res.json();
}
