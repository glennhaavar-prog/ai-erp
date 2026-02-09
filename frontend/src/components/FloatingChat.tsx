"use client";

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ChatWindow from './chat/ChatWindow';
import { useClient } from '@/contexts/ClientContext';

interface FloatingChatProps {
  userId?: string;
}

export function FloatingChat({ 
  userId 
}: FloatingChatProps) {
  const [isOpen, setIsOpen] = useState(false);
  
  // Get selected client from context
  const { selectedClient } = useClient();
  const clientId = selectedClient?.id;

  return (
    <>
      {/* Chat Toggle Button */}
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 w-16 h-16 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-full shadow-2xl hover:shadow-3xl transition-shadow z-50 flex items-center justify-center text-white text-2xl"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
      >
        {isOpen ? '✕' : '💬'}
      </motion.button>

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="fixed bottom-24 right-6 w-96 h-[600px] bg-white rounded-2xl shadow-2xl z-40 flex flex-col overflow-hidden border border-gray-200"
          >
            <ChatWindow clientId={clientId} userId={userId} />
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
