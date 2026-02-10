'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';

export type ViewMode = 'multi-client' | 'client';
export type TaskFilter = 'all' | 'bilag' | 'bank' | 'avstemming';

interface ViewModeContextType {
  viewMode: ViewMode;
  setViewMode: (mode: ViewMode) => void;
  toggleViewMode: () => void;
  taskFilter: TaskFilter;
  setTaskFilter: (filter: TaskFilter) => void;
  selectedClientId: string | null;
  setSelectedClientId: (id: string | null) => void;
  selectedItem: any | null;
  setSelectedItem: (item: any | null) => void;
}

const ViewModeContext = createContext<ViewModeContextType | undefined>(undefined);

export function ViewModeProvider({ children }: { children: ReactNode }) {
  const [viewMode, setViewMode] = useState<ViewMode>('multi-client');
  const [taskFilter, setTaskFilter] = useState<TaskFilter>('all');
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<any | null>(null);

  const toggleViewMode = () => {
    setViewMode(prev => prev === 'multi-client' ? 'client' : 'multi-client');
  };

  return (
    <ViewModeContext.Provider
      value={{
        viewMode,
        setViewMode,
        toggleViewMode,
        taskFilter,
        setTaskFilter,
        selectedClientId,
        setSelectedClientId,
        selectedItem,
        setSelectedItem,
      }}
    >
      {children}
    </ViewModeContext.Provider>
  );
}

export function useViewMode() {
  const context = useContext(ViewModeContext);
  if (context === undefined) {
    throw new Error('useViewMode must be used within a ViewModeProvider');
  }
  return context;
}
