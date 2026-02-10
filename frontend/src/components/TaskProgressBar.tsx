"use client";

import React from 'react';
import { Progress } from '@/components/ui/progress';
import { CheckCircle2, Clock, AlertTriangle, Circle } from 'lucide-react';

interface TaskProgressBarProps {
  total: number;
  completed: number;
  in_progress: number;
  not_started: number;
  deviations: number;
}

const TaskProgressBar: React.FC<TaskProgressBarProps> = ({
  total,
  completed,
  in_progress,
  not_started,
  deviations
}) => {
  const progressPercent = total > 0 ? (completed / total) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm font-medium">
          <span>Fremdrift</span>
          <span>{completed}/{total} fullført ({Math.round(progressPercent)}%)</span>
        </div>
        <Progress value={progressPercent} className="h-3" />
      </div>

      {/* Status Breakdown */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Completed */}
        <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 border border-green-200">
          <CheckCircle2 className="w-5 h-5 text-green-600" />
          <div>
            <div className="text-2xl font-bold text-green-700">{completed}</div>
            <div className="text-xs text-green-600">Fullført</div>
          </div>
        </div>

        {/* In Progress */}
        <div className="flex items-center gap-2 p-3 rounded-lg bg-blue-50 border border-blue-200">
          <Clock className="w-5 h-5 text-blue-600" />
          <div>
            <div className="text-2xl font-bold text-blue-700">{in_progress}</div>
            <div className="text-xs text-blue-600">Pågår</div>
          </div>
        </div>

        {/* Not Started */}
        <div className="flex items-center gap-2 p-3 rounded-lg bg-gray-50 border border-gray-200">
          <Circle className="w-5 h-5 text-gray-600" />
          <div>
            <div className="text-2xl font-bold text-gray-700">{not_started}</div>
            <div className="text-xs text-gray-600">Ikke startet</div>
          </div>
        </div>

        {/* Deviations */}
        <div className="flex items-center gap-2 p-3 rounded-lg bg-orange-50 border border-orange-200">
          <AlertTriangle className="w-5 h-5 text-orange-600" />
          <div>
            <div className="text-2xl font-bold text-orange-700">{deviations}</div>
            <div className="text-xs text-orange-600">Avvik</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskProgressBar;
