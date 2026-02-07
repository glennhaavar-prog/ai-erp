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
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Load clients from API
    const loadClients = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/clients/');
        const data = await response.json();
        
        if (data && data.length > 0) {
          setClients(data);
          // Auto-select first client
          setSelectedClient(data[0]);
        }
      } catch (error) {
        console.error('Failed to load clients:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadClients();
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
