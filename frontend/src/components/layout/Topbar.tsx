'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search, ChevronDown, LayoutGrid, Building2 } from 'lucide-react';
import { useViewMode } from '@/contexts/ViewModeContext';
import { useClient } from '@/contexts/ClientContext';

export default function Topbar() {
  const router = useRouter();
  const { viewMode, toggleViewMode } = useViewMode();
  const { selectedClient, setSelectedClient, clients, isLoading: loading } = useClient();
  const [clientDropdownOpen, setClientDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Filter clients based on search query
  const filteredClients = clients.filter(client =>
    client.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    client.org_number.includes(searchQuery)
  );

  return (
    <header className="h-16 border-b border-border bg-card flex items-center justify-between px-6">
      {/* Left: Client selector and ViewMode Toggle */}
      <div className="flex items-center gap-4">
        {/* Client Dropdown - only shown in client view mode */}
        {viewMode === 'client' && (
          <div className="relative">
            <button
              onClick={() => setClientDropdownOpen(!clientDropdownOpen)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border bg-background hover:bg-muted/50 transition-colors cursor-pointer"
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="w-8 h-8 rounded-full bg-muted animate-pulse"></div>
                  <div className="text-sm text-muted-foreground">Laster klienter...</div>
                </>
              ) : selectedClient ? (
                <>
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-medium text-sm">
                    {selectedClient.name.substring(0, 2).toUpperCase()}
                  </div>
                  <div className="text-left flex items-center gap-2">
                    <div className="text-sm font-medium text-foreground">{selectedClient.name}</div>
                    <div className="w-2 h-2 rounded-full bg-success animate-pulse" title="Aktiv klient"></div>
                  </div>
                  <ChevronDown className="w-4 h-4 text-muted-foreground" />
                </>
              ) : (
                <div className="text-sm text-muted-foreground">Ingen klienter</div>
              )}
            </button>

            {/* Backdrop overlay */}
            {clientDropdownOpen && (
              <div 
                className="fixed inset-0 bg-black/50 z-40"
                onClick={() => setClientDropdownOpen(false)}
              />
            )}

            {/* Dropdown */}
            {clientDropdownOpen && !loading && (
              <div className="absolute top-full left-0 mt-2 w-96 bg-gray-900 border border-gray-700 rounded-lg shadow-2xl z-50">
                <div className="p-3 border-b border-gray-700 bg-gray-800">
                  <div className="text-sm font-semibold text-gray-300 uppercase tracking-wider px-2 mb-2">
                    Bytt klient ({clients.length})
                  </div>
                  {/* Search input */}
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Søk etter navn eller org.nr..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 rounded-md bg-gray-700 border border-gray-600 text-white placeholder:text-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>
                </div>
                <div className="max-h-96 overflow-y-auto p-2">
                  {filteredClients.length === 0 ? (
                    <div className="px-4 py-8 text-center text-gray-400 text-sm">
                      Ingen klienter funnet
                    </div>
                  ) : (
                    filteredClients.map(client => (
                      <button
                        key={client.id}
                        onClick={() => {
                          setSelectedClient(client);
                          setClientDropdownOpen(false);
                          setSearchQuery('');
                          // Navigate to client-specific dashboard
                          router.push(`/clients/${client.id}`);
                        }}
                        className={`
                          w-full flex items-center gap-3 px-4 py-3 rounded-lg text-base transition-colors cursor-pointer
                          ${selectedClient?.id === client.id 
                            ? 'bg-primary text-white font-semibold' 
                            : 'hover:bg-gray-800 text-white'}
                        `}
                      >
                        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-semibold text-sm border-2 border-primary/30">
                          {client.name.substring(0, 2).toUpperCase()}
                        </div>
                        <div className="flex-1 text-left">
                          <div>{client.name}</div>
                          <div className="text-xs text-gray-400">{client.org_number}</div>
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ViewMode Toggle - Icons only, no text */}
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border bg-background">
          <button
            onClick={toggleViewMode}
            className={`p-2 rounded transition-colors cursor-pointer ${
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
            className={`p-2 rounded transition-colors cursor-pointer ${
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

      {/* Center: Global search (Task 7: HIGH CONTRAST for peripheral vision) */}
      <div className="flex-1 max-w-md mx-8">
        <div className="relative" title="Global søk (kommer snart)">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-primary" />
          <input
            type="text"
            placeholder="Søk etter bilag, faktura, klient..."
            disabled
            className="w-full pl-11 pr-4 py-2.5 rounded-lg border-2 border-primary/30 bg-card text-foreground placeholder:text-foreground/60 text-sm font-medium shadow-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all disabled:cursor-not-allowed disabled:opacity-60"
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
