export interface KPISummary {
  total_orders: number;
  total_revenue: number;
  avg_order_value: number;
  active_customers: number;
  completion_rate: number;
  payment_success_rate: number;
}

export interface PipelineInfo {
  id: string;
  name: string;
  schedule: string;
  layer: string;
  last_status: string;
  last_run_date: string;
  last_duration_seconds: number;
}

export interface PipelineRun {
  run_id: string;
  dag_id: string;
  execution_date: string;
  state: string;
  duration_seconds: number;
  tasks_executed: number;
  details?: string;
}

export interface StreamingStatus {
  status: string;
  live_kafka_active: boolean;
  bootstrap_servers: string;
  topics: Record<string, number>;
  consumer_groups: Record<string, any>;
  dlq_message_count: number;
}

export interface DLQMessage {
  dlq_id: string;
  topic: string;
  raw_payload: any;
  error_reason: string;
  metadata: any;
  failed_at: string;
  status: string;
}

export interface DataQualityReport {
  audit_id: string;
  generated_at: string;
  is_silver_production_ready: boolean;
  bronze_audit: {
    suite_name: string;
    layer: string;
    quality_score_pct: number;
    total_checks: number;
    passed_checks: number;
    failed_checks: number;
    expectations: Array<{
      expectation: string;
      column: string;
      success: boolean;
      details?: string;
      unexpected_count?: number;
    }>;
  };
  silver_audit: {
    suite_name: string;
    layer: string;
    quality_score_pct: number;
    total_checks: number;
    passed_checks: number;
    failed_checks: number;
    expectations: Array<{
      expectation: string;
      column: string;
      success: boolean;
      details?: string;
      unexpected_count?: number;
    }>;
  };
  quarantine_summary: {
    total_quarantined_records: number;
    entities: Record<string, {
      count: number;
      top_rejection_reasons: Record<string, number>;
    }>;
  };
}

export interface RevenueAnalytics {
  daily_trends: Array<{
    order_day: string;
    total_orders: number;
    completed_orders: number;
    total_gross_revenue: number;
    avg_order_value: number;
  }>;
  regional_breakdown: Array<{
    region: string;
    total_orders: number;
    total_revenue: number;
  }>;
  category_breakdown: Array<{
    category: string;
    product_count: number;
    avg_margin_pct: number;
  }>;
}
