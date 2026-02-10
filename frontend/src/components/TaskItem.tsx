"use client";

import React from 'react';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import { FileText, AlertTriangle } from 'lucide-react';

interface Task {
  id: string;
  name: string;
  description?: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'deviation';
  completed_by?: string;
  completed_at?: string;
  documentation_url?: string;
  ai_comment?: string;
}

interface TaskItemProps {
  task: Task;
  onComplete: (taskId: string) => void;
  onShowAuditLog: (taskId: string) => void;
}

const TaskItem: React.FC<TaskItemProps> = ({ task, onComplete, onShowAuditLog }) => {
  const isCompleted = task.status === 'completed';
  const isDeviation = task.status === 'deviation';

  const handleCheckboxChange = (checked: boolean) => {
    if (checked && !isCompleted && !isDeviation) {
      onComplete(task.id);
    }
  };

  const getStatusIcon = () => {
    if (isDeviation) {
      return <AlertTriangle className="w-5 h-5 text-orange-500" />;
    }
    return null;
  };

  const getCompletedDate = () => {
    if (!task.completed_at) return '';
    const date = new Date(task.completed_at);
    return date.toLocaleDateString('nb-NO', { day: '2-digit', month: '2-digit' });
  };

  return (
    <div className={`flex items-center justify-between p-3 rounded-lg border ${
      isDeviation ? 'border-orange-200 bg-orange-50' : 
      isCompleted ? 'border-green-200 bg-green-50' : 
      'border-gray-200 hover:bg-gray-50'
    }`}>
      <div className="flex items-center gap-3 flex-1">
        {/* Checkbox or Status Icon */}
        <div className="flex-shrink-0">
          {isDeviation ? (
            getStatusIcon()
          ) : (
            <Checkbox
              checked={isCompleted}
              onCheckedChange={handleCheckboxChange}
              disabled={isCompleted}
              className={isCompleted ? 'bg-green-500 border-green-500' : ''}
            />
          )}
        </div>

        {/* Task Name */}
        <div className="flex-1">
          <div className={`font-medium ${isCompleted ? 'text-gray-500 line-through' : ''}`}>
            {task.name}
          </div>
          
          {/* AI Comment for deviations */}
          {isDeviation && task.ai_comment && (
            <div className="text-sm text-orange-600 mt-1">
              {task.ai_comment}
            </div>
          )}
        </div>

        {/* Completed By */}
        {task.completed_by && (
          <div className="text-sm text-gray-600 min-w-[60px] text-center">
            {task.completed_by}
          </div>
        )}

        {/* Completed Date */}
        {task.completed_at && (
          <div className="text-sm text-gray-600 min-w-[50px] text-center">
            {getCompletedDate()}
          </div>
        )}

        {/* Documentation Link */}
        {task.documentation_url && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => window.open(task.documentation_url, '_blank')}
            className="flex-shrink-0"
          >
            <FileText className="w-4 h-4" />
          </Button>
        )}
      </div>

      {/* Audit Log Button */}
      {(isCompleted || isDeviation) && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onShowAuditLog(task.id)}
          className="ml-2 text-xs"
        >
          Sporbarhet
        </Button>
      )}
    </div>
  );
};

export default TaskItem;
