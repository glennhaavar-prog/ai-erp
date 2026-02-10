'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface TenantContextType {
  tenantId: string | null;
  tenantName: string | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

interface TenantProviderProps {
  children: ReactNode;
}

export function TenantProvider({ children }: TenantProviderProps) {
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [tenantName, setTenantName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTenant = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Add timeout to prevent infinite loading
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout
      
      const response = await fetch('http://localhost:8000/api/tenants/demo', {
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch tenant: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('TenantContext: Fetched tenant:', data);
      setTenantId(data.id);
      setTenantName(data.name);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
      console.error('TenantContext: Failed to fetch tenant:', err);
    } finally {
      setIsLoading(false);
      console.log('TenantContext: Loading complete');
    }
  };

  useEffect(() => {
    fetchTenant();
  }, []);

  const value: TenantContextType = {
    tenantId,
    tenantName,
    isLoading,
    error,
    refetch: fetchTenant,
  };

  return (
    <TenantContext.Provider value={value}>
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant(): TenantContextType {
  const context = useContext(TenantContext);
  
  if (context === undefined) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  
  return context;
}
