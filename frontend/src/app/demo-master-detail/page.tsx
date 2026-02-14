'use client';

import React, { useState } from 'react';
import { MasterDetailLayout } from '@/components/MasterDetailLayout';

// Demo data types
interface DemoItem {
  id: string;
  title: string;
  description: string;
  status: 'active' | 'pending' | 'completed';
  timestamp: string;
  priority: 'high' | 'medium' | 'low';
}

// Generate dummy data
const generateDummyData = (): DemoItem[] => {
  const statuses: Array<'active' | 'pending' | 'completed'> = ['active', 'pending', 'completed'];
  const priorities: Array<'high' | 'medium' | 'low'> = ['high', 'medium', 'low'];
  const titles = [
    'Kundefaktura #1024',
    'Leverandørfaktura #2051',
    'Lønnskjøring Januar',
    'Revisjonsrapport Q4',
    'Skattemelding 2024',
    'Årsavslutning',
    'Budsjettforslag 2025',
    'Månedsrapport Februar',
    'Kontoutskrift DNB',
    'Bilagsføring uke 7',
    'Purring kunde #445',
    'Godkjenning reiseregning',
  ];

  return titles.map((title, index) => ({
    id: `item-${index + 1}`,
    title,
    description: `Dette er en detaljert beskrivelse for ${title}. Her kan det stå mer informasjon om denne transaksjonen eller oppgaven.`,
    status: statuses[index % statuses.length],
    timestamp: new Date(Date.now() - Math.random() * 10000000000).toISOString(),
    priority: priorities[index % priorities.length],
  }));
};

export default function DemoMasterDetailPage() {
  const [items] = useState<DemoItem[]>(generateDummyData());
  const [selectedId, setSelectedId] = useState<string | null>(items[0]?.id || null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [multiSelectEnabled, setMultiSelectEnabled] = useState(false);
  const [chatMessage, setChatMessage] = useState('');

  // Render individual item in list
  const renderItem = (item: DemoItem, isSelected: boolean, isMultiSelected: boolean) => {
    const statusColors = {
      active: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-gray-100 text-gray-800',
    };

    const priorityColors = {
      high: 'text-red-600',
      medium: 'text-orange-600',
      low: 'text-gray-600',
    };

    return (
      <div className="p-4 hover:bg-blue-50 transition-colors">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <h3 className={`font-medium truncate ${isSelected ? 'text-blue-900' : 'text-gray-900'}`}>
              {item.title}
            </h3>
            <p className="text-sm text-gray-600 truncate mt-1">
              {item.description}
            </p>
            <div className="flex items-center gap-2 mt-2">
              <span className={`text-xs px-2 py-1 rounded-full ${statusColors[item.status]}`}>
                {item.status}
              </span>
              <span className={`text-xs font-medium ${priorityColors[item.priority]}`}>
                {item.priority}
              </span>
            </div>
          </div>
          <div className="text-xs text-gray-500 whitespace-nowrap">
            {new Date(item.timestamp).toLocaleDateString('no-NO')}
          </div>
        </div>
      </div>
    );
  };

  // Render detail view
  const renderDetail = (item: DemoItem | null) => {
    if (!item) {
      return (
        <div className="flex items-center justify-center h-full text-gray-500">
          <div className="text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No item selected</h3>
            <p className="mt-1 text-sm text-gray-500">Select an item from the list to view details</p>
          </div>
        </div>
      );
    }

    const statusColors = {
      active: 'bg-green-100 text-green-800 border-green-200',
      pending: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      completed: 'bg-gray-100 text-gray-800 border-gray-200',
    };

    return (
      <div className="p-8 max-w-4xl">
        <div className="space-y-6">
          {/* Header */}
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{item.title}</h1>
            <p className="text-gray-600 mt-2">{item.description}</p>
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <div className="text-sm text-gray-600">Status</div>
              <div className={`mt-2 inline-block px-3 py-1 rounded-full text-sm font-medium border ${statusColors[item.status]}`}>
                {item.status}
              </div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <div className="text-sm text-gray-600">Priority</div>
              <div className="mt-2 text-lg font-semibold capitalize">{item.priority}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <div className="text-sm text-gray-600">Date</div>
              <div className="mt-2 text-lg font-semibold">
                {new Date(item.timestamp).toLocaleDateString('no-NO', {
                  day: 'numeric',
                  month: 'long',
                  year: 'numeric',
                })}
              </div>
            </div>
          </div>

          {/* Content sections */}
          <div className="border-t pt-6">
            <h2 className="text-xl font-semibold mb-4">Details</h2>
            <div className="prose max-w-none">
              <p className="text-gray-700">
                Her kan du vise detaljert informasjon om den valgte oppgaven eller transaksjonen.
                Dette kan inkludere bilagsbilder, kommentarer, historikk, og andre relevante data.
              </p>
              <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="text-sm font-medium text-blue-900">Demo informasjon</h3>
                <ul className="mt-2 text-sm text-blue-800 space-y-1">
                  <li>• ID: {item.id}</li>
                  <li>• Timestamp: {item.timestamp}</li>
                  <li>• Status: {item.status}</li>
                  <li>• Priority: {item.priority}</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex gap-3 pt-4 border-t">
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              Approve
            </button>
            <button className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors">
              Edit
            </button>
            <button className="px-4 py-2 bg-red-100 text-red-800 rounded-lg hover:bg-red-200 transition-colors">
              Reject
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Render footer (chat interface)
  const renderFooter = () => {
    return (
      <div className="h-full flex flex-col">
        <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
          <h3 className="font-medium text-gray-900">💬 Chat / Notater</h3>
          <span className="text-xs text-gray-500">Klikk i feltet for å utvide</span>
        </div>
        <div className="flex-1 p-4 overflow-y-auto">
          <div className="text-sm text-gray-600 mb-4">
            Her kan du chatte med AI-assistenten eller legge til notater...
          </div>
        </div>
        <div className="p-4 border-t border-gray-200">
          <div className="flex gap-2">
            <input
              type="text"
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
              placeholder="Skriv en melding..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={() => {
                console.log('Send message:', chatMessage);
                setChatMessage('');
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Demo header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">MasterDetailLayout Demo</h1>
            <p className="text-sm text-gray-600 mt-1">
              Gjenbrukbar komponent for Kontali redesign
            </p>
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={multiSelectEnabled}
                onChange={(e) => {
                  setMultiSelectEnabled(e.target.checked);
                  if (!e.target.checked) {
                    setSelectedIds([]);
                  }
                }}
                className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Enable Multiselect</span>
            </label>
            {selectedIds.length > 0 && (
              <div className="text-sm bg-blue-100 text-blue-800 px-3 py-1 rounded-full">
                {selectedIds.length} selected
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Layout component */}
      <div className="flex-1 overflow-hidden">
        <MasterDetailLayout
          items={items}
          selectedId={selectedId}
          selectedIds={selectedIds}
          onSelectItem={setSelectedId}
          onMultiSelect={setSelectedIds}
          renderItem={renderItem}
          renderDetail={renderDetail}
          renderFooter={renderFooter}
          multiSelectEnabled={multiSelectEnabled}
          loading={false}
        />
      </div>
    </div>
  );
}
