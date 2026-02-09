'use client';

import React from 'react';
import { FixedChatPanel } from './FixedChatPanel';
import { Building2, FileText, Calendar, AlertCircle } from 'lucide-react';

interface Client {
  client_id: string;
  client_name: string;
  status: 'green' | 'yellow' | 'red';
  counts: {
    bilag: number;
    bank: number;
    avstemming: number;
  };
  urgent_items: number;
  review_items: number;
}

interface Task {
  id: string;
  client_id: string;
  client_name: string;
  category: string;
  title: string;
  description: string;
  priority: string;
  confidence: number;
}

interface RightPanelProps {
  selectedItem: Client | Task | null;
  type: 'client' | 'task';
}

function ClientDetails({ client }: { client: Client }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Building2 className="w-8 h-8 text-muted-foreground" />
        <div>
          <h3 className="text-lg font-semibold text-foreground">{client.client_name}</h3>
          <p className="text-sm text-muted-foreground">Klient ID: {client.client_id}</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 pt-4 border-t">
        <div className="text-center">
          <div className="text-2xl font-bold text-foreground">{client.counts.bilag}</div>
          <div className="text-xs text-muted-foreground">Bilag</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-foreground">{client.counts.bank}</div>
          <div className="text-xs text-muted-foreground">Bank</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-foreground">{client.counts.avstemming}</div>
          <div className="text-xs text-muted-foreground">Avstemming</div>
        </div>
      </div>

      {client.status === 'red' && client.urgent_items > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
          <div>
            <div className="text-sm font-medium text-red-900">{client.urgent_items} oppgaver haster</div>
            <div className="text-xs text-red-700">Trenger umiddelbar oppmerksomhet</div>
          </div>
        </div>
      )}

      {client.status === 'yellow' && client.review_items > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0" />
          <div>
            <div className="text-sm font-medium text-yellow-900">{client.review_items} til gjennomgang</div>
            <div className="text-xs text-yellow-700">Bør sees på snart</div>
          </div>
        </div>
      )}

      {client.status === 'green' && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-center gap-2">
          <div className="text-4xl">✅</div>
          <div>
            <div className="text-sm font-medium text-green-900">Alt OK</div>
            <div className="text-xs text-green-700">Ingen oppgaver krever oppmerksomhet</div>
          </div>
        </div>
      )}

      <div className="pt-4 border-t">
        <div className="text-xs text-muted-foreground mb-2">SISTE AKTIVITET</div>
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm">
            <Calendar className="w-4 h-4 text-muted-foreground" />
            <span className="text-muted-foreground">I dag, 14:32</span>
          </div>
          <div className="text-sm text-foreground">Automatisk bokføring av leverandørfaktura</div>
        </div>
      </div>
    </div>
  );
}

function TaskDetails({ task }: { task: Task }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <FileText className="w-8 h-8 text-muted-foreground" />
        <div>
          <h3 className="text-lg font-semibold text-foreground">{task.title}</h3>
          <p className="text-sm text-muted-foreground">{task.client_name}</p>
        </div>
      </div>

      <div className="pt-4 border-t space-y-3">
        <div>
          <div className="text-xs text-muted-foreground mb-1">BESKRIVELSE</div>
          <div className="text-sm text-foreground">{task.description}</div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="text-xs text-muted-foreground mb-1">PRIORITET</div>
            <div className={`text-sm font-medium ${
              task.priority === 'high' ? 'text-red-600' : 
              task.priority === 'medium' ? 'text-yellow-600' : 
              'text-green-600'
            }`}>
              {task.priority === 'high' ? '🔴 Høy' : 
               task.priority === 'medium' ? '🟡 Medium' : 
               '🟢 Lav'}
            </div>
          </div>

          <div>
            <div className="text-xs text-muted-foreground mb-1">TILLIT</div>
            <div className="text-sm font-medium text-foreground">{task.confidence}%</div>
          </div>
        </div>

        <div>
          <div className="text-xs text-muted-foreground mb-1">KATEGORI</div>
          <div className="text-sm text-foreground capitalize">{task.category}</div>
        </div>
      </div>

      <div className="pt-4 border-t">
        <button className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors">
          Åpne oppgave
        </button>
      </div>
    </div>
  );
}

export function RightPanel({ selectedItem, type }: RightPanelProps) {
  return (
    <div className="h-full flex flex-col bg-card border rounded-lg overflow-hidden">
      {/* Details Section (40%) */}
      <div className="flex-[2] border-b overflow-y-auto p-4">
        {!selectedItem && (
          <div className="h-full flex items-center justify-center text-center">
            <div>
              <div className="text-4xl mb-2">👆</div>
              <div className="text-sm text-muted-foreground">
                Velg en {type === 'client' ? 'klient' : 'oppgave'} for å se detaljer
              </div>
            </div>
          </div>
        )}

        {selectedItem && type === 'client' && <ClientDetails client={selectedItem as Client} />}
        {selectedItem && type === 'task' && <TaskDetails task={selectedItem as Task} />}
      </div>

      {/* Chat Section (60%) */}
      <div className="flex-[3] overflow-hidden">
        <FixedChatPanel context={selectedItem} />
      </div>
    </div>
  );
}
