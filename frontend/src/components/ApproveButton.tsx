import React, { useState } from 'react';
import clsx from 'clsx';

interface ApproveButtonProps {
  itemId: string;
  onApprove: (id: string) => Promise<void>;
  disabled?: boolean;
}

export const ApproveButton: React.FC<ApproveButtonProps> = ({ itemId, onApprove, disabled }) => {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    try {
      await onApprove(itemId);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={disabled || loading}
      className={clsx(
        'px-6 py-2.5 rounded-lg font-medium transition-all',
        'bg-accent-green hover:bg-green-600 text-white',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        loading && 'animate-pulse'
      )}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Godkjenner...
        </span>
      ) : (
        '✓ Godkjenn'
      )}
    </button>
  );
};
