export type AuditAction = 'create' | 'update' | 'delete';
export type ChangedByType = 'user' | 'ai_agent' | 'system';

export interface AuditEntry {
  id: string;
  client_id: string | null;
  table_name: string;
  record_id: string;
  action: AuditAction;
  changed_by_type: ChangedByType;
  changed_by_id: string | null;
  changed_by_name: string | null;
  reason: string | null;
  timestamp: string;
  ip_address: string | null;
  user_agent: string | null;
  old_value: any;
  new_value: any;
}

export interface AuditFilters {
  start_date?: string;
  end_date?: string;
  action?: AuditAction | string;
  table_name?: string;
  changed_by_type?: ChangedByType | string;
  search?: string;
  sort_order?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
}

export interface AuditResponse {
  entries: AuditEntry[];
  pagination: {
    page: number;
    page_size: number;
    total_entries: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
  summary: {
    total_events: number;
    tables_affected: number;
    unique_users: number;
    action_breakdown: Record<string, number>;
    date_range: {
      start: string | null;
      end: string | null;
    };
    filters_applied: {
      action: string | null;
      table_name: string | null;
      changed_by_type: string | null;
      search: string | null;
    };
  };
  timestamp: string;
}

export interface AuditTable {
  table_name: string;
  event_count: number;
}
