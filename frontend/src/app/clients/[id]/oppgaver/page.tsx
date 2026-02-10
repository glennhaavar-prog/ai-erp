"use client";

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import TaskList from '@/components/TaskList';
import TaskProgressBar from '@/components/TaskProgressBar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { PlusCircle } from 'lucide-react';

interface Client {
  id: string;
  name: string;
}

interface TaskSummary {
  total: number;
  completed: number;
  in_progress: number;
  not_started: number;
  deviations: number;
}

const OppgaverPage = () => {
  const params = useParams();
  const clientId = params?.id as string;

  const [client, setClient] = useState<Client | null>(null);
  const [periodYear, setPeriodYear] = useState<number>(new Date().getFullYear());
  const [periodMonth, setPeriodMonth] = useState<number>(new Date().getMonth() + 1);
  const [taskSummary, setTaskSummary] = useState<TaskSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClient();
  }, [clientId]);

  useEffect(() => {
    fetchTaskSummary();
  }, [clientId, periodYear, periodMonth]);

  const fetchClient = async () => {
    try {
      const response = await fetch(`/api/clients/${clientId}`);
      const data = await response.json();
      setClient(data);
    } catch (error) {
      console.error('Error fetching client:', error);
    }
  };

  const fetchTaskSummary = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        client_id: clientId,
        period_year: periodYear.toString(),
        period_month: periodMonth.toString(),
      });

      const response = await fetch(`/api/tasks?${params.toString()}`);
      const data = await response.json();
      
      setTaskSummary({
        total: data.total,
        completed: data.completed,
        in_progress: data.in_progress,
        not_started: data.not_started,
        deviations: data.deviations
      });
    } catch (error) {
      console.error('Error fetching task summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyTemplate = async () => {
    try {
      await fetch('/api/tasks/templates/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: clientId,
          period_year: periodYear,
          period_month: periodMonth
        })
      });
      
      // Refresh tasks
      window.location.reload();
    } catch (error) {
      console.error('Error applying template:', error);
    }
  };

  const years = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - 2 + i);
  const months = [
    'Januar', 'Februar', 'Mars', 'April', 'Mai', 'Juni',
    'Juli', 'August', 'September', 'Oktober', 'November', 'Desember'
  ];

  if (!client) {
    return <div className="flex justify-center items-center h-screen">Laster...</div>;
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Oppgaveadministrasjon</h1>
          <p className="text-gray-600 mt-1">Kvalitetssystem og sporbarhet</p>
        </div>

        <Button onClick={handleApplyTemplate} className="gap-2">
          <PlusCircle className="w-4 h-4" />
          Opprett oppgaver for periode
        </Button>
      </div>

      {/* Period Selector */}
      <Card>
        <CardHeader>
          <CardTitle>Velg periode</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">År</label>
              <Select value={periodYear.toString()} onValueChange={(v) => setPeriodYear(parseInt(v))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {years.map(year => (
                    <SelectItem key={year} value={year.toString()}>
                      {year}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">Måned</label>
              <Select value={periodMonth.toString()} onValueChange={(v) => setPeriodMonth(parseInt(v))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {months.map((month, index) => (
                    <SelectItem key={index + 1} value={(index + 1).toString()}>
                      {month}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Progress Summary */}
      {!loading && taskSummary && taskSummary.total > 0 && (
        <TaskProgressBar
          total={taskSummary.total}
          completed={taskSummary.completed}
          in_progress={taskSummary.in_progress}
          not_started={taskSummary.not_started}
          deviations={taskSummary.deviations}
        />
      )}

      {/* Task List */}
      <TaskList
        clientId={clientId}
        clientName={client.name}
        periodYear={periodYear}
        periodMonth={periodMonth}
      />

      {/* Empty State */}
      {!loading && taskSummary && taskSummary.total === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <p className="text-gray-600 mb-4">
              Ingen oppgaver opprettet for denne perioden ennå.
            </p>
            <Button onClick={handleApplyTemplate} className="gap-2">
              <PlusCircle className="w-4 h-4" />
              Opprett standardoppgaver
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default OppgaverPage;
