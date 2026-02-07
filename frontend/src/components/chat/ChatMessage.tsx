"use client";

import React from 'react';
import ReactMarkdown from 'react-markdown';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  action?: string;
  data?: any;
  timestamp?: string;
}

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';
  
  // Get status emoji based on action
  const getActionEmoji = (action?: string) => {
    if (!action) return '';
    
    const emojiMap: Record<string, string> = {
      'booking_executed': '✅',
      'suggest_booking': '💡',
      'error': '❌',
      'approve': '✅',
      'cancelled': '❌',
      'status': '📊',
      'list_invoices': '📋',
      'help': '🤖'
    };
    
    return emojiMap[action] || '';
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-white text-gray-900 border border-gray-200 shadow-sm'
        }`}
      >
        {/* Action emoji indicator */}
        {!isUser && message.action && (
          <div className="text-xs opacity-60 mb-1">
            {getActionEmoji(message.action)}
          </div>
        )}
        
        {/* Message content with markdown support */}
        <div className="prose prose-sm max-w-none text-gray-900">
          {isUser ? (
            <p className="text-white m-0 whitespace-pre-wrap">{message.content}</p>
          ) : (
            <ReactMarkdown
              components={{
                p: ({children}) => <p className="m-0 mb-2 last:mb-0 whitespace-pre-wrap">{children}</p>,
                strong: ({children}) => <strong className="font-semibold text-gray-900">{children}</strong>,
                ul: ({children}) => <ul className="my-2 ml-4 space-y-1">{children}</ul>,
                li: ({children}) => <li className="text-sm">{children}</li>,
                code: ({children}) => <code className="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono text-blue-600">{children}</code>
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>
        
        {/* Timestamp */}
        {message.timestamp && (
          <div className={`text-xs mt-2 ${isUser ? 'text-blue-100' : 'text-gray-400'}`}>
            {new Date(message.timestamp).toLocaleTimeString('nb-NO', { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </div>
        )}
        
        {/* Rich data display (optional) */}
        {!isUser && message.data && message.data.invoices && message.data.invoices.length > 0 && (
          <div className="mt-3 space-y-2">
            {message.data.invoices.slice(0, 3).map((invoice: any, idx: number) => (
              <div key={idx} className="bg-gray-50 rounded-lg p-2 text-xs border border-gray-200">
                <div className="font-medium text-gray-900">{invoice.invoice_number}</div>
                <div className="text-gray-600">{invoice.vendor} • {invoice.total_amount.toLocaleString('nb-NO')} kr</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
