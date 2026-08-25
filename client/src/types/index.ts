export interface Customer {
  id: string;
  name: string;
  email: string;
  location?: string;
  segment: string;
  total_orders: number;
  total_spend: number;
  churn_risk: number;
  clv: number;
}

export interface Opportunity {
  id: string;
  merchant_id?: string;
  title: string;
  description: string;
  opportunity_type: string;
  target_segment?: string;
  audience_count: number;
  estimated_gmv: number;
  confidence: number;
  status: string;
}

export interface OfferDetails {
  offer_code: string;
  description: string;
  discount_type: string;
  discount_value: number;
  min_order_value: number;
  reasoning: string;
}

export interface PermissionGateInfo {
  status: "auto_approved" | "requires_merchant_approval" | "rejected";
  is_executable: boolean;
  policy_notes: string;
  max_allowed_discount_percentage: number;
  estimated_cost_inr: number;
  reasoning: string;
}

export interface CheckoutSession {
  order_id: string;
  customer_id: string;
  customer_name?: string;
  razorpay_order_id: string;
  amount: number;
  variant: "treatment" | "control";
  is_mock?: boolean;
}

export interface ExperimentMetrics {
  campaign_id: string;
  control_customers_count: number;
  treatment_customers_count: number;
  control_orders_count: number;
  treatment_orders_count: number;
  control_conversion_rate: number;
  treatment_conversion_rate: number;
  absolute_difference_percentage: number;
  relative_lift_display: string;
  incremental_orders_count: number;
  incremental_revenue_inr: number;
}

export interface CampaignLaunchResult {
  status: "launched" | "requires_approval";
  campaign_id?: string;
  opportunity_id?: string;
  permission_gate?: PermissionGateInfo;
  eligible_audience?: number;
  total_audience?: number;
  safe_audience_cap?: number;
  treatment_group_size?: number;
  control_group_size?: number;
  emails_dispatched?: number;
  offer?: OfferDetails;
  checkout_sessions?: CheckoutSession[];
  total_test_orders?: number;
  message?: string;
}

export interface TraceStep {
  step_name: string;
  timestamp?: string;
  step_data: Record<string, any>;
}

export interface WebhookEventRecord {
  event: string;
  payment_id?: string;
  order_id?: string;
  amount?: number;
  status?: string;
  method?: string;
  received_at?: string;
  payload?: Record<string, any>;
}

export interface ChatMessage {
  id: string;
  role: "user" | "ai";
  content: string;
  suggestedAction?: string;
  reasoning_trace?: string;
  provider_used?: string;
  tools_used?: string[];
  tool_data?: Record<string, any>;
  timestamp: string;
}

export interface AgenticStep {
  step_number: number;
  tool_name: string;
  arguments: Record<string, unknown>;
  result: Record<string, unknown>;
  step_summary: string;
}

export interface AgenticScanResponse {
  status: string;
  mode: string;
  merchant_id: string;
  session_id: string;
  plan_summary: string;
  steps_taken: AgenticStep[];
  memory_citations: Array<{ id?: string; summary: string; metadata?: Record<string, unknown> }>;
  status_detail: string;
}

export interface SnapshotData {
  merchant_id: string;
  merchant_name: string;
  customers_created: number;
  orders_created: number;
  segment_distribution?: Record<string, number>;
  sample_customers?: Customer[];
}

export interface SessionSummary {
  session_id: string;
  merchant_id: string;
  last_updated: string;
  top_opportunity: string;
  campaign_id?: string;
  total_audience: number;
  has_experiment: boolean;
  lift_display: string;
  incremental_gmv: number;
}

export interface CrossReferenceResult {
  status: string;
  current_session_id: string;
  target_session_id?: string;
  comparison_narrative: string;
  current_metrics: Record<string, any>;
  target_metrics: Record<string, any>;
  vector_memories: Array<{ id?: string; summary: string; metadata?: Record<string, any> }>;
}
