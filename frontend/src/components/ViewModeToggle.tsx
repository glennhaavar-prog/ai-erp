'use client';

import React from 'react';
import { useViewMode, ViewMode } from '@/contexts/ViewModeContext';
import { Globe, User } from 'lucide-react';

export function ViewModeToggle() {
  const { viewMode, setViewMode } = useViewMode();

  const handleToggle = (mode: ViewMode) => {
    setViewMode(mode);
  };

  return (
    <div className="flex gap-1 p-1 bg-muted rounded-lg">
      <button
        onClick={() => handleToggle('multi-client')}
        className={`
          flex items-center gap-2 px-4 py-2 rounded-md transition-all text-sm font-medium
          ${
            viewMode === 'multi-client'
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:bg-background/50'
          }
        `}
      >
        <Globe className="w-4 h-4" />
        Multi-Client
      </button>
      <button
        onClick={() => handleToggle('client')}
        className={`
          flex items-center gap-2 px-4 py-2 rounded-md transition-all text-sm font-medium
          ${
            viewMode === 'client'
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:bg-background/50'
          }
        `}
      >
        <User className="w-4 h-4" />
        Single Client
      </button>
    </div>
  );
}
