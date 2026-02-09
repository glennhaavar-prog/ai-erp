'use client';

import React from 'react';
import { useViewMode } from '@/contexts/ViewModeContext';

export default function ViewModeToggle() {
  const { viewMode, toggleViewMode } = useViewMode();

  return (
    <div className="flex items-center gap-2 bg-card border border-border rounded-lg p-1">
      <button
        onClick={() => viewMode !== 'multi-client' && toggleViewMode()}
        className={`
          px-3 py-1.5 rounded-md text-sm font-medium transition-all duration-200
          ${viewMode === 'multi-client' 
            ? 'bg-primary text-primary-foreground' 
            : 'text-muted-foreground hover:text-foreground'
          }
        `}
      >
        Multi-klient
      </button>
      
      <button
        onClick={() => viewMode !== 'client' && toggleViewMode()}
        className={`
          px-3 py-1.5 rounded-md text-sm font-medium transition-all duration-200
          ${viewMode === 'client' 
            ? 'bg-primary text-primary-foreground' 
            : 'text-muted-foreground hover:text-foreground'
          }
        `}
      >
        Klient
      </button>
    </div>
  );
}
