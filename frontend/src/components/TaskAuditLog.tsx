"use client";

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { FileText } from 'lucide-react';

interface AuditLogEntry {
  id: string;
  action: string;
  performed_by: string;
  performed_at: string;
  result?: 'ok' | 'deviation';
  result_description?: string;
  documentation_reference?: string;
}

interface TaskAuditLogProps {
  taskId: string;
  onClose: () => void;
}

const TaskAuditLog: React.FC<TaskAuditLogProps> = ({ taskId, onClose }) => {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAuditLog();
  }, [taskId]);

  const fetchAuditLog = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/tasks/${taskId}/audit-log`);
      const data = await response.json();
      setLogs(data);
    } catch (error) {
      console.error('Error fetching audit log:', error);
    } finally {
      setLoading(false);
    }
  };

  const getActionLabel = (action: string): string => {
    const labels: Record<string, string> = {
      created: 'Opprettet',
      completed: 'Fullført',
      marked_deviation: 'Markert med avvik',
      manually_checked: 'Manuelt krysset av',
      auto_completed: 'Auto-fullført av AI'
    };
    return labels[action] || action;
  };

  const getResultBadge = (result?: string) => {
    if (!result) return null;
    
    if (result === 'ok') {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
          OK
        </span>
      );
    }
    
    if (result === 'deviation') {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
          Avvik
        </span>
      );
    }
    
    return null;
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('nb-NO', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Sporbarhet / Audit Trail</DialogTitle>
          <DialogDescription>
            Full historikk for oppgaven. Loggen kan ikke endres eller slettes.
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-[500px] mt-4">
          {loading ? (
            <div className="text-center py-8">Laster...</div>
          ) : logs.length === 0 ? (
            <div className="text-center py-8 text-gray-500">Ingen historikk</div>
          ) : (
            <div className="space-y-4">
              {logs.map((log, index) => (
                <div
                  key={log.id}
                  className={`p-4 rounded-lg border ${
                    index === 0 ? 'border-blue-200 bg-blue-50' : 'border-gray-200'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{getActionLabel(log.action)}</span>
                      {getResultBadge(log.result)}
                    </div>
                    <span className="text-sm text-gray-500">
                      {formatDateTime(log.performed_at)}
                    </span>
                  </div>

                  <div className="text-sm text-gray-600 mb-2">
                    Utført av: <span className="font-medium">{log.performed_by}</span>
                  </div>

                  {log.result_description && (
                    <div className="text-sm text-gray-700 mt-2 p-2 bg-white rounded border border-gray-200">
                      {log.result_description}
                    </div>
                  )}

                  {log.documentation_reference && (
                    <div className="mt-2">
                      <a
                        href={log.documentation_reference}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
                      >
                        <FileText className="w-4 h-4" />
                        Se dokumentasjon
                      </a>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
};

export default TaskAuditLog;
