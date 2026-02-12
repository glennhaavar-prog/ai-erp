"use client";

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import QuickActions from './QuickActions';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  action?: string;
  data?: any;
  timestamp?: string;
}

interface ChatWindowProps {
  clientId: string;
  userId?: string;
}

export default function ChatWindow({ clientId, userId }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Generate session ID on mount
  useEffect(() => {
    const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
    
    // Add welcome message
    setMessages([{
      id: `msg-${Date.now()}`,
      role: 'assistant',
      content: "👋 Hei! Jeg er din AI bokføringsassistent.\n\nJeg kan hjelpe deg med:\n• Bokføre fakturaer\n• Vise fakturastatus\n• Godkjenne bokføringer\n• Korrigere kontoføringer\n\nSi f.eks: 'Vis meg fakturaer som venter' eller 'Bokfør faktura INV-12345'",
      timestamp: new Date().toISOString()
    }]);
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (message: string, files: any[] = []) => {
    if (!message.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat-booking/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          client_id: clientId,
          user_id: userId,
          session_id: sessionId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      
      // Add assistant message
      const assistantMessage: Message = {
        id: `msg-${Date.now()}`,
        role: 'assistant',
        content: data.message,
        action: data.action,
        data: data.data,
        timestamp: data.timestamp
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
    } catch (error) {
      console.error('Chat error:', error);
      
      // Add error message
      setMessages(prev => [...prev, {
        id: `msg-${Date.now()}`,
        role: 'assistant',
        content: '❌ Beklager, jeg fikk ikke kontakt med serveren. Prøv igjen.',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickAction = async (command: string) => {
    await sendMessage(command);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-4 rounded-t-2xl">
        <h3 className="font-semibold text-lg">Kontali AI Assistant</h3>
        <p className="text-sm text-blue-100">Bokfør fakturaer med naturlig språk</p>
      </div>

      {/* Quick Actions */}
      <QuickActions onAction={handleQuickAction} disabled={loading} />

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.map((msg, idx) => (
          <ChatMessage 
            key={idx} 
            message={{
              ...msg,
              timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date()
            }} 
          />
        ))}
        
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl px-4 py-2">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={sendMessage} isLoading={loading} />
    </div>
  );
}
