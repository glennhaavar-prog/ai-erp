/**
 * Voucher Control API Client
 * Module 5: Bilagssplit og kontroll (Voucher Control Overview)
 * 
 * Aggregates data from ALL other modules with filtering and full audit trail visibility.
 * Backend endpoints: http://localhost:8000/api/voucher-control
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ==================== Types ====================

export type VoucherType = 
  | 'supplier_invoice' 
  | 'other_voucher' 
  | 'bank_recon' 
  | 'balance_recon';

export type TreatmentType = 
  | 'auto_approved'      // Auto-godkjent (uten berøring) 🤖
  | 'pending'            // Venter på godkjenning ⏳
  | 'corrected'          // Korrigert av regnskapsfører ✏️
  | 'rule_based'         // Godkjent via regel 📋
  | 'manager_approved';  // Godkjent av daglig leder 👤

export type VoucherStatus = 'approved' | 'pending' | 'rejected';

export type PerformedBy = 'ai' | 'accountant' | 'supervisor' | 'manager';

export interface VoucherControlItem {
  id: string;
  voucher_number: string;
  voucher_type: VoucherType;
  vendor_name?: string;
  amount: number;
  treatment_type: TreatmentType;
  ai_confidence?: number; // 0-1 scale
  status: VoucherStatus;
  created_at: string;
  processed_at?: string;
}

export interface AuditTrailEntry {
  id: string;
  action: string;
  performed_by: PerformedBy;
  user_name?: string;
  ai_confidence?: number;
  timestamp: string;
  details?: any;
}

export interface VoucherControlOverviewParams {
  clientId: string;
  treatmentType?: TreatmentType;
  voucherType?: VoucherType;
  startDate?: string;  // ISO 8601 format
  endDate?: string;    // ISO 8601 format
  limit?: number;
  offset?: number;
}

export interface VoucherControlOverviewResponse {
  items: VoucherControlItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface AuditTrailResponse {
  voucher_id: string;
  voucher_number: string;
  entries: AuditTrailEntry[];
}

// ==================== API Functions ====================

/**
 * Fetch voucher control overview with filtering
 * Aggregates data from all modules (supplier invoices, other vouchers, bank recon, balance recon)
 */
export async function fetchVoucherControlOverview(
  params: VoucherControlOverviewParams
): Promise<VoucherControlOverviewResponse> {
  const {
    clientId,
    treatmentType,
    voucherType,
    startDate,
    endDate,
    limit = 50,
    offset = 0,
  } = params;

  const queryParams = new URLSearchParams({
    client_id: clientId,
    limit: limit.toString(),
    offset: offset.toString(),
  });

  if (treatmentType) queryParams.append('treatment_type', treatmentType);
  if (voucherType) queryParams.append('voucher_type', voucherType);
  if (startDate) queryParams.append('start_date', startDate);
  if (endDate) queryParams.append('end_date', endDate);

  const response = await fetch(
    `${API_BASE}/api/voucher-control/overview?${queryParams.toString()}`
  );

  if (!response.ok) {
    // If backend not ready, return mock data for development
    if (response.status === 404) {
      console.warn('⚠️ Backend API not ready yet - using mock data');
      return getMockVoucherControlOverview(params);
    }
    throw new Error(`Failed to fetch voucher control overview: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch audit trail for a specific voucher
 * Shows complete history: AI suggestion → review → approval/correction/rejection
 */
export async function fetchVoucherAuditTrail(
  voucherId: string
): Promise<AuditTrailResponse> {
  const response = await fetch(
    `${API_BASE}/api/voucher-control/${voucherId}/audit-trail`
  );

  if (!response.ok) {
    // If backend not ready, return mock data for development
    if (response.status === 404) {
      console.warn('⚠️ Backend API not ready yet - using mock data');
      return getMockAuditTrail(voucherId);
    }
    throw new Error(`Failed to fetch audit trail: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get statistics summary
 */
export async function getVoucherControlStats(clientId: string): Promise<{
  total: number;
  by_treatment: Record<TreatmentType, number>;
  by_status: Record<VoucherStatus, number>;
  by_type: Record<VoucherType, number>;
  avg_ai_confidence: number;
}> {
  const response = await fetch(
    `${API_BASE}/api/voucher-control/stats?client_id=${clientId}`
  );

  if (!response.ok) {
    // If backend not ready, return mock data
    if (response.status === 404) {
      return {
        total: 247,
        by_treatment: {
          auto_approved: 180,
          pending: 23,
          corrected: 31,
          rule_based: 8,
          manager_approved: 5,
        },
        by_status: {
          approved: 224,
          pending: 23,
          rejected: 0,
        },
        by_type: {
          supplier_invoice: 156,
          other_voucher: 48,
          bank_recon: 32,
          balance_recon: 11,
        },
        avg_ai_confidence: 0.87,
      };
    }
    throw new Error(`Failed to fetch stats: ${response.statusText}`);
  }

  return response.json();
}

// ==================== Mock Data (for development while backend is being built) ====================

function getMockVoucherControlOverview(
  params: VoucherControlOverviewParams
): VoucherControlOverviewResponse {
  const mockItems: VoucherControlItem[] = [
    {
      id: 'vc-001',
      voucher_number: 'LF-2024-001',
      voucher_type: 'supplier_invoice',
      vendor_name: 'Telenor ASA',
      amount: 3500.00,
      treatment_type: 'auto_approved',
      ai_confidence: 0.95,
      status: 'approved',
      created_at: '2024-02-14T10:30:00Z',
      processed_at: '2024-02-14T10:30:15Z',
    },
    {
      id: 'vc-002',
      voucher_number: 'AB-2024-042',
      voucher_type: 'other_voucher',
      vendor_name: 'Reiseutlegg - Hans Hansen',
      amount: 1250.00,
      treatment_type: 'pending',
      ai_confidence: 0.72,
      status: 'pending',
      created_at: '2024-02-14T09:15:00Z',
    },
    {
      id: 'vc-003',
      voucher_number: 'LF-2024-002',
      voucher_type: 'supplier_invoice',
      vendor_name: 'Elkjøp Norge AS',
      amount: 12500.00,
      treatment_type: 'corrected',
      ai_confidence: 0.81,
      status: 'approved',
      created_at: '2024-02-14T08:45:00Z',
      processed_at: '2024-02-14T11:20:00Z',
    },
    {
      id: 'vc-004',
      voucher_number: 'BANK-2024-015',
      voucher_type: 'bank_recon',
      vendor_name: 'DNB Bankavstemming',
      amount: 5000.00,
      treatment_type: 'rule_based',
      ai_confidence: 0.88,
      status: 'approved',
      created_at: '2024-02-14T07:00:00Z',
      processed_at: '2024-02-14T07:01:00Z',
    },
    {
      id: 'vc-005',
      voucher_number: 'BAL-2024-003',
      voucher_type: 'balance_recon',
      vendor_name: 'Balansekonto 2400',
      amount: 25000.00,
      treatment_type: 'manager_approved',
      ai_confidence: 0.68,
      status: 'approved',
      created_at: '2024-02-13T16:30:00Z',
      processed_at: '2024-02-14T09:00:00Z',
    },
    {
      id: 'vc-006',
      voucher_number: 'LF-2024-003',
      voucher_type: 'supplier_invoice',
      vendor_name: 'Staples Norge AS',
      amount: 2300.00,
      treatment_type: 'auto_approved',
      ai_confidence: 0.93,
      status: 'approved',
      created_at: '2024-02-13T14:20:00Z',
      processed_at: '2024-02-13T14:20:10Z',
    },
  ];

  // Apply filters
  let filtered = mockItems;

  if (params.treatmentType) {
    filtered = filtered.filter(item => item.treatment_type === params.treatmentType);
  }

  if (params.voucherType) {
    filtered = filtered.filter(item => item.voucher_type === params.voucherType);
  }

  // Apply pagination
  const start = params.offset || 0;
  const end = start + (params.limit || 50);
  const paginated = filtered.slice(start, end);

  return {
    items: paginated,
    total: filtered.length,
    limit: params.limit || 50,
    offset: params.offset || 0,
  };
}

function getMockAuditTrail(voucherId: string): AuditTrailResponse {
  // Different mock trails based on ID
  if (voucherId === 'vc-001') {
    return {
      voucher_id: 'vc-001',
      voucher_number: 'LF-2024-001',
      entries: [
        {
          id: 'at-001-1',
          action: 'Bilag opprettet fra EHF-faktura',
          performed_by: 'ai',
          timestamp: '2024-02-14T10:30:00Z',
          details: {
            source: 'EHF Import',
            vendor: 'Telenor ASA',
          },
        },
        {
          id: 'at-001-2',
          action: 'AI-analyse: Kontokoding foreslått',
          performed_by: 'ai',
          ai_confidence: 0.95,
          timestamp: '2024-02-14T10:30:05Z',
          details: {
            account: '6800 - Kontorrekvisita',
            vat_code: '3 (25%)',
            reasoning: 'Telenor faktura, vanligvis kontorkostnader',
          },
        },
        {
          id: 'at-001-3',
          action: 'Auto-godkjent (høy konfidensgrad)',
          performed_by: 'ai',
          ai_confidence: 0.95,
          timestamp: '2024-02-14T10:30:15Z',
          details: {
            rule: 'Auto-approve if confidence > 90% and vendor known',
          },
        },
      ],
    };
  } else if (voucherId === 'vc-003') {
    return {
      voucher_id: 'vc-003',
      voucher_number: 'LF-2024-002',
      entries: [
        {
          id: 'at-003-1',
          action: 'Bilag opprettet fra EHF-faktura',
          performed_by: 'ai',
          timestamp: '2024-02-14T08:45:00Z',
          details: {
            source: 'EHF Import',
            vendor: 'Elkjøp Norge AS',
          },
        },
        {
          id: 'at-003-2',
          action: 'AI-analyse: Kontokoding foreslått',
          performed_by: 'ai',
          ai_confidence: 0.81,
          timestamp: '2024-02-14T08:45:10Z',
          details: {
            account: '6540 - Inventar og utstyr',
            vat_code: '3 (25%)',
            reasoning: 'Elkjøp - sannsynligvis utstyr',
          },
        },
        {
          id: 'at-003-3',
          action: 'Sendt til manuell gjennomgang (middels konfidensgrad)',
          performed_by: 'ai',
          timestamp: '2024-02-14T08:45:15Z',
        },
        {
          id: 'at-003-4',
          action: 'Korrigert: Konto endret til 1200 - Inventar',
          performed_by: 'accountant',
          user_name: 'Linda Regnskapsfører',
          timestamp: '2024-02-14T11:20:00Z',
          details: {
            original_account: '6540',
            new_account: '1200',
            reason: 'Dette er aktivering, ikke kostnad',
          },
        },
      ],
    };
  }

  // Default mock trail
  return {
    voucher_id: voucherId,
    voucher_number: 'MOCK-001',
    entries: [
      {
        id: 'at-default-1',
        action: 'Bilag opprettet',
        performed_by: 'ai',
        timestamp: new Date().toISOString(),
      },
    ],
  };
}
