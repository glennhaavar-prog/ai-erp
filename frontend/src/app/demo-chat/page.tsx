'use client';

import React, { useState } from 'react';
import { ChatProvider } from '@/contexts/ChatContext';
import ChatWindow from '@/components/ChatWindow';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export default function ChatDemo() {
  const [module, setModule] = useState<string>('review-queue');
  const [selectedItems, setSelectedItems] = useState<string[]>(['invoice-123']);

  const modules = [
    { id: 'review-queue', label: 'Gjennomgangskø', color: 'bg-blue-500' },
    { id: 'bank-recon', label: 'Bankavstemming', color: 'bg-green-500' },
    { id: 'general', label: 'Generell', color: 'bg-purple-500' },
  ];

  const mockInvoices = [
    { id: 'invoice-123', vendor: 'Staples AS', amount: 4500 },
    { id: 'invoice-456', vendor: 'Office Depot', amount: 2300 },
    { id: 'invoice-789', vendor: 'Amazon Business', amount: 8900 },
  ];

  const toggleItem = (itemId: string) => {
    setSelectedItems(prev => 
      prev.includes(itemId) 
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  return (
    <ChatProvider initialModule={module} clientId="demo-client" userId="demo-user">
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Kontali AI Chat Demo
            </h1>
            <p className="text-gray-600">
              Test den kontekstsensitive chatvindu-komponenten
            </p>
          </div>

          {/* Module Selector */}
          <Card className="p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Velg modul</h2>
            <div className="flex gap-3">
              {modules.map((mod) => (
                <Button
                  key={mod.id}
                  onClick={() => setModule(mod.id)}
                  variant={module === mod.id ? 'default' : 'outline'}
                  className={module === mod.id ? mod.color : ''}
                >
                  {mod.label}
                </Button>
              ))}
            </div>
          </Card>

          {/* Mock Data Selection */}
          <Card className="p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">
              Valgte items (simulerer valgte fakturaer)
            </h2>
            <div className="space-y-3">
              {mockInvoices.map((invoice) => (
                <div
                  key={invoice.id}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    selectedItems.includes(invoice.id)
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                  onClick={() => toggleItem(invoice.id)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{invoice.vendor}</p>
                      <p className="text-sm text-gray-500">{invoice.id}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-gray-900">
                        {invoice.amount.toLocaleString('no-NO')} kr
                      </p>
                      {selectedItems.includes(invoice.id) && (
                        <Badge className="mt-1 bg-blue-500">Valgt</Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Context Info */}
          <Card className="p-6 mb-6 bg-gradient-to-r from-indigo-50 to-blue-50 border-indigo-200">
            <h2 className="text-lg font-semibold mb-4 text-indigo-900">
              Nåværende kontekst
            </h2>
            <div className="space-y-2 font-mono text-sm">
              <div className="flex gap-2">
                <span className="text-gray-600">Modul:</span>
                <span className="font-semibold text-indigo-900">{module}</span>
              </div>
              <div className="flex gap-2">
                <span className="text-gray-600">Valgte items:</span>
                <span className="font-semibold text-indigo-900">
                  {selectedItems.length > 0 ? selectedItems.join(', ') : 'Ingen valgt'}
                </span>
              </div>
            </div>
          </Card>

          {/* Instructions */}
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4">💡 Test dette</h2>
            <div className="space-y-2 text-sm text-gray-700">
              <p>1. <strong>Velg en modul</strong> (Review Queue, Bank Recon, etc.)</p>
              <p>2. <strong>Velg noen items</strong> fra listen over</p>
              <p>3. <strong>Klikk på chat-ikonet</strong> nederst til høyre</p>
              <p>4. <strong>Skriv meldinger</strong> som:</p>
              <ul className="ml-6 mt-2 space-y-1 list-disc">
                <li>"Post denne mot konto 4000"</li>
                <li>"Vis meg valgte fakturaer"</li>
                <li>"Hva er konteksten min?"</li>
                <li>"Godkjenn alle valgte"</li>
              </ul>
              <p className="mt-4 text-xs text-gray-500">
                💡 <strong>Tips:</strong> Chatvinduen sender automatisk modul og selectedItems 
                til backend i hver melding.
              </p>
            </div>
          </Card>
        </div>

        {/* Chat Window */}
        <ChatWindow />
      </div>
    </ChatProvider>
  );
}
