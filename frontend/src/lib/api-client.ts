/**
 * API Client for Kontali ERP
 * 
 * Production-grade API client with proper error handling,
 * type safety, and no mock data.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// Types (matching backend exactly)
// ============================================================================

export interface MultiClientTask {
  id: string;
  type: 'vendor_invoice_review' | 'bank_reconciliation' | 'customer_invoice_review';
  category: 'invoicing' | 'bank' | 'reporting';
  client_id: string;
  client_name: string;
  description: string;
  confidence: number;
  created_at: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  data: Record<string, any>;
}

export interface MultiClientDashboardResponse {
  tenant_id: string;
  total_clients: number;
  clients: Array<{
    id: string;
    name: string;
  }>;
  tasks: MultiClientTask[];
  summary: {
    total_tasks: number;
    by_category: {
      invoicing: number;
      bank: number;
      reporting: number;
    };
    by_priority: {
      low: number;
      medium: number;
      high: number;
      urgent: number;
    };
  };
}

export interface ClientStatus {
  id: string;
  name: string;
  bilag: number;      // vendor_invoice_review + customer_invoice_review
  bank: number;       // bank_reconciliation
  avstemming: number; // reporting tasks
}

// ============================================================================
// Error Handling
// ============================================================================

export class APIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `API Error: ${response.status} ${response.statusText}`;
    let details;

    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = errorData.detail;
        details = errorData;
      }
    } catch {
      // If JSON parsing fails, use default error message
    }

    throw new APIError(errorMessage, response.status, details);
  }

  try {
    return await response.json();
  } catch (error) {
    throw new APIError('Failed to parse API response', response.status);
  }
}

// ============================================================================
// Multi-Client Dashboard API
// ============================================================================

export async function fetchMultiClientDashboard(
  tenantId: string,
  category?: 'invoicing' | 'bank' | 'reporting' | 'all'
): Promise<MultiClientDashboardResponse> {
  const url = new URL(`${API_BASE_URL}/api/dashboard/multi-client/tasks`);
  url.searchParams.append('tenant_id', tenantId);
  if (category && category !== 'all') {
    url.searchParams.append('category', category);
  }

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return handleResponse<MultiClientDashboardResponse>(response);
}

/**
 * Calculate client statuses from dashboard data
 * 
 * Aggregates tasks by client and categorizes them into:
 * - bilag: invoicing tasks (vendor + customer invoices)
 * - bank: bank reconciliation tasks
 * - avstemming: reporting/compliance tasks
 */
export function calculateClientStatuses(
  dashboard: MultiClientDashboardResponse
): ClientStatus[] {
  const statusMap = new Map<string, ClientStatus>();

  // Initialize all clients with zero counts
  dashboard.clients.forEach(client => {
    statusMap.set(client.id, {
      id: client.id,
      name: client.name,
      bilag: 0,
      bank: 0,
      avstemming: 0,
    });
  });

  // Count tasks per client per category
  dashboard.tasks.forEach(task => {
    const status = statusMap.get(task.client_id);
    if (!status) return; // Skip if client not found (shouldn't happen)

    switch (task.category) {
      case 'invoicing':
        status.bilag++;
        break;
      case 'bank':
        status.bank++;
        break;
      case 'reporting':
        status.avstemming++;
        break;
    }
  });

  return Array.from(statusMap.values());
}

// ============================================================================
// Review Queue API
// ============================================================================

export interface ReviewQueueItem {
  id: string;
  vendor_invoice_id: string;
  status: 'pending' | 'approved' | 'rejected';
  confidence_score: number;
  suggested_account: string;
  suggested_vat_code: string;
  ai_reasoning: string;
  created_at: string;
  reviewed_at?: string;
}

export async function fetchReviewQueue(): Promise<ReviewQueueItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/review-queue/`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return handleResponse<ReviewQueueItem[]>(response);
}

export async function approveReviewItem(itemId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/review-queue/${itemId}/approve`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new APIError(`Failed to approve item: ${response.statusText}`, response.status);
  }
}

export async function rejectReviewItem(itemId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/review-queue/${itemId}/reject`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new APIError(`Failed to reject item: ${response.statusText}`, response.status);
  }
}

// ============================================================================
// Auto-Booking API
// ============================================================================

export interface AutoBookingStatsData {
  processed_count: number;
  auto_booked_count: number;
  review_queue_count: number;
  success_rate: number;
  escalation_rate: number;
  avg_confidence_auto_booked: number | null;
  avg_confidence_escalated: number | null;
  false_positives: number;
  false_positive_rate: number;
  period_start: string;
  period_end: string;
}

export interface AutoBookingStatsResponse {
  success: boolean;
  stats: AutoBookingStatsData;
  skattefunn_compliant: boolean;
  message?: string;
}

export interface AutoBookingStatusData {
  pending_invoices: number;
  auto_booked_today: number;
  in_review_queue: number;
  processing_available: boolean;
}

export interface AutoBookingStatusResponse {
  success: boolean;
  status: AutoBookingStatusData;
}

export interface AutoBookingHealthResponse {
  success: boolean;
  service: string;
  status: string;
  timestamp: string;
}

export interface ProcessBatchResponse {
  success: boolean;
  processed_count: number;
  auto_booked_count: number;
  review_queue_count: number;
  failed_count: number;
  results: Array<{
    invoice_id: string;
    status: string;
    error?: string;
  }>;
}

/**
 * Fetch auto-booking statistics
 */
export async function fetchAutoBookingStats(
  clientId?: string,
  days: number = 30
): Promise<AutoBookingStatsResponse> {
  const url = new URL(`${API_BASE_URL}/api/auto-booking/stats`);
  if (clientId) {
    url.searchParams.append('client_id', clientId);
  }
  url.searchParams.append('days', days.toString());

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return handleResponse<AutoBookingStatsResponse>(response);
}

/**
 * Fetch current auto-booking status
 */
export async function fetchAutoBookingStatus(clientId?: string): Promise<AutoBookingStatusResponse> {
  const url = new URL(`${API_BASE_URL}/api/auto-booking/status`);
  if (clientId) {
    url.searchParams.append('client_id', clientId);
  }

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return handleResponse<AutoBookingStatusResponse>(response);
}

/**
 * Fetch auto-booking health check
 */
export async function fetchAutoBookingHealth(): Promise<AutoBookingHealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auto-booking/health`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return handleResponse<AutoBookingHealthResponse>(response);
}

/**
 * Start batch auto-booking process
 */
export async function startAutoBookingBatch(
  clientId?: string,
  limit: number = 50
): Promise<ProcessBatchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auto-booking/process`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      client_id: clientId,
      limit: limit,
    }),
  });

  return handleResponse<ProcessBatchResponse>(response);
}

/**
 * Process single invoice
 */
export async function processSingleInvoice(invoiceId: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/auto-booking/process-single`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ invoice_id: invoiceId }),
  });

  return handleResponse<any>(response);
}
