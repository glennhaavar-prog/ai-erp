"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import TaskItem from './TaskItem';
import TaskAuditLog from './TaskAuditLog';

interface Task {
  id: string;
  name: string;
  description?: string;
  category: 'avstemming' | 'rapportering' | 'bokføring' | 'compliance';
  status: 'not_started' | 'in_progress' | 'completed' | 'deviation';
  completed_by?: string;
  completed_at?: string;
  documentation_url?: string;
  ai_comment?: string;
  subtasks?: Task[];
}

interface TaskListData {
  tasks: Task[];
  total: number;
  completed: number;
  in_progress: number;
  not_started: number;
  deviations: number;
}

interface TaskListProps {
  clientId: string;
  clientName: string;
  periodYear: number;
  periodMonth?: number;
}

const TaskList: React.FC<TaskListProps> = ({ clientId, clientName, periodYear, periodMonth }) => {
  const [taskData, setTaskData] = useState<TaskListData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState<string | null>(null);
  const [showAuditLog, setShowAuditLog] = useState(false);

  useEffect(() => {
    fetchTasks();
  }, [clientId, periodYear, periodMonth]);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        client_id: clientId,
        period_year: periodYear.toString(),
      });
      
      if (periodMonth) {
        params.append('period_month', periodMonth.toString());
      }

      const response = await fetch(`/api/tasks?${params.toString()}`);
      const data = await response.json();
      setTaskData(data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTaskComplete = async (taskId: string) => {
    try {
      await fetch(`/api/tasks/${taskId}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          completed_by: 'Regnskapsfører', // In production, get from auth context
          notes: 'Manuelt krysset av'
        })
      });
      
      fetchTasks(); // Refresh
    } catch (error) {
      console.error('Error completing task:', error);
    }
  };

  const handleShowAuditLog = (taskId: string) => {
    setSelectedTask(taskId);
    setShowAuditLog(true);
  };

  if (loading) {
    return <div className="flex justify-center p-8">Laster oppgaver...</div>;
  }

  if (!taskData) {
    return <div className="text-center p-8">Kunne ikke laste oppgaver</div>;
  }

  const progressPercent = taskData.total > 0 
    ? (taskData.completed / taskData.total) * 100 
    : 0;

  const periodLabel = periodMonth 
    ? `${getMonthName(periodMonth)} ${periodYear}`
    : `${periodYear}`;

  const groupedTasks = groupTasksByCategory(taskData.tasks);

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle>
            Oppgaver – Klient: {clientName} – {periodLabel}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>{taskData.completed}/{taskData.total} utført</span>
              <span>{Math.round(progressPercent)}%</span>
            </div>
            <Progress value={progressPercent} className="h-2" />
            
            {taskData.deviations > 0 && (
              <div className="text-sm text-orange-600 mt-2">
                ⚠ {taskData.deviations} oppgave(r) med avvik
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Task Categories */}
      {Object.entries(groupedTasks).map(([category, tasks]) => (
        <Card key={category}>
          <CardHeader>
            <CardTitle className="text-lg">{getCategoryName(category)}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {tasks.map(task => (
                <TaskItem
                  key={task.id}
                  task={task}
                  onComplete={handleTaskComplete}
                  onShowAuditLog={handleShowAuditLog}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      ))}

      {/* Audit Log Modal */}
      {showAuditLog && selectedTask && (
        <TaskAuditLog
          taskId={selectedTask}
          onClose={() => setShowAuditLog(false)}
        />
      )}
    </div>
  );
};

// Helper functions
function groupTasksByCategory(tasks: Task[]): Record<string, Task[]> {
  const grouped: Record<string, Task[]> = {
    bokføring: [],
    avstemming: [],
    rapportering: [],
    compliance: []
  };

  tasks.forEach(task => {
    if (task.category && grouped[task.category]) {
      grouped[task.category].push(task);
    }
  });

  // Remove empty categories
  Object.keys(grouped).forEach(key => {
    if (grouped[key].length === 0) {
      delete grouped[key];
    }
  });

  return grouped;
}

function getCategoryName(category: string): string {
  const names: Record<string, string> = {
    bokføring: 'Bokføring',
    avstemming: 'Avstemming',
    rapportering: 'Rapportering',
    compliance: 'Compliance'
  };
  return names[category] || category;
}

function getMonthName(month: number): string {
  const months = [
    'Januar', 'Februar', 'Mars', 'April', 'Mai', 'Juni',
    'Juli', 'August', 'September', 'Oktober', 'November', 'Desember'
  ];
  return months[month - 1] || month.toString();
}

export default TaskList;
