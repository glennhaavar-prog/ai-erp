'use client';

/**
 * Example: Review Queue with Integrated Chat
 * 
 * This demonstrates how to integrate ChatWindow into an existing module
 * with proper context management for selected items.
 */

import { useState, useEffect } from 'react';
import { ChatProvider, useChatContext } from '@/contexts/ChatContext';
import ChatWindow from '@/components/ChatWindow';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';

// Mock invoice data
interface Invoice {
  id: string;
  vendor: string;
  amount: number;
  date: string;
  status: 'pending' | 'approved' | 'rejected';
}

const MOCK_INVOICES: Invoice[] = [
  { id: 'inv-001', vendor: 'Staples AS', amount: 4500, date: '2025-02-10', status: 'pending' },
  { id: 'inv-002', vendor: 'Office Depot', amount: 2300, date: '2025-02-11', status: 'pending' },
  { id: 'inv-003', vendor: 'Amazon Business', amount: 8900, date: '2025-02-12', status: 'pending' },
  { id: 'inv-004', vendor: 'IKEA Norge', amount: 12500, date: '2025-02-13', status: 'pending' },
  { id: 'inv-005', vendor: 'Elkjøp AS', amount: 6700, date: '2025-02-14', status: 'pending' },
];

// Inner component that uses ChatContext
function ReviewQueueContent() {
  const { setSelectedItems } = useChatContext();
  const [invoices] = useState<Invoice[]>(MOCK_INVOICES);
  const [selectedInvoices, setSelectedInvoices] = useState<string[]>([]);

  // Sync selected invoices with chat context
  useEffect(() => {
    setSelectedItems(selectedInvoices);
  }, [selectedInvoices, setSelectedItems]);

  const toggleInvoice = (invoiceId: string) => {
    setSelectedInvoices(prev =>
      prev.includes(invoiceId)
        ? prev.filter(id => id !== invoiceId)
        : [...prev, invoiceId]
    );
  };

  const selectAll = () => {
    if (selectedInvoices.length === invoices.length) {
      setSelectedInvoices([]);
    } else {
      setSelectedInvoices(invoices.map(inv => inv.id));
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8 pb-32">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Gjennomgangskø
          </h1>
          <p className="text-gray-600">
            Velg fakturaer og bruk AI-assistenten til å bokføre dem
          </p>
        </div>

        {/* Actions Bar */}
        <Card className="p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="outline" onClick={selectAll}>
                {selectedInvoices.length === invoices.length ? 'Velg ingen' : 'Velg alle'}
              </Button>
              <span className="text-sm text-gray-600">
                {selectedInvoices.length} av {invoices.length} valgt
              </span>
            </div>
            <div className="flex gap-2">
              <Badge variant="outline" className="text-sm">
                💬 Spør AI for hjelp
              </Badge>
            </div>
          </div>
        </Card>

        {/* Invoice List */}
        <div className="space-y-3">
          {invoices.map((invoice) => {
            const isSelected = selectedInvoices.includes(invoice.id);
            
            return (
              <Card
                key={invoice.id}
                className={`p-4 cursor-pointer transition-all ${
                  isSelected
                    ? 'border-2 border-blue-500 bg-blue-50'
                    : 'border border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => toggleInvoice(invoice.id)}
              >
                <div className="flex items-center gap-4">
                  <Checkbox
                    checked={isSelected}
                    onCheckedChange={() => toggleInvoice(invoice.id)}
                    onClick={(e) => e.stopPropagation()}
                  />
                  
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold text-gray-900">
                          {invoice.vendor}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {invoice.id} • {new Date(invoice.date).toLocaleDateString('no-NO')}
                        </p>
                      </div>
                      
                      <div className="text-right">
                        <p className="text-lg font-bold text-gray-900">
                          {invoice.amount.toLocaleString('no-NO')} kr
                        </p>
                        <Badge variant="outline" className="text-xs">
                          {invoice.status === 'pending' && '⏳ Venter'}
                          {invoice.status === 'approved' && '✅ Godkjent'}
                          {invoice.status === 'rejected' && '❌ Avvist'}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>

        {/* Helper Card */}
        <Card className="mt-6 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
          <h3 className="font-semibold text-blue-900 mb-3">
            💡 Prøv AI-assistenten
          </h3>
          <div className="space-y-2 text-sm text-blue-800">
            <p>Velg én eller flere fakturaer, deretter spør AI:</p>
            <ul className="ml-6 space-y-1 list-disc">
              <li>"Post valgte fakturaer mot konto 4000"</li>
              <li>"Hva er totalbeløpet for valgte fakturaer?"</li>
              <li>"Godkjenn alle valgte"</li>
              <li>"Vis detaljer om faktura INV-001"</li>
            </ul>
          </div>
        </Card>
      </div>
    </div>
  );
}

// Main page component with ChatProvider wrapper
export default function ReviewQueueWithChatPage() {
  return (
    <ChatProvider 
      initialModule="review-queue"
      clientId="demo-client"
      userId="demo-user"
    >
      <ReviewQueueContent />
      <ChatWindow />
    </ChatProvider>
  );
}
