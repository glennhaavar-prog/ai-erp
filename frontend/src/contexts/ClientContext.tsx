'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface Client {
  id: string;
  name: string;
  org_number: string;
  is_demo?: boolean;
}

interface ClientContextType {
  selectedClient: Client | null;
  setSelectedClient: (client: Client | null) => void;
  clients: Client[];
  isLoading: boolean;
}

const ClientContext = createContext<ClientContextType | undefined>(undefined);

export const ClientProvider = ({ children }: { children: ReactNode }) => {
  const [selectedClient, setSelectedClientState] = useState<Client | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Wrapper to save to localStorage
  // Note: ViewMode syncing removed to prevent circular dependency issues
  const setSelectedClient = (client: Client | null) => {
    setSelectedClientState(client);
    if (client) {
      localStorage.setItem('selected_client_id', client.id);
    } else {
      localStorage.removeItem('selected_client_id');
    }
  };

  useEffect(() => {
    // Load clients from API
    const loadClients = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/clients/');
        const data = await response.json();
        
        if (data && data.items && data.items.length > 0) {
          setClients(data.items);
          
          // Try to restore selected client from localStorage
          const savedClientId = localStorage.getItem('selected_client_id');
          if (savedClientId) {
            const savedClient = data.items.find((c: Client) => c.id === savedClientId);
            if (savedClient) {
              setSelectedClient(savedClient); // This will also set viewMode to 'client'
              return;
            }
          }
          
          // Auto-select first client if no saved selection
          setSelectedClient(data.items[0]); // This will also set viewMode to 'client'
        }
      } catch (error) {
        console.error('Failed to load clients:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadClients();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <ClientContext.Provider value={{ selectedClient, setSelectedClient, clients, isLoading }}>
      {children}
    </ClientContext.Provider>
  );
};

export const useClient = () => {
  const context = useContext(ClientContext);
  if (context === undefined) {
    throw new Error('useClient must be used within a ClientProvider');
  }
  return context;
};
