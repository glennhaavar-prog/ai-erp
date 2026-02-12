'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Paperclip, X } from 'lucide-react';
import FileUpload, { UploadedFile } from './FileUpload';

interface ChatInputProps {
  onSend: (message: string, files: UploadedFile[]) => void;
  isLoading: boolean;
  placeholder?: string;
}

export default function ChatInput({ 
  onSend, 
  isLoading,
  placeholder = "Skriv en melding..."
}: ChatInputProps) {
  const [input, setInput] = useState('');
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }
  }, [input]);

  const handleSend = () => {
    if ((!input.trim() && files.length === 0) || isLoading) return;

    onSend(input, files);
    setInput('');
    setFiles([]);
    setShowFileUpload(false);

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleFileUpload = () => {
    setShowFileUpload(!showFileUpload);
  };

  return (
    <div className="space-y-3">
      {/* File upload section */}
      {showFileUpload && (
        <FileUpload
          files={files}
          onFilesChange={setFiles}
        />
      )}

      {/* Input area */}
      <div className="flex gap-2">
        {/* Attachment button */}
        <button
          onClick={toggleFileUpload}
          disabled={isLoading}
          className={`
            px-3 py-3 rounded-xl transition-colors flex-shrink-0
            ${showFileUpload || files.length > 0
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-muted-foreground hover:bg-muted/80'
            }
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
          title="Vedlegg"
        >
          {files.length > 0 ? (
            <div className="relative">
              <Paperclip className="w-5 h-5" />
              <div className="absolute -top-1 -right-1 w-4 h-4 bg-primary-foreground text-primary rounded-full flex items-center justify-center text-xs font-bold">
                {files.length}
              </div>
            </div>
          ) : (
            <Paperclip className="w-5 h-5" />
          )}
        </button>

        {/* Text input */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isLoading}
            rows={1}
            className="
              w-full px-4 py-3 bg-background border border-border rounded-xl 
              focus:outline-none focus:ring-2 focus:ring-primary 
              disabled:opacity-50 disabled:cursor-not-allowed 
              text-sm resize-none overflow-hidden
            "
          />
        </div>

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={(!input.trim() && files.length === 0) || isLoading}
          className="
            px-6 py-3 bg-primary text-primary-foreground rounded-xl 
            hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed 
            transition-colors flex items-center gap-2 font-medium flex-shrink-0
          "
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="hidden sm:inline">Sender...</span>
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              <span className="hidden sm:inline">Send</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
