'use client';

import { useState } from 'react';
import { useClient } from '@/contexts/ClientContext';

export const Topbar = () => {
  const { selectedClient, setSelectedClient, clients, isLoading } = useClient();
  const [isClientSwitcherOpen, setIsClientSwitcherOpen] = useState(false);
  const [notifications, setNotifications] = useState(3); // Mock notification count

  return (
    <header className="h-14 bg-bg-dark border-b border-border flex items-center px-6 gap-4 shrink-0">
      {/* Client Switcher */}
      <div className="relative">
        <button
          onClick={() => setIsClientSwitcherOpen(!isClientSwitcherOpen)}
          className="flex items-center gap-2 px-3 py-1.5 bg-bg-card border border-border-light rounded-md cursor-pointer transition-all duration-150 hover:border-accent-blue hover:bg-bg-hover"
        >
          <span className="w-2 h-2 rounded-full bg-accent-green"></span>
          {selectedClient ? (
            <>
              <span className="text-[13px] font-semibold text-text-primary">
                {selectedClient.name}
              </span>
              <span className="text-[11px] text-text-muted ml-1">
                {selectedClient.org_number}
              </span>
            </>
          ) : (
            <span className="text-[13px] font-semibold text-text-secondary">
              Velg klient...
            </span>
          )}
          <span className="text-[10px] text-text-muted ml-1">▾</span>
        </button>

        {/* Client Dropdown */}
        {isClientSwitcherOpen && (
          <div className="absolute top-full left-0 mt-1 w-80 bg-bg-card border border-border rounded-lg shadow-xl z-50 max-h-96 overflow-y-auto">
            <div className="p-2">
              <input
                type="text"
                placeholder="Søk etter klient..."
                className="w-full px-3 py-2 bg-bg-dark border border-border rounded-md text-[13px] text-text-primary placeholder:text-text-muted outline-none focus:border-accent-blue"
              />
            </div>
            <div className="border-t border-border">
              {clients.map(client => (
                <button
                  key={client.id}
                  onClick={() => {
                    setSelectedClient(client);
                    setIsClientSwitcherOpen(false);
                  }}
                  className="w-full px-4 py-2.5 flex items-center gap-2 hover:bg-bg-hover transition-colors text-left"
                >
                  <span className="w-2 h-2 rounded-full bg-accent-green"></span>
                  <div className="flex-1">
                    <div className="text-[13px] font-medium text-text-primary">
                      {client.name}
                    </div>
                    <div className="text-[11px] text-text-muted">
                      Org.nr: {client.org_number}
                    </div>
                  </div>
                  {selectedClient?.id === client.id && (
                    <span className="text-accent-blue text-sm">✓</span>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Search */}
      <div className="flex-1 max-w-md relative">
        <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted text-[14px]">
          🔍
        </span>
        <input
          type="text"
          placeholder="Søk bilag, fakturaer, kunder..."
          className="w-full pl-9 pr-14 py-1.5 bg-bg-card border border-border rounded-md text-[13px] text-text-primary placeholder:text-text-muted outline-none transition-colors focus:border-accent-blue"
        />
        <span className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[10px] text-text-muted bg-bg-hover px-1.5 py-0.5 rounded font-mono">
          ⌘K
        </span>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-1.5 ml-auto">
        {/* Notifications */}
        <button
          className="w-9 h-9 flex items-center justify-center rounded-md text-text-secondary hover:bg-bg-hover hover:text-text-primary transition-all relative"
          title="Varsler"
        >
          <span className="text-[16px]">🔔</span>
          {notifications > 0 && (
            <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-accent-red rounded-full border-2 border-bg-dark"></span>
          )}
        </button>

        {/* AI Assistant */}
        <button
          className="w-9 h-9 flex items-center justify-center rounded-md text-text-secondary hover:bg-bg-hover hover:text-text-primary transition-all"
          title="AI-assistent"
        >
          <span className="text-[16px]">💬</span>
        </button>

        {/* User Avatar */}
        <div
          className="w-8 h-8 rounded-full bg-gradient-to-br from-accent-blue to-accent-purple flex items-center justify-center text-white font-bold text-[12px] cursor-pointer ml-1.5"
          title="Glenn Håvar Brottveit"
        >
          GB
        </div>
      </div>
    </header>
  );
};
