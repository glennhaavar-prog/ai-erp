/**
 * Bank Reconciliation API Client
 * Module 2: Bank-to-Ledger Reconciliation
 * 
 * Backend endpoints: http://localhost:8000/api/bank-recon
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ==================== Types ====================

export interface BankTransaction {
  id: string;
  bank_account: string;
  transaction_date: string;
  description: string;
  amount: number;
  status: 'unmatched' | 'matched' | 'reviewed';
  matched_to?: string; // ledger_entry_id
  kid?: string;
  reference?: string;
  currency?: string;
}

export interface GeneralLedgerLine {
  account_number: string;
  account_name?: string;
  debit_amount: number;
  credit_amount: number;
  description?: string;
}

export interface GeneralLedger {
  id: string;
  accounting_date: string;
  voucher_number: string;
  description: string;
  lines: GeneralLedgerLine[];
  total_debit?: number;
  total_credit?: number;
  currency?: string;
}

export interface UnmatchedItemsSummary {
  bank_count: number;
  ledger_count: number;
  total_bank_amount: number;
  total_ledger_amount: number;
}

export interface UnmatchedItemsResponse {
  bank_transactions: BankTransaction[];
  ledger_entries: GeneralLedger[];
  summary: UnmatchedItemsSummary;
}

export interface MatchedItem {
  id: string;
  bank_transaction: BankTransaction;
  ledger_entry: GeneralLedger;
  match_type: 'manual' | 'auto' | 'rule';
  match_date: string;
  matched_by?: string;
  confidence?: number;
}

export interface MatchRequest {
  client_id: string;
  bank_transaction_id: string;
  ledger_entry_id: string;
  match_type: 'manual' | 'auto';
}

export interface MatchResponse {
  id: string;
  status: string;
  message: string;
}

export interface UnmatchRequest {
  client_id: string;
  bank_transaction_id: string;
  ledger_entry_id: string;
}

export interface MatchingRule {
  id: string;
  client_id: string;
  rule_type: 'kid' | 'amount' | 'description' | 'date_range';
  name: string;
  description?: string;
  conditions: Record<string, any>;
  priority: number;
  enabled: boolean;
  created_at: string;
  last_matched?: number;
}

export interface CreateRuleRequest {
  client_id: string;
  rule_type: 'kid' | 'amount' | 'description' | 'date_range';
  name: string;
  description?: string;
  conditions: Record<string, any>;
  priority: number;
}

export interface AutoMatchResponse {
  matched_count: number;
  unmatched_count: number;
  matches: MatchedItem[];
  errors?: string[];
}

// ==================== API Functions ====================

/**
 * Fetch unmatched bank transactions and ledger entries
 */
export async function fetchUnmatchedItems(
  clientId: string,
  account?: string,
  startDate?: string,
  endDate?: string
): Promise<UnmatchedItemsResponse> {
  const params = new URLSearchParams({
    client_id: clientId,
  });

  if (account) params.append('account', account);
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const response = await fetch(`${API_BASE}/api/bank-recon/unmatched?${params.toString()}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch unmatched items: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch matched items (already reconciled)
 */
export async function fetchMatchedItems(
  clientId: string,
  account?: string,
  startDate?: string,
  endDate?: string
): Promise<MatchedItem[]> {
  const params = new URLSearchParams({
    client_id: clientId,
  });

  if (account) params.append('account', account);
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const response = await fetch(`${API_BASE}/api/bank-recon/matched?${params.toString()}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch matched items: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Create a manual match between bank transaction and ledger entry
 */
export async function createMatch(data: MatchRequest): Promise<MatchResponse> {
  const response = await fetch(`${API_BASE}/api/bank-recon/match`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`Failed to create match: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Unlink a match (break the connection)
 */
export async function unmatch(data: UnmatchRequest): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE}/api/bank-recon/unmatch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`Failed to unmatch: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Trigger auto-matching algorithm
 */
export async function autoMatch(
  clientId: string,
  account?: string,
  startDate?: string,
  endDate?: string
): Promise<AutoMatchResponse> {
  const params = new URLSearchParams({
    client_id: clientId,
  });

  if (account) params.append('account', account);
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const response = await fetch(`${API_BASE}/api/bank-recon/auto-match?${params.toString()}`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`Failed to auto-match: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch matching rules
 */
export async function fetchMatchingRules(clientId: string): Promise<MatchingRule[]> {
  const response = await fetch(
    `${API_BASE}/api/bank-recon/rules?client_id=${clientId}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch rules: ${response.statusText}`);
  }

  const data = await response.json();
  return data.rules || [];
}

/**
 * Create a new matching rule
 */
export async function createMatchingRule(data: CreateRuleRequest): Promise<MatchingRule> {
  const response = await fetch(`${API_BASE}/api/bank-recon/rules`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`Failed to create rule: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Delete a matching rule
 */
export async function deleteMatchingRule(ruleId: string): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE}/api/bank-recon/rules/${ruleId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error(`Failed to delete rule: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch bank accounts for dropdown
 */
export async function fetchBankAccounts(clientId: string): Promise<Array<{ account: string; name: string }>> {
  const response = await fetch(
    `${API_BASE}/api/bank/accounts?client_id=${clientId}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch bank accounts: ${response.statusText}`);
  }

  return response.json();
}
