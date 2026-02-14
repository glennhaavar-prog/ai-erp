/**
 * API Client for Reconciliations Module
 * Module 3: Balance Account Reconciliation
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// Types
// ============================================================================

export interface Reconciliation {
  id: string;
  client_id: string;
  account_id: string;
  account_number: string;
  account_name: string;
  period_start: string; // ISO datetime
  period_end: string;
  opening_balance: number; // Auto-calculated from ledger
  closing_balance: number; // Auto-calculated from ledger
  expected_balance: number | null; // Manual input
  difference: number | null; // Auto-calculated: closing - expected
  status: 'pending' | 'reconciled' | 'approved';
  reconciliation_type: 'bank' | 'receivables' | 'payables' | 'inventory' | 'other';
  notes: string | null;
  created_at: string;
  reconciled_at: string | null;
  reconciled_by: string | null;
  approved_at: string | null;
  approved_by: string | null;
  attachments_count: number;
}

export interface ReconciliationAttachment {
  id: string;
  reconciliation_id: string;
  filename: string;
  file_size: number;
  content_type: string;
  storage_path: string;
  uploaded_at: string;
  uploaded_by: string | null;
}

export interface ReconciliationListResponse {
  reconciliations: Reconciliation[];
  total: number;
}

export interface ReconciliationFilters {
  client_id: string;
  period_start?: string;
  period_end?: string;
  status?: 'pending' | 'reconciled' | 'approved';
  reconciliation_type?: 'bank' | 'receivables' | 'payables' | 'inventory' | 'other';
}

export interface CreateReconciliationRequest {
  client_id: string;
  account_id: string;
  period_start: string;
  period_end: string;
  reconciliation_type: 'bank' | 'receivables' | 'payables' | 'inventory' | 'other';
  expected_balance?: number;
  notes?: string;
}

export interface UpdateReconciliationRequest {
  expected_balance?: number;
  notes?: string;
  status?: 'pending' | 'reconciled';
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
// Reconciliation CRUD
// ============================================================================

/**
 * Fetch list of reconciliations with optional filters
 */
export async function fetchReconciliations(
  filters: ReconciliationFilters
): Promise<Reconciliation[]> {
  const url = new URL(`${API_BASE_URL}/api/reconciliations/`);
  
  url.searchParams.append('client_id', filters.client_id);
  if (filters.period_start) url.searchParams.append('period_start', filters.period_start);
  if (filters.period_end) url.searchParams.append('period_end', filters.period_end);
  if (filters.status) url.searchParams.append('status', filters.status);
  if (filters.reconciliation_type) url.searchParams.append('reconciliation_type', filters.reconciliation_type);

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Backend returns { reconciliations: [...], count: number }
  // Extract just the reconciliations array
  const data = await handleResponse<{ reconciliations: Reconciliation[]; count: number }>(response);
  return data.reconciliations || [];
}

/**
 * Fetch single reconciliation by ID
 */
export async function fetchReconciliation(id: string): Promise<Reconciliation> {
  const response = await fetch(`${API_BASE_URL}/api/reconciliations/${id}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return handleResponse<Reconciliation>(response);
}

/**
 * Create new reconciliation
 */
export async function createReconciliation(
  data: CreateReconciliationRequest
): Promise<Reconciliation> {
  const response = await fetch(`${API_BASE_URL}/api/reconciliations/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  return handleResponse<Reconciliation>(response);
}

/**
 * Update reconciliation
 */
export async function updateReconciliation(
  id: string,
  data: UpdateReconciliationRequest
): Promise<Reconciliation> {
  const response = await fetch(`${API_BASE_URL}/api/reconciliations/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  return handleResponse<Reconciliation>(response);
}

/**
 * Approve reconciliation (status must be 'reconciled')
 */
export async function approveReconciliation(
  id: string,
  user_id: string
): Promise<Reconciliation> {
  const response = await fetch(`${API_BASE_URL}/api/reconciliations/${id}/approve?user_id=${user_id}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return handleResponse<Reconciliation>(response);
}

// ============================================================================
// Attachments
// ============================================================================

/**
 * Upload attachment to reconciliation
 */
export async function uploadAttachment(
  reconciliationId: string,
  file: File
): Promise<ReconciliationAttachment> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(
    `${API_BASE_URL}/api/reconciliations/${reconciliationId}/attachments`,
    {
      method: 'POST',
      body: formData,
    }
  );

  return handleResponse<ReconciliationAttachment>(response);
}

/**
 * Fetch attachments for a reconciliation
 */
export async function fetchAttachments(
  reconciliationId: string
): Promise<ReconciliationAttachment[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/reconciliations/${reconciliationId}/attachments`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  return handleResponse<ReconciliationAttachment[]>(response);
}

/**
 * Delete attachment
 */
export async function deleteAttachment(
  reconciliationId: string,
  attachmentId: string
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/reconciliations/${reconciliationId}/attachments/${attachmentId}`,
    {
      method: 'DELETE',
    }
  );

  if (!response.ok) {
    throw new APIError('Failed to delete attachment', response.status);
  }
}
