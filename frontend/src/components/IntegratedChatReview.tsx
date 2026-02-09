'use client';

import React, { useState, useEffect, useRef } from 'react';
import { ReviewItem, ReviewStatus, Priority } from '@/types/review-queue';
import clsx from 'clsx';
import { mockReviewItems } from '@/utils/mock-data';
import { chatApi } from '@/api/chat';
import { ClientSafeTimestamp } from '@/lib/date-utils';

interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  data?: any;
}

// Generate a stable client ID for the session
const getClientId = () => {
  if (typeof window !== 'undefined') {
    let clientId = localStorage.getItem('kontali_client_id');
    if (!clientId) {
      // Generate a valid UUID v4
      clientId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      });
      localStorage.setItem('kontali_client_id', clientId);
    }
    return clientId;
  }
  return 'default-client-id';
};

export const IntegratedChatReview: React.FC = () => {
  const [items, setItems] = useState<ReviewItem[]>(mockReviewItems);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      role: 'system',
      content: '👋 Hei! Jeg kan hjelpe deg med å administrere fakturaer. Prøv kommandoer som "show review queue", "approve [id]", "reject [id]".\n\nTips: Toggle "API Mode" for å bruke den virkelige databasen.',
      timestamp: new Date().toISOString(),
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [useMockData, setUseMockData] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [compactView, setCompactView] = useState(false);
  const [clientId] = useState(getClientId());

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  // Filter pending reviews
  const pendingReviews = items.filter(item => item.status === 'pending');

  const getPriorityColor = (priority: Priority) => {
    switch (priority) {
      case 'high': return 'text-red-400';
      case 'medium': return 'text-yellow-400';
      case 'low': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  const getPriorityBg = (priority: Priority) => {
    switch (priority) {
      case 'high': return 'bg-red-500/10 border-red-500/30';
      case 'medium': return 'bg-yellow-500/10 border-yellow-500/30';
      case 'low': return 'bg-green-500/10 border-green-500/30';
      default: return 'bg-gray-500/10 border-gray-500/30';
    }
  };

  const processCommand = async (command: string): Promise<ChatMessage> => {
    const cmd = command.toLowerCase().trim();

    // show reviews
    if (cmd === 'show reviews' || cmd === 'reviews' || cmd === 'list') {
      const reviewsText = pendingReviews.map((item, idx) => 
        `${idx + 1}. [${item.id.slice(0, 8)}] ${item.supplier} - ${item.amount.toLocaleString('nb-NO')} kr (${item.priority})`
      ).join('\n');

      return {
        role: 'assistant',
        content: pendingReviews.length > 0 
          ? `📋 **${pendingReviews.length} fakturaer venter på godkjenning:**\n\n${reviewsText}`
          : '✅ Ingen fakturaer venter på godkjenning!',
        timestamp: new Date().toISOString(),
        data: { reviews: pendingReviews },
      };
    }

    // status
    if (cmd === 'status') {
      const stats = {
        total: items.length,
        pending: items.filter(i => i.status === 'pending').length,
        approved: items.filter(i => i.status === 'approved').length,
        rejected: items.filter(i => i.status === 'rejected').length,
        corrected: items.filter(i => i.status === 'corrected').length,
      };

      return {
        role: 'assistant',
        content: `📊 **Status oversikt:**\n\n` +
          `• Total: ${stats.total} fakturaer\n` +
          `• ⏳ Venter: ${stats.pending}\n` +
          `• ✅ Godkjent: ${stats.approved}\n` +
          `• ❌ Avvist: ${stats.rejected}\n` +
          `• ✏️ Korrigert: ${stats.corrected}`,
        timestamp: new Date().toISOString(),
        data: stats,
      };
    }

    // approve [id]
    const approveMatch = cmd.match(/^approve\s+(.+)$/);
    if (approveMatch) {
      const idPrefix = approveMatch[1].trim();
      const item = items.find(i => i.id.toLowerCase().startsWith(idPrefix.toLowerCase()) && i.status === 'pending');
      
      if (!item) {
        return {
          role: 'assistant',
          content: `❌ Fant ingen faktura med ID som starter med "${idPrefix}" eller den er allerede behandlet.`,
          timestamp: new Date().toISOString(),
        };
      }

      // Simulate approval
      setItems(items.map(i => 
        i.id === item.id 
          ? { ...i, status: 'approved' as ReviewStatus, reviewedAt: new Date().toISOString(), reviewedBy: 'chat-user' }
          : i
      ));

      return {
        role: 'assistant',
        content: `✅ **Faktura godkjent!**\n\n` +
          `• Leverandør: ${item.supplier}\n` +
          `• Beløp: ${item.amount.toLocaleString('nb-NO')} kr\n` +
          `• Fakturanr: ${item.invoiceNumber || 'N/A'}`,
        timestamp: new Date().toISOString(),
        data: { approved: item },
      };
    }

    // reject [id] [reason]
    const rejectMatch = cmd.match(/^reject\s+(\S+)(?:\s+(.+))?$/);
    if (rejectMatch) {
      const idPrefix = rejectMatch[1].trim();
      const reason = rejectMatch[2]?.trim() || 'Ingen grunn oppgitt';
      const item = items.find(i => i.id.toLowerCase().startsWith(idPrefix.toLowerCase()) && i.status === 'pending');
      
      if (!item) {
        return {
          role: 'assistant',
          content: `❌ Fant ingen faktura med ID som starter med "${idPrefix}" eller den er allerede behandlet.`,
          timestamp: new Date().toISOString(),
        };
      }

      // Simulate rejection
      setItems(items.map(i => 
        i.id === item.id 
          ? { ...i, status: 'rejected' as ReviewStatus, reviewedAt: new Date().toISOString(), reviewedBy: 'chat-user' }
          : i
      ));

      return {
        role: 'assistant',
        content: `❌ **Faktura avvist!**\n\n` +
          `• Leverandør: ${item.supplier}\n` +
          `• Beløp: ${item.amount.toLocaleString('nb-NO')} kr\n` +
          `• Grunn: ${reason}`,
        timestamp: new Date().toISOString(),
        data: { rejected: item, reason },
      };
    }

    // help
    if (cmd === 'help' || cmd === 'hjelp') {
      return {
        role: 'assistant',
        content: `🤖 **Tilgjengelige kommandoer:**\n\n` +
          `• **show reviews** - Vis alle fakturaer som venter\n` +
          `• **status** - Vis oversikt over alle fakturaer\n` +
          `• **approve [id]** - Godkjenn en faktura\n` +
          `• **reject [id] [grunn]** - Avvis en faktura\n` +
          `• **help** - Vis denne hjelpen\n\n` +
          `Tips: Du kan bruke de første tegnene av ID-en, f.eks. "approve abc123"`,
        timestamp: new Date().toISOString(),
      };
    }

    // Unknown command - try to be helpful
    return {
      role: 'assistant',
      content: `🤔 Beklager, jeg forstod ikke kommandoen "${command}". Skriv "help" for å se tilgjengelige kommandoer.`,
      timestamp: new Date().toISOString(),
    };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    setChatMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      let response: ChatMessage;
      
      if (useMockData) {
        // Use local mock processing
        await new Promise(resolve => setTimeout(resolve, 500));
        response = await processCommand(userMessage.content);
      } else {
        // Use real API with conversation history
        const history = chatMessages
          .filter(msg => msg.role !== 'system')
          .map(msg => ({ role: msg.role, content: msg.content }));
        
        const apiResponse = await chatApi.sendMessage(
          userMessage.content, 
          clientId,
          history
        );
        
        response = {
          role: 'assistant',
          content: apiResponse.message,
          timestamp: apiResponse.timestamp,
          data: apiResponse.data,
        };
        
        // If the API returned action data, update local items
        if (apiResponse.action && apiResponse.data) {
          if (apiResponse.action === 'list_queue' && apiResponse.data.items) {
            // Update local items with server data
            console.log('Queue items from server:', apiResponse.data.items);
          }
        }
      }
      
      setChatMessages(prev => [...prev, response]);
    } catch (error) {
      console.error('Chat error:', error);
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: '❌ En feil oppstod. Vennligst prøv igjen.',
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen bg-dark-bg flex flex-col">
      {/* Header */}
      <div className="bg-dark-card border-b border-dark-border p-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-100">Kontali ERP - AI Chat</h1>
            <p className="text-sm text-gray-400 mt-1">
              Administrer fakturaer med naturlig språk
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Mode:</span>
              <button
                onClick={() => setUseMockData(!useMockData)}
                className={clsx(
                  'px-3 py-1 rounded text-xs font-medium transition-colors',
                  useMockData 
                    ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 hover:bg-yellow-500/30' 
                    : 'bg-blue-500/20 text-blue-400 border border-blue-500/30 hover:bg-blue-500/30'
                )}
                title={useMockData ? 'Using mock data (client-side)' : 'Using real API (database)'}
              >
                {useMockData ? '🎭 Mock' : '🔌 API'}
              </button>
            </div>
            <div className="text-xs text-gray-500">
              Client: {clientId.slice(0, 8)}...
            </div>
            <button
              onClick={() => setCompactView(!compactView)}
              className="px-3 py-1 bg-dark-bg border border-dark-border rounded text-xs font-medium text-gray-300 hover:bg-dark-border"
            >
              {compactView ? '📋 Vis fullstendig' : '📏 Kompakt visning'}
            </button>
          </div>
        </div>
      </div>

      {/* Main Content - 70/30 Split */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Area - 70% */}
        <div className="flex-[7] flex flex-col border-r border-dark-border">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-thin">
            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                className={clsx(
                  'flex',
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                <div
                  className={clsx(
                    'max-w-[85%] rounded-lg p-4',
                    msg.role === 'user'
                      ? 'bg-accent-blue text-white'
                      : msg.role === 'system'
                      ? 'bg-purple-500/10 border border-purple-500/30 text-purple-200'
                      : 'bg-dark-card border border-dark-border text-gray-100'
                  )}
                >
                  <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                  <div className={clsx(
                    'text-xs mt-2',
                    msg.role === 'user' ? 'text-blue-200' : 'text-gray-500'
                  )}>
                    <ClientSafeTimestamp date={msg.timestamp} format="time" />
                  </div>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-dark-card border border-dark-border rounded-lg p-4">
                  <div className="flex items-center gap-2">
                    <div className="animate-pulse">💭</div>
                    <span className="text-gray-400 text-sm">Tenker...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="border-t border-dark-border p-4 bg-dark-card">
            <div className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder='Skriv en kommando eller spørsmål... (prøv "help")'
                disabled={loading}
                className="flex-1 bg-dark-bg border border-dark-border rounded-lg px-4 py-3 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent-blue disabled:opacity-50"
                autoFocus
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="px-8 py-3 bg-accent-blue hover:bg-blue-600 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? '⏳' : '📤 Send'}
              </button>
            </div>
          </form>
        </div>

        {/* Review Queue - 30% */}
        <div className="flex-[3] flex flex-col bg-dark-card">
          {/* Header */}
          <div className="p-4 border-b border-dark-border">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-lg font-semibold text-gray-100">
                Review Queue
              </h2>
              <span className="px-2 py-1 bg-accent-blue/20 text-accent-blue rounded text-xs font-medium">
                {pendingReviews.length} venter
              </span>
            </div>
            <p className="text-xs text-gray-500">
              Fakturaer som venter på godkjenning
            </p>
          </div>

          {/* Review Items */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2 scrollbar-thin">
            {pendingReviews.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-2">✅</div>
                <div className="text-sm">Alle fakturaer er behandlet!</div>
              </div>
            ) : (
              pendingReviews.map(item => (
                <div
                  key={item.id}
                  className={clsx(
                    'p-3 rounded-lg border transition-all cursor-pointer hover:shadow-lg',
                    getPriorityBg(item.priority)
                  )}
                  onClick={() => setInput(`approve ${item.id.slice(0, 8)}`)}
                >
                  {/* Priority Badge */}
                  <div className="flex items-center justify-between mb-2">
                    <span className={clsx('text-xs font-medium uppercase', getPriorityColor(item.priority))}>
                      {item.priority}
                    </span>
                    <span className="text-[10px] text-gray-500 font-mono">
                      {item.id.slice(0, 8)}
                    </span>
                  </div>

                  {/* Supplier */}
                  <div className="font-medium text-gray-100 text-sm mb-1 truncate">
                    {item.supplier}
                  </div>

                  {/* Amount */}
                  <div className="text-xl font-bold text-gray-100 mb-2">
                    {item.amount.toLocaleString('nb-NO')} kr
                  </div>

                  {compactView ? null : (
                    <>
                      {/* Description */}
                      <div className="text-xs text-gray-400 mb-2 line-clamp-2">
                        {item.description}
                      </div>

                      {/* Confidence */}
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-dark-bg rounded-full overflow-hidden">
                          <div
                            className={clsx(
                              'h-full transition-all',
                              item.confidence >= 80 ? 'bg-green-500' :
                              item.confidence >= 60 ? 'bg-yellow-500' :
                              'bg-red-500'
                            )}
                            style={{ width: `${item.confidence}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">{item.confidence}%</span>
                      </div>

                      {/* Date */}
                      <div className="text-[10px] text-gray-600 mt-2">
                        <ClientSafeTimestamp date={item.createdAt} format="datetime" />
                      </div>
                    </>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
