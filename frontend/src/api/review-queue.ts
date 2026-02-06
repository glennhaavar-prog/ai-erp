import axios from 'axios';
import { ReviewItem, ChatMessage, ReviewQueueFilters } from '@/types/review-queue';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const reviewQueueApi = {
  // Get all review items
  getReviewItems: async (filters?: ReviewQueueFilters): Promise<ReviewItem[]> => {
    const { data } = await api.get('/api/review-queue', { params: filters });
    return data;
  },

  // Get single review item
  getReviewItem: async (id: string): Promise<ReviewItem> => {
    const { data } = await api.get(`/api/review-queue/${id}`);
    return data;
  },

  // Approve item
  approveItem: async (id: string): Promise<ReviewItem> => {
    const { data } = await api.post(`/api/review-queue/${id}/approve`);
    return data;
  },

  // Correct item
  correctItem: async (id: string, corrections: { bookingEntries: any[] }): Promise<ReviewItem> => {
    const { data } = await api.post(`/api/review-queue/${id}/correct`, corrections);
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
