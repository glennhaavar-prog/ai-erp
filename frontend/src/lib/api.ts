// API client for Kontali ERP backend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Client {
  id: string;
  name: string;
  tenant_id: string;
  created_at: string;
}

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
  vendor_invoice?: {
    id: string;
    vendor_name: string;
    invoice_number: string;
    amount: number;
    invoice_date: string;
    pdf_path?: string;
  };
}

export interface BankTransaction {
  id: string;
  client_id: string;
  transaction_date: string;
  amount: number;
  description: string;
  matched: boolean;
}

export interface ClientStatus {
  id: string;
  name: string;
  bilag: number;
  bank: number;
  avstemming: number | 'pending';
}

// Fetch all clients
export async function fetchClients(): Promise<Client[]> {
  const response = await fetch(`${API_BASE_URL}/api/clients`, {
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch clients: ${response.statusText}`);
  }

  return response.json();
}

// Fetch review queue items
export async function fetchReviewQueue(): Promise<ReviewQueueItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/review-queue`, {
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch review queue: ${response.statusText}`);
  }

  return response.json();
}

// Fetch bank transactions
export async function fetchBankTransactions(clientId?: string): Promise<BankTransaction[]> {
  const url = clientId 
    ? `${API_BASE_URL}/api/bank/transactions?client_id=${clientId}`
    : `${API_BASE_URL}/api/bank/transactions`;

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch bank transactions: ${response.statusText}`);
  }

  return response.json();
}

// Calculate client status from API data
export async function fetchClientStatuses(): Promise<ClientStatus[]> {
  try {
    const [clients, reviewQueue, bankTransactions] = await Promise.all([
      fetchClients(),
      fetchReviewQueue(),
      fetchBankTransactions(),
    ]);

    // Count open items per client
    const clientStatuses: ClientStatus[] = clients.map(client => {
      const pendingBilag = reviewQueue.filter(
        item => item.status === 'pending' && item.vendor_invoice?.id
      ).length;

      const unmatchedBank = bankTransactions.filter(
        tx => tx.client_id === client.id && !tx.matched
      ).length;

      return {
        id: client.id,
        name: client.name,
        bilag: pendingBilag,
        bank: unmatchedBank,
        avstemming: 'pending', // TODO: Implement reconciliation logic
      };
    });

    return clientStatuses;
  } catch (error) {
    console.error('Failed to fetch client statuses:', error);
    throw error;
  }
}

// Approve review queue item
export async function approveReviewItem(itemId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/review-queue/${itemId}/approve`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to approve item: ${response.statusText}`);
  }
}

// Reject review queue item
export async function rejectReviewItem(itemId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/review-queue/${itemId}/reject`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to reject item: ${response.statusText}`);
  }
}
