import axios from 'axios';
import { ReviewItem, ChatMessage, ReviewQueueFilters } from '@/types/review-queue';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types for correction payload
export interface BookingEntryCorrection {
  account_number: string;
  vat_code?: string;
  amount?: number;
  description?: string;
}

export interface CorrectItemPayload {
  bookingEntries: BookingEntryCorrection[];
  notes?: string;
}

export interface ApproveResponse {
  id: string;
  status: string;
  updated_at: string;
  message: string;
  voucher?: {
    id: string;
    voucher_number: string;
    total_debit: number;
    total_credit: number;
    is_balanced: boolean;
    lines_count: number;
  };
  feedback_recorded: boolean;
}

export interface ReviewQueueResponse {
  items: ReviewItem[];
  total: number;
  page: number;
  page_size: number;
}

export const reviewQueueApi = {
  // Get all review items
  getReviewItems: async (filters?: ReviewQueueFilters): Promise<ReviewQueueResponse> => {
    const { data } = await api.get('/api/review-queue/', { params: filters });
    return data;
  },

  // Get single review item
  getReviewItem: async (id: string): Promise<ReviewItem> => {
    const { data } = await api.get(`/api/review-queue/${id}`);
    return data;
  },

  // Approve item
  approveItem: async (id: string, notes?: string): Promise<ApproveResponse> => {
    const { data } = await api.post(`/api/review-queue/${id}/approve`, { notes });
    return data;
  },

  // Correct item
  correctItem: async (id: string, corrections: CorrectItemPayload): Promise<ApproveResponse> => {
    const { data } = await api.post(`/api/review-queue/${id}/correct`, corrections);
    return data;
  },

  // Get queue statistics
  getStats: async (clientId?: string): Promise<{
    pending: number;
    approved: number;
    corrected: number;
    total_resolved: number;
    average_confidence: number;
    escalation_rate: number;
    auto_approval_rate: number;
  }> => {
    const { data } = await api.get('/api/review-queue/stats', {
      params: clientId ? { client_id: clientId } : undefined
    });
    return data;
  },

  // Send chat message
  sendChatMessage: async (id: string, message: string): Promise<ChatMessage> => {
    const { data } = await api.post(`/api/review-queue/${id}/chat`, { message });
    return data;
  },

  // Get chat history
  getChatHistory: async (id: string): Promise<ChatMessage[]> => {
    const { data } = await api.get(`/api/review-queue/${id}/chat`);
    return data;
  },
};

export default reviewQueueApi;
