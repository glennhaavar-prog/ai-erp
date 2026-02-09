'use client';

import React from 'react';
import { useViewMode, TaskFilter } from '@/contexts/ViewModeContext';
import { FileText, Banknote, CheckSquare } from 'lucide-react';

export function TaskTypeFilter() {
  const { taskFilter, setTaskFilter } = useViewMode();

  const handleFilter = (filter: TaskFilter) => {
    setTaskFilter(filter);
  };

  return (
    <div className="flex gap-1 p-1 bg-muted rounded-lg">
      <button
        onClick={() => handleFilter('all')}
        className={`
          flex items-center gap-2 px-3 py-2 rounded-md transition-all text-sm font-medium
          ${
            taskFilter === 'all'
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:bg-background/50'
          }
        `}
      >
        Alle
      </button>
      <button
        onClick={() => handleFilter('bilag')}
        className={`
          flex items-center gap-2 px-3 py-2 rounded-md transition-all text-sm font-medium
          ${
            taskFilter === 'bilag'
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:bg-background/50'
          }
        `}
      >
        <FileText className="w-4 h-4" />
        Bilag
      </button>
      <button
        onClick={() => handleFilter('bank')}
        className={`
          flex items-center gap-2 px-3 py-2 rounded-md transition-all text-sm font-medium
          ${
            taskFilter === 'bank'
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:bg-background/50'
          }
        `}
      >
        <Banknote className="w-4 h-4" />
        Bank
      </button>
      <button
        onClick={() => handleFilter('avstemming')}
        className={`
          flex items-center gap-2 px-3 py-2 rounded-md transition-all text-sm font-medium
          ${
            taskFilter === 'avstemming'
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:bg-background/50'
          }
        `}
      >
        <CheckSquare className="w-4 h-4" />
        Avstemming
      </button>
    </div>
  );
}
