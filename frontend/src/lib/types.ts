export type User = {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "editor" | "viewer";
  is_active: boolean;
};

export type Connector = {
  id: string;
  name: string;
  connector_type: string;
  config_encrypted: Record<string, unknown>;
  status: string;
  last_tested_at: string | null;
};

export type ConnectorSchema = {
  name: string;
  asset_names: string[];
};

export type ConnectorScope = {
  schemas: string[];
  tables: Record<string, string[]>;
};

export type Column = {
  id: string;
  name: string;
  data_type: string;
  ordinal_position: number;
  nullable: boolean;
  description: string | null;
  standard_format: string | null;
  sample_values: unknown[];
  tags: string[];
  classifications: string[];
  completeness_score: number | null;
  uniqueness_score: number | null;
  consistency_score: number | null;
  accuracy_score: number | null;
};

export type Asset = {
  id: string;
  name: string;
  source_path: string;
  asset_type: string;
  schema_name: string | null;
  description: string | null;
  row_count: number | null;
  dq_score: number | null;
  last_scanned_at: string | null;
  columns?: Column[];
};

export type Scan = {
  id: string;
  connector_ids: string[];
  scan_type: string;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  assets_scanned: number;
  columns_scanned: number;
  dq_issues_raised: number;
  policies_applied: number;
  schedule_cron: string | null;
  errors: unknown[];
};

export type GlossaryTerm = {
  id: string;
  term: string;
  definition: string;
  synonyms: string[];
  related_term_ids: string[];
  linked_asset_ids: string[];
  linked_column_ids: string[];
  status: string;
  steward_id: string | null;
  created_at: string;
  updated_at: string;
};

export type GlossarySuggestion = {
  term_id: string;
  term: string;
  resource_type: "asset" | "column" | string;
  resource_id: string;
  resource_name: string;
  confidence: number;
};

export type LineageEdge = {
  id: string;
  upstream_asset_id: string;
  downstream_asset_id: string;
  source_type: string;
  confidence: number | null;
  edge_metadata: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
};

export type LineageNode = {
  id: string;
  name: string;
  source_path: string;
  dq_score: number | null;
  classifications: string[];
};

export type LineageGraph = {
  nodes: LineageNode[];
  edges: LineageEdge[];
};

export type DQScore = {
  asset_id: string;
  asset_name: string;
  source_path: string;
  dq_score: number | null;
  last_scanned_at: string | null;
};

export type DQIssue = {
  id: string;
  asset_id: string;
  column_id: string | null;
  metric_name: string;
  severity: "warning" | "critical" | string;
  status: "open" | "resolved" | string;
  delta_value: number | null;
  current_score: number | null;
  previous_score: number | null;
  resolution_note: string | null;
};

export type Policy = {
  id: string;
  name: string;
  policy_type: string;
  status: "draft" | "active" | "disabled" | string;
  rules: Array<Record<string, unknown>>;
  action: Record<string, unknown>;
  created_by_id: string | null;
  last_run_at: string | null;
};

export type ClassificationLabel = {
  id: string;
  name: string;
  color_key: string;
  description: string | null;
  masks_samples: boolean;
};

export type GovernanceCoverage = {
  pii_columns: number;
  gdpr_assets: number;
  unclassified_assets: number;
  fully_governed_assets: number;
  total_assets: number;
  total_columns: number;
};

export type AuditLog = {
  id: string;
  user_id: string | null;
  user_email: string | null;
  user_name: string | null;
  event_type: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  event_metadata: Record<string, unknown>;
  created_at: string;
};

export type NotificationSetting = {
  id: string;
  channel: "email" | "slack" | string;
  target: string;
  enabled: boolean;
  events: string[];
  created_at: string;
  updated_at: string;
};

export type ApiResponse<T> = {
  data: T;
  meta: Record<string, unknown>;
};
