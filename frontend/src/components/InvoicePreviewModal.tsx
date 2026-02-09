'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle, XCircle, MessageSquare, FileText } from 'lucide-react';

interface Invoice {
  id: string;
  vendor_name: string;
  invoice_number: string;
  amount: number;
  suggested_account: string;
  suggested_vat_code: string;
  confidence_score: number;
  ai_reasoning: string;
  pdf_url?: string;
}

interface InvoicePreviewModalProps {
  invoice: Invoice | null;
  isOpen: boolean;
  onClose: () => void;
  onApprove: (invoiceId: string) => void;
  onReject: (invoiceId: string) => void;
}

export default function InvoicePreviewModal({
  invoice,
  isOpen,
  onClose,
  onApprove,
  onReject,
}: InvoicePreviewModalProps) {
  const [chatMessages, setChatMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([]);
  const [chatInput, setChatInput] = useState('');

  if (!invoice) return null;

  const handleSendMessage = () => {
    if (!chatInput.trim()) return;
    
    setChatMessages([...chatMessages, { role: 'user', content: chatInput }]);
    // TODO: Send to AI backend
    setChatInput('');
  };

  const confidenceColor = invoice.confidence_score >= 85 ? 'text-success' : invoice.confidence_score >= 60 ? 'text-warning' : 'text-destructive';
  const confidenceBg = invoice.confidence_score >= 85 ? 'bg-success/10' : invoice.confidence_score >= 60 ? 'bg-warning/10' : 'bg-destructive/10';

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            transition={{ type: 'spring', damping: 20, stiffness: 300 }}
            className="relative w-full max-w-7xl h-[90vh] bg-card border border-border rounded-2xl shadow-2xl flex overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={onClose}
              className="absolute top-4 right-4 z-10 p-2 rounded-full bg-muted hover:bg-muted/80 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Left: Chat Interface */}
            <div className="w-1/2 border-r border-border flex flex-col">
              {/* Chat Header */}
              <div className="p-6 border-b border-border">
                <h3 className="text-xl font-semibold flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-primary" />
                  Chat med AI-agent
                </h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Diskuter bokføring av {invoice.vendor_name}
                </p>
              </div>

              {/* AI Reasoning Card */}
              <div className="p-6 bg-muted/30 border-b border-border">
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${confidenceBg}`}>
                    <FileText className={`w-5 h-5 ${confidenceColor}`} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-medium">AI-resonnement</span>
                      <span className={`px-2 py-0.5 text-xs rounded-full ${confidenceBg} ${confidenceColor}`}>
                        {invoice.confidence_score}% sikkerhet
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {invoice.ai_reasoning}
                    </p>
                  </div>
                </div>
              </div>

              {/* Chat Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {chatMessages.length === 0 ? (
                  <div className="text-center text-muted-foreground py-12">
                    <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-20" />
                    <p>Ingen meldinger ennå. Start en samtale!</p>
                  </div>
                ) : (
                  chatMessages.map((msg, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                        msg.role === 'user' 
                          ? 'bg-primary text-primary-foreground' 
                          : 'bg-muted text-foreground'
                      }`}>
                        {msg.content}
                      </div>
                    </motion.div>
                  ))
                )}
              </div>

              {/* Chat Input */}
              <div className="p-6 border-t border-border">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Skriv melding til AI-agent..."
                    className="flex-1 px-4 py-3 bg-muted border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!chatInput.trim()}
                    className="px-6 py-3 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Send
                  </button>
                </div>
              </div>
            </div>

            {/* Right: Invoice Preview + Actions */}
            <div className="w-1/2 flex flex-col">
              {/* Invoice Header */}
              <div className="p-6 border-b border-border">
                <h3 className="text-2xl font-bold">{invoice.vendor_name}</h3>
                <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                  <span>Faktura: {invoice.invoice_number}</span>
                  <span>•</span>
                  <span className="font-semibold text-foreground">
                    {invoice.amount.toLocaleString('no-NO', { style: 'currency', currency: 'NOK' })}
                  </span>
                </div>
              </div>

              {/* Suggested Booking */}
              <div className="p-6 bg-muted/30 border-b border-border space-y-3">
                <h4 className="font-medium">Foreslått bokføring</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs uppercase tracking-wider text-muted-foreground">Konto</label>
                    <p className="font-mono font-semibold">{invoice.suggested_account}</p>
                  </div>
                  <div>
                    <label className="text-xs uppercase tracking-wider text-muted-foreground">MVA-kode</label>
                    <p className="font-mono font-semibold">{invoice.suggested_vat_code}</p>
                  </div>
                </div>
              </div>

              {/* PDF Preview */}
              <div className="flex-1 bg-muted/10 p-6 overflow-auto">
                {invoice.pdf_url ? (
                  <iframe
                    src={invoice.pdf_url}
                    className="w-full h-full border border-border rounded-lg"
                    title="Faktura PDF"
                  />
                ) : (
                  <div className="flex items-center justify-center h-full text-muted-foreground">
                    <div className="text-center">
                      <FileText className="w-16 h-16 mx-auto mb-3 opacity-20" />
                      <p>PDF-forhåndsvisning ikke tilgjengelig</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="p-6 border-t border-border flex gap-3">
                <button
                  onClick={() => onReject(invoice.id)}
                  className="flex-1 py-3 px-4 rounded-xl border-2 border-destructive text-destructive hover:bg-destructive hover:text-destructive-foreground transition-colors flex items-center justify-center gap-2 font-medium"
                >
                  <XCircle className="w-5 h-5" />
                  Avvis
                </button>
                <button
                  onClick={() => onApprove(invoice.id)}
                  className="flex-1 py-3 px-4 rounded-xl bg-success text-success-foreground hover:bg-success/90 transition-colors flex items-center justify-center gap-2 font-medium"
                >
                  <CheckCircle className="w-5 h-5" />
                  Godkjenn
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
