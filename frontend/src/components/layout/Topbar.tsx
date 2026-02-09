'use client';

import React, { useState } from 'react';
import { Search, ChevronDown, LayoutGrid, Building2 } from 'lucide-react';
import { useViewMode } from '@/contexts/ViewModeContext';

// Mock clients - will be replaced with real data from context/API
const MOCK_CLIENTS = [
  { id: '1', name: 'Fjordvik Fiskeoppdrett AS' },
  { id: '2', name: 'Nordic Tech Solutions AS' },
  { id: '3', name: 'Bergen Byggeservice AS' },
];

export default function Topbar() {
  const { viewMode, toggleViewMode } = useViewMode();
  const [selectedClient, setSelectedClient] = useState(MOCK_CLIENTS[0]);
  const [clientDropdownOpen, setClientDropdownOpen] = useState(false);

  return (
    <header className="h-16 border-b border-border bg-card flex items-center justify-between px-6">
      {/* Left: Client selector and ViewMode Toggle */}
      <div className="flex items-center gap-4">
        {/* Client Dropdown - only shown in client view mode */}
        {viewMode === 'client' && (
          <div className="relative">
            <button
              onClick={() => setClientDropdownOpen(!clientDropdownOpen)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border bg-background hover:bg-muted/50 transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-medium text-sm">
                {selectedClient.name.substring(0, 2).toUpperCase()}
              </div>
              <div className="text-left">
                <div className="text-sm font-medium text-foreground">{selectedClient.name}</div>
                <div className="text-xs text-muted-foreground">Aktiv klient</div>
              </div>
              <ChevronDown className="w-4 h-4 text-muted-foreground" />
            </button>

            {/* Dropdown */}
            {clientDropdownOpen && (
              <div className="absolute top-full left-0 mt-2 w-72 bg-card border border-border rounded-lg shadow-lg z-50">
                <div className="p-2 border-b border-border">
                  <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-2 py-1">
                    Bytt klient
                  </div>
                </div>
                <div className="max-h-64 overflow-y-auto p-2">
                  {MOCK_CLIENTS.map(client => (
                    <button
                      key={client.id}
                      onClick={() => {
                        setSelectedClient(client);
                        setClientDropdownOpen(false);
                      }}
                      className={`
                        w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors
                        ${selectedClient.id === client.id 
                          ? 'bg-primary/10 text-primary' 
                          : 'hover:bg-muted/50 text-foreground'}
                      `}
                    >
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-medium text-xs">
                        {client.name.substring(0, 2).toUpperCase()}
                      </div>
                      <span className="flex-1 text-left">{client.name}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ViewMode Toggle - Icons only, no text */}
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border bg-background">
          <button
            onClick={toggleViewMode}
            className={`p-2 rounded transition-colors ${
              viewMode === 'multi-client' 
                ? 'bg-primary text-primary-foreground' 
                : 'text-muted-foreground hover:text-foreground'
            }`}
            title="Multi-klient visning"
          >
            <LayoutGrid className="w-5 h-5" />
          </button>
          <button
            onClick={toggleViewMode}
            className={`p-2 rounded transition-colors ${
              viewMode === 'client' 
                ? 'bg-primary text-primary-foreground' 
                : 'text-muted-foreground hover:text-foreground'
            }`}
            title="Enkeltklient visning"
          >
            <Building2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Center: Global search (disabled for now) */}
      <div className="flex-1 max-w-md mx-8">
        <div className="relative opacity-35 cursor-not-allowed" title="Kommer snart">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Søk i Kontali..."
            disabled
            className="w-full pl-10 pr-4 py-2 rounded-lg border border-border bg-background text-sm"
          />
        </div>
      </div>

      {/* Right: User (disabled for now) */}
      <div className="flex items-center gap-3">
        {/* User menu (grayed out - no function yet) */}
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg opacity-40 cursor-not-allowed" title="Brukerinnstillinger kommer snart">
          <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-muted-foreground font-medium text-sm">
            G
          </div>
          <span className="text-sm font-medium text-muted-foreground">Glenn</span>
        </div>
      </div>
    </header>
  );
}
