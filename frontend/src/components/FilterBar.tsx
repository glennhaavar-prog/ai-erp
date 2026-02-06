import React from 'react';
import clsx from 'clsx';
import { ReviewStatus, Priority } from '@/types/review-queue';

interface FilterBarProps {
  selectedStatus?: ReviewStatus;
  selectedPriority?: Priority;
  onStatusChange: (status?: ReviewStatus) => void;
  onPriorityChange: (priority?: Priority) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  selectedStatus,
  selectedPriority,
  onStatusChange,
  onPriorityChange,
  searchQuery,
  onSearchChange,
}) => {
  const statuses: (ReviewStatus | 'all')[] = ['all', 'pending', 'approved', 'corrected', 'rejected'];
  const priorities: (Priority | 'all')[] = ['all', 'high', 'medium', 'low'];

  const FilterButton = ({ active, onClick, children }: any) => (
    <button
      onClick={onClick}
      className={clsx(
        'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
        active
          ? 'bg-accent-blue text-white'
          : 'bg-dark-card text-gray-300 hover:bg-dark-hover'
      )}
    >
      {children}
    </button>
  );

  return (
    <div className="bg-dark-card border border-dark-border rounded-lg p-4 space-y-4">
      {/* Search */}
      <input
        type="text"
        value={searchQuery}
        onChange={(e) => onSearchChange(e.target.value)}
        placeholder="Søk etter leverandør, fakturanummer..."
        className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent-blue"
      />

      {/* Status Filter */}
      <div>
        <label className="text-xs text-gray-400 uppercase tracking-wide mb-2 block">
          Status
        </label>
        <div className="flex flex-wrap gap-2">
          {statuses.map((status) => (
            <FilterButton
              key={status}
              active={status === 'all' ? !selectedStatus : selectedStatus === status}
              onClick={() => onStatusChange(status === 'all' ? undefined : status as ReviewStatus)}
            >
              {status === 'all' ? 'Alle' : status.charAt(0).toUpperCase() + status.slice(1)}
            </FilterButton>
          ))}
        </div>
      </div>

      {/* Priority Filter */}
      <div>
        <label className="text-xs text-gray-400 uppercase tracking-wide mb-2 block">
          Prioritet
        </label>
        <div className="flex flex-wrap gap-2">
          {priorities.map((priority) => (
            <FilterButton
              key={priority}
              active={priority === 'all' ? !selectedPriority : selectedPriority === priority}
              onClick={() => onPriorityChange(priority === 'all' ? undefined : priority as Priority)}
            >
              {priority === 'all' ? 'Alle' : priority.charAt(0).toUpperCase() + priority.slice(1)}
            </FilterButton>
          ))}
        </div>
      </div>
    </div>
  );
};
