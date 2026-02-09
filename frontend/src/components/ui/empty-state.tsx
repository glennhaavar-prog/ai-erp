/**
 * EmptyState Component
 * Friendly empty state with icon, message, and optional CTA
 * 
 * Usage:
 *   <EmptyState
 *     icon={<FileX className="w-16 h-16" />}
 *     title="Ingen fakturaer"
 *     description="Det ser tomt ut her! Last opp en faktura for å komme i gang."
 *     action={<Button>Last opp faktura</Button>}
 *   />
 */

import React from 'react';
import { cn } from '@/lib/utils';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-12 px-6 text-center',
        className
      )}
    >
      {/* Icon */}
      {icon && (
        <div className="mb-4 text-muted-foreground/30">
          {icon}
        </div>
      )}

      {/* Title */}
      <h3 className="text-lg font-semibold text-foreground mb-2">
        {title}
      </h3>

      {/* Description */}
      {description && (
        <p className="text-sm text-muted-foreground max-w-md mb-6">
          {description}
        </p>
      )}

      {/* Action */}
      {action && (
        <div className="mt-2">
          {action}
        </div>
      )}
    </div>
  );
}

/**
 * Pre-made empty states for common scenarios
 */
export function NoInvoicesEmptyState({ onUpload }: { onUpload?: () => void }) {
  return (
    <EmptyState
      icon={
        <svg className="w-16 h-16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M9 12h6M9 16h6M9 8h6M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" />
          <path d="M14 2v6h6" />
          <path d="M3 18L21 6" strokeWidth="2" />
        </svg>
      }
      title="Ingen fakturaer"
      description="Det ser tomt ut her! Last opp en faktura for å komme i gang med AI-assistert bokføring."
      action={
        onUpload && (
          <button
            onClick={onUpload}
            className="px-6 py-3 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 transition-colors font-medium"
          >
            Last opp faktura
          </button>
        )
      }
    />
  );
}

export function NoTransactionsEmptyState() {
  return (
    <EmptyState
      icon={
        <svg className="w-16 h-16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
          <path d="M3 12L21 6" strokeWidth="2" />
        </svg>
      }
      title="Ingen banktransaksjoner"
      description="Importer banktransaksjoner for å starte avstemming og automatisk matching mot fakturaer."
    />
  );
}

export function NoDataEmptyState({ title = "Ingen data", description }: { title?: string; description?: string }) {
  return (
    <EmptyState
      icon={
        <svg className="w-16 h-16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      }
      title={title}
      description={description || "Når du får data, vil den vises her."}
    />
  );
}

export function SearchEmptyState({ query }: { query?: string }) {
  return (
    <EmptyState
      icon={
        <svg className="w-16 h-16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          <path d="M3 18L21 6" strokeWidth="2" />
        </svg>
      }
      title="Ingen treff"
      description={query ? `Ingen resultater for "${query}". Prøv et annet søk.` : "Søk returnerte ingen resultater."}
    />
  );
}
