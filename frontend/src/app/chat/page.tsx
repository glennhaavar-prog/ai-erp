'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, Trash2, Loader2, AlertCircle, RotateCcw } from 'lucide-react';
import ChatMessage, { ChatMessageData } from '@/components/chat/ChatMessage';
import ChatInput from '@/components/chat/ChatInput';
import { UploadedFile } from '@/components/chat/FileUpload';
import { chatApi, fileToBase64, ChatAttachment, ChatMessage as APIChatMessage } from '@/api/chat';
import { useClient } from '@/contexts/ClientContext';

const STORAGE_KEY = 'kontali-chat-session';

interface StoredSession {
  session_id: string;
  messages: ChatMessageData[];
  client_id: string;
}

export default function ChatPage() {
  const { selectedClient } = useClient();
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [sessionId, setSessionId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load session from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const session: StoredSession = JSON.parse(stored);
        // Only restore if same client
        if (session.client_id === selectedClient?.id) {
          setMessages(session.messages.map(msg => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          })));
          setSessionId(session.session_id);
        }
      } catch (err) {
        console.error('Failed to parse stored session:', err);
      }
    }

    // Generate session ID if not exists
    if (!sessionId) {
      setSessionId(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
    }
  }, [selectedClient?.id]);

  // Save session to localStorage whenever messages change
  useEffect(() => {
    if (messages.length > 0 && selectedClient?.id) {
      const session: StoredSession = {
        session_id: sessionId,
        messages,
        client_id: selectedClient.id,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    }
  }, [messages, sessionId, selectedClient?.id]);

  const handleSend = async (message: string, files: UploadedFile[]) => {
    if ((!message.trim() && files.length === 0) || isLoading) return;

    setError(null);

    // Create user message
    const userMessage: ChatMessageData = {
      id: Date.now().toString(),
      role: 'user',
      content: message || '(Vedlagt fil)',
      timestamp: new Date(),
      attachments: files.map(f => ({
        filename: f.file.name,
        content_type: f.file.type,
      })),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Convert files to base64
      const attachments: ChatAttachment[] = await Promise.all(
        files.map(async (f) => ({
          filename: f.file.name,
          content_type: f.file.type,
          data: await fileToBase64(f.file),
        }))
      );

      // Prepare conversation history
      const conversation_history: APIChatMessage[] = messages.map(msg => ({
        role: msg.role,
        content: msg.content,
      }));

      // Send to API
      const response = await chatApi.sendBookingMessage({
        message: message || '',
        client_id: selectedClient?.id || 'default-client',
        user_id: 'current-user', // TODO: Get from auth context
        session_id: sessionId,
        conversation_history,
        attachments: attachments.length > 0 ? attachments : undefined,
      });

      // Update session ID if provided
      if (response.session_id) {
        setSessionId(response.session_id);
      }

      // Add assistant response
      const assistantMessage: ChatMessageData = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(response.timestamp),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      console.error('Chat error:', err);
      
      const errorMessage = err.response?.data?.detail 
        || err.message 
        || 'Det oppstod en feil ved sending av meldingen.';
      
      setError(errorMessage);

      // Add error message to chat
      const errorChatMessage: ChatMessageData = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `❌ Feil: ${errorMessage}`,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorChatMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearConversation = () => {
    if (confirm('Er du sikker på at du vil slette hele samtalen?')) {
      setMessages([]);
      setSessionId(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  const handleRetry = () => {
    setError(null);
  };

  // Quick action suggestions
  const quickActions = [
    'Hva er status på klient?',
    'Vis leverandørreskontro',
    'Bokfør denne fakturen',
  ];

  const handleQuickAction = (action: string) => {
    handleSend(action, []);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-background">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border bg-card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <Bot className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-foreground">AI Chat med Kontali</h1>
              <p className="text-sm text-muted-foreground">
                {selectedClient?.name || 'Ingen klient valgt'} • Chat-assistent
              </p>
            </div>
          </div>
          
          {messages.length > 0 && (
            <button
              onClick={handleClearConversation}
              className="px-3 py-2 text-sm text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg transition-colors flex items-center gap-2"
            >
              <Trash2 className="w-4 h-4" />
              <span className="hidden sm:inline">Tøm samtale</span>
            </button>
          )}
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-md">
              <Bot className="w-20 h-20 mx-auto mb-6 text-muted-foreground/30" />
              <h2 className="text-2xl font-semibold mb-3">Hei! Jeg er Kontali AI</h2>
              <p className="text-muted-foreground mb-6">
                Jeg kan hjelpe deg med bokføring, spørsmål om klienter, og mye mer.
                Last opp bilag og si hva du vil gjøre!
              </p>
              
              {/* Quick actions */}
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground mb-3">Prøv for eksempel:</p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {quickActions.map((action, index) => (
                    <button
                      key={index}
                      onClick={() => handleQuickAction(action)}
                      className="px-4 py-2 bg-muted hover:bg-muted/80 rounded-lg text-sm transition-colors"
                    >
                      {action}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4 max-w-4xl mx-auto">
            <AnimatePresence>
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
            </AnimatePresence>

            {/* Loading indicator */}
            {isLoading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex justify-start"
              >
                <div className="flex gap-3 max-w-[85%]">
                  <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                    <Bot className="w-4 h-4 text-muted-foreground" />
                  </div>
                  <div className="bg-muted rounded-2xl px-4 py-3">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-muted-foreground/40 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-muted-foreground/40 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-muted-foreground/40 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Error banner */}
      {error && (
        <div className="px-6 py-3 bg-destructive/10 border-t border-destructive/20">
          <div className="flex items-center justify-between max-w-4xl mx-auto">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">{error}</span>
            </div>
            <button
              onClick={handleRetry}
              className="px-3 py-1 text-sm text-destructive hover:bg-destructive/20 rounded transition-colors flex items-center gap-1"
            >
              <RotateCcw className="w-3 h-3" />
              Lukk
            </button>
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="px-6 py-4 border-t border-border bg-card">
        <div className="max-w-4xl mx-auto">
          <ChatInput
            onSend={handleSend}
            isLoading={isLoading}
            placeholder="Skriv en melding..."
          />
        </div>
      </div>
    </div>
  );
}
