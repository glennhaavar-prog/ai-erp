"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, Command } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

const SUGGESTIONS = [
  'Vis meg fakturaer som venter',
  'Bokfør faktura INV-12345',
  'Hva er status på alle fakturaer?',
  'Vis fakturaer med lav confidence',
  'help'
];

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);

  // Filter suggestions based on input
  const filteredSuggestions = SUGGESTIONS.filter(s => 
    s.toLowerCase().includes(message.toLowerCase())
  );

  const handleSend = () => {
    if (!message.trim() || disabled) return;
    
    onSend(message);
    setMessage('');
    setShowSuggestions(false);
    setSelectedSuggestion(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    } else if (e.key === '/') {
      if (message === '') {
        e.preventDefault();
        setShowSuggestions(true);
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    } else if (showSuggestions && filteredSuggestions.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedSuggestion(prev => 
          prev < filteredSuggestions.length - 1 ? prev + 1 : 0
        );
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedSuggestion(prev => 
          prev > 0 ? prev - 1 : filteredSuggestions.length - 1
        );
      } else if (e.key === 'Tab' || e.key === 'Enter') {
        if (selectedSuggestion >= 0) {
          e.preventDefault();
          setMessage(filteredSuggestions[selectedSuggestion]);
          setShowSuggestions(false);
          setSelectedSuggestion(-1);
        }
      }
    }
  };

  const selectSuggestion = (suggestion: string) => {
    setMessage(suggestion);
    setShowSuggestions(false);
    setSelectedSuggestion(-1);
    inputRef.current?.focus();
  };

  useEffect(() => {
    if (message === '/') {
      setShowSuggestions(true);
    } else if (message === '') {
      setShowSuggestions(false);
    }
  }, [message]);

  return (
    <div className="border-t border-gray-200 p-4 bg-white rounded-b-2xl relative">
      {/* Suggestions dropdown */}
      {showSuggestions && filteredSuggestions.length > 0 && (
        <div className="absolute bottom-full left-0 right-0 mb-2 mx-4 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
          <div className="p-2 border-b border-gray-100 text-xs text-gray-500 flex items-center gap-1">
            <Command className="w-3 h-3" />
            Kommandoer
          </div>
          {filteredSuggestions.map((suggestion, idx) => (
            <button
              key={idx}
              onClick={() => selectSuggestion(suggestion)}
              className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-50 transition-colors ${
                selectedSuggestion === idx ? 'bg-blue-50 text-blue-600' : 'text-gray-700'
              }`}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      {/* Input field */}
      <div className="flex space-x-2">
        <input
          ref={inputRef}
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Skriv melding... (/ for kommandoer)"
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          disabled={disabled}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !message.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          <Send className="w-4 h-4" />
          <span className="hidden sm:inline">Send</span>
        </button>
      </div>

      {/* Hint */}
      <div className="text-xs text-gray-400 mt-2 flex items-center gap-1">
        <Command className="w-3 h-3" />
        Trykk <kbd className="px-1 py-0.5 bg-gray-100 rounded text-xs">/</kbd> for kommandoer
      </div>
    </div>
  );
}
