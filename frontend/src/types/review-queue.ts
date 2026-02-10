export type ReviewStatus = 'pending' | 'approved' | 'corrected' | 'rejected';
export type Priority = 'high' | 'medium' | 'low';

export interface BookingEntry {
  account: string;
  accountName: string;
  debit?: number;
  credit?: number;
}

export interface Pattern {
  id: string;
  description: string;
  matchCount: number;
  confidence: number;
  lastUsed: string;
}

export interface ReviewItem {
  id: string;
  type: 'invoice' | 'receipt';
  status: ReviewStatus;
  priority: Priority;
  confidence: number;
  supplier: string;
  amount: number;
  date: string;
  description: string;
  invoiceNumber?: string;
  bookingEntries: BookingEntry[];
  suggestedPatterns: Pattern[];
  createdAt: string;
  reviewedAt?: string;
  reviewedBy?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ReviewQueueFilters {
  status?: ReviewStatus;
  priority?: Priority;
  search?: string;
  client_id?: string;
}
