/**
 * Date/Time Utilities - Client-Safe Formatting
 * 
 * PROBLEM: Server-rendered timestamps cause hydration mismatches
 * because server uses UTC while client uses local timezone.
 * 
 * SOLUTION: Always format dates on client-side only, or use
 * these utilities that handle SSR/client differences properly.
 */

import { useEffect, useState } from 'react';

/**
 * Hook to detect if component is mounted (client-side)
 * Use this to conditionally render timestamps
 * 
 * @example
 * const mounted = useClientOnly();
 * return mounted ? <span>{formatTime(date)}</span> : null;
 */
export function useClientOnly(): boolean {
  const [mounted, setMounted] = useState(false);
  
  useEffect(() => {
    setMounted(true);
  }, []);
  
  return mounted;
}

/**
 * Format timestamp for display (Norwegian locale)
 * Safe for client-side rendering only
 * 
 * @param date - Date object or ISO string
 * @returns Formatted time string (HH:MM)
 */
export function formatTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleTimeString('nb-NO', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format date for display (Norwegian locale)
 * Safe for client-side rendering only
 * 
 * @param date - Date object or ISO string
 * @returns Formatted date string (DD.MM.YYYY)
 */
export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('nb-NO', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

/**
 * Format date and time for display (Norwegian locale)
 * Safe for client-side rendering only
 * 
 * @param date - Date object or ISO string
 * @returns Formatted datetime string (DD.MM.YYYY HH:MM)
 */
export function formatDateTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleString('nb-NO', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format relative time (e.g., "2 timer siden", "i går")
 * Safe for client-side rendering only
 * 
 * @param date - Date object or ISO string
 * @returns Relative time string in Norwegian
 */
export function formatRelativeTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'nå nettopp';
  if (diffMins < 60) return `${diffMins} min siden`;
  if (diffHours < 24) return `${diffHours} timer siden`;
  if (diffDays === 1) return 'i går';
  if (diffDays < 7) return `${diffDays} dager siden`;
  
  return formatDate(d);
}

/**
 * ClientSafeTimestamp component - wraps timestamp rendering
 * to prevent hydration errors
 * 
 * @example
 * <ClientSafeTimestamp date={message.timestamp} format="time" />
 */
interface ClientSafeTimestampProps {
  date: Date | string;
  format?: 'time' | 'date' | 'datetime' | 'relative';
  fallback?: string;
}

export function ClientSafeTimestamp({ 
  date, 
  format = 'time',
  fallback = '' 
}: ClientSafeTimestampProps) {
  const mounted = useClientOnly();
  
  if (!mounted) {
    return <span>{fallback}</span>;
  }
  
  let formatted: string;
  switch (format) {
    case 'time':
      formatted = formatTime(date);
      break;
    case 'date':
      formatted = formatDate(date);
      break;
    case 'datetime':
      formatted = formatDateTime(date);
      break;
    case 'relative':
      formatted = formatRelativeTime(date);
      break;
    default:
      formatted = formatTime(date);
  }
  
  return <span>{formatted}</span>;
}
