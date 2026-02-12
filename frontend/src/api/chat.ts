import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatAttachment {
  filename: string;
  content_type: string;
  data: string; // base64
}

export interface ChatRequest {
  message: string;
  client_id: string;
  user_id: string;
  session_id: string;
  conversation_history?: ChatMessage[];
  attachments?: ChatAttachment[];
}

export interface ChatResponse {
  message: string;
  action?: string;
  data?: Record<string, any>;
  timestamp: string;
  session_id?: string;
}

export const chatApi = {
  /**
   * Send a chat message with optional attachments
   */
  sendBookingMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const { data } = await api.post<ChatResponse>('/api/chat-booking/message', request);
    return data;
  },

  /**
   * Send a chat message (legacy - for backwards compatibility)
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

/**
 * Convert file to base64
 */
export const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const result = reader.result as string;
      // Remove data URL prefix to get pure base64
      const base64 = result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = error => reject(error);
  });
};

export default chatApi;
