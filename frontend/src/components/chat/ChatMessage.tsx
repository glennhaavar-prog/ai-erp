'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Bot, User, FileText, Image as ImageIcon } from 'lucide-react';
import { ClientSafeTimestamp } from '@/lib/date-utils';

export interface ChatMessageData {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  attachments?: {
    filename: string;
    content_type: string;
  }[];
}

interface ChatMessageProps {
  message: ChatMessageData;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  const getFileIcon = (contentType: string) => {
    if (contentType.startsWith('image/')) {
      return <ImageIcon className="w-4 h-4" />;
    }
    return <FileText className="w-4 h-4" />;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`flex gap-3 max-w-[85%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
          isUser 
            ? 'bg-primary/10' 
            : 'bg-muted'
        }`}>
          {isUser ? (
            <User className="w-4 h-4 text-primary" />
          ) : (
            <Bot className="w-4 h-4 text-muted-foreground" />
          )}
        </div>

        {/* Message bubble */}
        <div className="flex flex-col gap-2">
          <div className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-foreground'
          }`}>
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
            
            {/* Attachments */}
            {message.attachments && message.attachments.length > 0 && (
              <div className="mt-2 space-y-1">
                {message.attachments.map((attachment, index) => (
                  <div
                    key={index}
                    className={`flex items-center gap-2 px-2 py-1 rounded ${
                      isUser
                        ? 'bg-primary-foreground/20'
                        : 'bg-background'
                    }`}
                  >
                    {getFileIcon(attachment.content_type)}
                    <span className="text-xs truncate max-w-[200px]">
                      {attachment.filename}
                    </span>
                  </div>
                ))}
              </div>
            )}

            <p className={`text-xs mt-1 ${
              isUser 
                ? 'text-primary-foreground/60' 
                : 'text-muted-foreground'
            }`}>
              <ClientSafeTimestamp date={message.timestamp} format="time" />
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
