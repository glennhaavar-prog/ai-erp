'use client';

import React, { createContext, useContext, useState, ReactNode, useCallback } from 'react';
import { chatApi, ChatMessage as ApiChatMessage } from '@/api/chat';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  action?: string;
  data?: Record<string, any>;
}

export interface ChatContextValue {
  module: string;  // "bank-recon" | "review-queue" | etc
  selectedItems: string[];  // IDs av valgte items
  sendMessage: (message: string) => Promise<void>;
  messages: ChatMessage[];
  loading: boolean;
  setModule: (module: string) => void;
  setSelectedItems: (items: string[]) => void;
  clearHistory: () => void;
}

const ChatContext = createContext<ChatContextValue | undefined>(undefined);

interface ChatProviderProps {
  children: ReactNode;
  initialModule?: string;
  clientId?: string;
  userId?: string;
}

export function ChatProvider({ 
  children, 
  initialModule = 'general',
  clientId = 'default-client',
  userId = 'default-user'
}: ChatProviderProps) {
  const [module, setModule] = useState<string>(initialModule);
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState<string>(() => 
    `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  );

  const sendMessage = useCallback(async (message: string) => {
    if (!message.trim()) return;

    // Add user message
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      role: 'user',
      content: message,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      // Build request payload with context
      const requestPayload = {
        message,
        context: {
          module,
          selected_items: selectedItems
        },
        client_id: clientId,
        user_id: userId,
        session_id: sessionId,
        conversation_history: messages.slice(-9).map(msg => ({
          role: msg.role,
          content: msg.content
        }))
      };

      // Call API
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/chat`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestPayload)
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      
      // Add assistant message
      const assistantMessage: ChatMessage = {
        id: `msg-${Date.now()}-assistant`,
        role: 'assistant',
        content: data.message || data.content || 'No response',
        timestamp: new Date(data.timestamp || Date.now()),
        action: data.action,
        data: data.data
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
    } catch (error) {
      console.error('Chat error:', error);
      
      // Add error message
      setMessages(prev => [...prev, {
        id: `msg-${Date.now()}-error`,
        role: 'assistant',
        content: '❌ Beklager, jeg fikk ikke kontakt med serveren. Prøv igjen.',
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  }, [module, selectedItems, messages, clientId, userId, sessionId]);

  const clearHistory = useCallback(() => {
    setMessages([]);
  }, []);

  const value: ChatContextValue = {
    module,
    selectedItems,
    sendMessage,
    messages,
    loading,
    setModule,
    setSelectedItems,
    clearHistory
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChatContext() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
}
