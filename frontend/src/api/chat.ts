import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ChatMessage {
  role: string;
  content: string;
}

export interface ChatRequest {
  client_id: string;
  message: string;
  conversation_history?: ChatMessage[];
}

export interface ChatResponse {
  message: string;
  action?: string;
  data?: Record<string, any>;
  timestamp: string;
}

export const chatApi = {
  /**
   * Send a chat message and get a response
   */
  sendMessage: async (
    message: string, 
    clientId: string = 'default-client-id',
    conversationHistory?: ChatMessage[]
  ): Promise<ChatResponse> => {
    const { data } = await api.post<ChatResponse>('/api/chat', {
      client_id: clientId,
      message,
      conversation_history: conversationHistory,
    });
    return data;
  },

  /**
   * Get review queue for a client
   */
  getQueue: async (clientId: string): Promise<ChatResponse> => {
    const { data } = await api.get<ChatResponse>(`/api/chat/queue/${clientId}`);
    return data;
  },

  /**
   * Approve a review item
   */
  approveItem: async (itemId: string, clientId: string): Promise<ChatResponse> => {
    const { data } = await api.post<ChatResponse>(`/api/chat/approve/${itemId}?client_id=${clientId}`);
    return data;
  },

  /**
   * Reject a review item
   */
  rejectItem: async (itemId: string, clientId: string, reason?: string): Promise<ChatResponse> => {
    const { data } = await api.post<ChatResponse>(`/api/chat/reject/${itemId}?client_id=${clientId}${reason ? `&reason=${encodeURIComponent(reason)}` : ''}`);
    return data;
  },

  /**
   * Health check for chat endpoint
   */
  health: async (): Promise<{ status: string; service: string; agent_type: string; claude_configured: boolean }> => {
    const { data } = await api.get('/api/chat/health');
    return data;
  },
};

export default chatApi;
