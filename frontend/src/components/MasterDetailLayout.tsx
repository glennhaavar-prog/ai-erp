'use client';

import React, { useState } from 'react';

export interface MasterDetailLayoutProps<T> {
  items: T[];
  selectedId: string | null;
  selectedIds: string[];
  onSelectItem: (id: string) => void;
  onMultiSelect: (ids: string[]) => void;
  renderItem: (item: T, isSelected: boolean, isMultiSelected: boolean) => React.ReactNode;
  renderDetail: (item: T | null) => React.ReactNode;
  renderFooter?: () => React.ReactNode;
  loading?: boolean;
  multiSelectEnabled?: boolean;
}

/**
 * MasterDetailLayout - Gjenbrukbar layout komponent for master-detail views
 * 
 * Features:
 * - Venstre panel med liste (400px på desktop, full width på mobil)
 * - Høyre panel med detaljer (flex-1)
 * - Optional footer slot (60px, expandable on focus)
 * - Multiselect support med checkboxes
 * - Responsive: Stacker vertikalt på mobil (<768px)
 */
export function MasterDetailLayout<T extends { id: string }>({
  items,
  selectedId,
  selectedIds,
  onSelectItem,
  onMultiSelect,
  renderItem,
  renderDetail,
  renderFooter,
  loading = false,
  multiSelectEnabled = false,
}: MasterDetailLayoutProps<T>) {
  const [footerExpanded, setFooterExpanded] = useState(false);

  // Get currently selected item
  const selectedItem = items.find(item => item.id === selectedId) || null;

  // Handle checkbox toggle for multiselect
  const handleCheckboxToggle = (id: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent triggering item selection
    
    const newSelectedIds = selectedIds.includes(id)
      ? selectedIds.filter(selectedId => selectedId !== id)
      : [...selectedIds, id];
    
    onMultiSelect(newSelectedIds);
  };

  // Handle select all / deselect all
  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      onMultiSelect(items.map(item => item.id));
    } else {
      onMultiSelect([]);
    }
  };

  const allSelected = items.length > 0 && selectedIds.length === items.length;
  const someSelected = selectedIds.length > 0 && selectedIds.length < items.length;

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Main content area - Master + Detail */}
      <div className="flex flex-col md:flex-row flex-1 overflow-hidden">
        
        {/* LEFT PANEL - Master List */}
        <div className="w-full md:w-[400px] border-r border-gray-200 bg-white flex flex-col">
          
          {/* Header with select all checkbox (if multiselect enabled) */}
          {multiSelectEnabled && (
            <div className="px-4 py-3 border-b border-gray-200 bg-gray-50 flex items-center gap-3">
              <input
                type="checkbox"
                checked={allSelected}
                ref={input => {
                  if (input) input.indeterminate = someSelected;
                }}
                onChange={handleSelectAll}
                className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-600">
                {selectedIds.length > 0 ? `${selectedIds.length} selected` : 'Select all'}
              </span>
            </div>
          )}

          {/* Scrollable list */}
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : items.length === 0 ? (
              <div className="flex items-center justify-center h-32 text-gray-500">
                No items to display
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {items.map((item) => {
                  const isSelected = item.id === selectedId;
                  const isMultiSelected = selectedIds.includes(item.id);

                  return (
                    <div
                      key={item.id}
                      onClick={() => onSelectItem(item.id)}
                      className={`
                        relative cursor-pointer transition-colors
                        hover:bg-blue-50
                        ${isSelected ? 'bg-blue-100 border-l-4 border-blue-600' : 'border-l-4 border-transparent'}
                      `}
                    >
                      {/* Checkbox overlay for multiselect */}
                      {multiSelectEnabled && (
                        <div className="absolute left-3 top-1/2 -translate-y-1/2 z-10">
                          <input
                            type="checkbox"
                            checked={isMultiSelected}
                            onChange={() => {}}
                            onClick={(e) => handleCheckboxToggle(item.id, e)}
                            className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                        </div>
                      )}

                      {/* Item content */}
                      <div className={multiSelectEnabled ? 'pl-10' : ''}>
                        {renderItem(item, isSelected, isMultiSelected)}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT PANEL - Detail View */}
        <div className="flex-1 bg-white overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            renderDetail(selectedItem)
          )}
        </div>
      </div>

      {/* FOOTER - Optional Chat/Action Panel */}
      {renderFooter && (
        <div
          className={`
            border-t border-gray-200 bg-white transition-all duration-300 ease-in-out
            ${footerExpanded ? 'h-96' : 'h-[60px]'}
          `}
          onFocus={() => setFooterExpanded(true)}
          onBlur={(e) => {
            // Only collapse if focus leaves the footer entirely
            if (!e.currentTarget.contains(e.relatedTarget as Node)) {
              setFooterExpanded(false);
            }
          }}
        >
          <div className="h-full overflow-y-auto">
            {renderFooter()}
          </div>
        </div>
      )}
    </div>
  );
}

export default MasterDetailLayout;
