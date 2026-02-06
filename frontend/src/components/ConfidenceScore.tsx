import React from 'react';
import clsx from 'clsx';

interface ConfidenceScoreProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
}

export const ConfidenceScore: React.FC<ConfidenceScoreProps> = ({ score, size = 'md' }) => {
  const getColor = (score: number) => {
    if (score >= 90) return 'text-accent-green';
    if (score >= 75) return 'text-accent-yellow';
    return 'text-accent-red';
  };

  const getBarColor = (score: number) => {
    if (score >= 90) return 'bg-accent-green';
    if (score >= 75) return 'bg-accent-yellow';
    return 'bg-accent-red';
  };

  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-dark-hover rounded-full h-2 overflow-hidden">
        <div
          className={clsx('h-full transition-all duration-300', getBarColor(score))}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className={clsx('font-semibold', getColor(score), sizeClasses[size])}>
        {score}%
      </span>
    </div>
  );
};
