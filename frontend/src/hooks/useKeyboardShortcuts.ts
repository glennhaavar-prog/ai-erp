/**
 * Keyboard Shortcuts Hook
 * Define and manage keyboard shortcuts throughout the app
 */
'use client';

import { useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';

export interface KeyboardShortcut {
  key: string;
  metaKey?: boolean;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  description: string;
  action: () => void;
  category: 'navigation' | 'actions' | 'editing';
  global?: boolean; // If true, works even when input is focused
}

interface UseKeyboardShortcutsOptions {
  shortcuts: KeyboardShortcut[];
  enabled?: boolean;
}

export function useKeyboardShortcuts({ shortcuts, enabled = true }: UseKeyboardShortcutsOptions) {
  const shortcutsRef = useRef(shortcuts);

  useEffect(() => {
    shortcutsRef.current = shortcuts;
  }, [shortcuts]);

  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Check if we're in an input/textarea (unless shortcut is marked as global)
      const activeElement = document.activeElement;
      const isInput =
        activeElement?.tagName === 'INPUT' ||
        activeElement?.tagName === 'TEXTAREA' ||
        activeElement?.getAttribute('contenteditable') === 'true';

      for (const shortcut of shortcutsRef.current) {
        // Skip if in input and not a global shortcut
        if (isInput && !shortcut.global) continue;

        const keyMatches =
          e.key.toLowerCase() === shortcut.key.toLowerCase() ||
          e.code.toLowerCase() === shortcut.key.toLowerCase();

        const modifiersMatch =
          (shortcut.metaKey ? e.metaKey : !e.metaKey) &&
          (shortcut.ctrlKey ? e.ctrlKey : !e.ctrlKey) &&
          (shortcut.shiftKey ? e.shiftKey : !e.shiftKey) &&
          (shortcut.altKey ? e.altKey : !e.altKey);

        if (keyMatches && modifiersMatch) {
          e.preventDefault();
          e.stopPropagation();
          shortcut.action();
          return;
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [enabled]);
}

// Navigation shortcuts (j/k for up/down)
export function useListNavigation(
  items: any[],
  selectedIndex: number,
  onSelect: (index: number) => void,
  onOpen?: (index: number) => void
) {
  const shortcuts: KeyboardShortcut[] = [
    {
      key: 'j',
      description: 'Neste rad',
      category: 'navigation',
      action: () => {
        if (selectedIndex < items.length - 1) {
          onSelect(selectedIndex + 1);
        }
      },
    },
    {
      key: 'k',
      description: 'Forrige rad',
      category: 'navigation',
      action: () => {
        if (selectedIndex > 0) {
          onSelect(selectedIndex - 1);
        }
      },
    },
    {
      key: 'Enter',
      description: 'Åpne valgt element',
      category: 'actions',
      action: () => {
        if (onOpen && selectedIndex >= 0) {
          onOpen(selectedIndex);
        }
      },
    },
  ];

  useKeyboardShortcuts({ shortcuts });
}

// Common app-wide shortcuts
export function useGlobalShortcuts() {
  const router = useRouter();

  const shortcuts: KeyboardShortcut[] = [
    {
      key: 'n',
      description: 'Ny (kontekstavhengig)',
      category: 'actions',
      action: () => {
        // This will be handled by page-specific handlers
        document.dispatchEvent(new CustomEvent('keyboard:new'));
      },
    },
    {
      key: 'e',
      description: 'Rediger',
      category: 'editing',
      action: () => {
        document.dispatchEvent(new CustomEvent('keyboard:edit'));
      },
    },
    {
      key: 's',
      metaKey: true,
      description: 'Lagre',
      category: 'editing',
      global: true,
      action: () => {
        document.dispatchEvent(new CustomEvent('keyboard:save'));
      },
    },
    {
      key: 'd',
      description: 'Slett',
      category: 'actions',
      action: () => {
        document.dispatchEvent(new CustomEvent('keyboard:delete'));
      },
    },
    {
      key: 'Escape',
      description: 'Lukk/avbryt',
      category: 'navigation',
      global: true,
      action: () => {
        document.dispatchEvent(new CustomEvent('keyboard:escape'));
      },
    },
    {
      key: '?',
      shiftKey: true,
      description: 'Vis snarveier',
      category: 'navigation',
      global: true,
      action: () => {
        document.dispatchEvent(new CustomEvent('keyboard:help'));
      },
    },
  ];

  useKeyboardShortcuts({ shortcuts });
}

// Format shortcut for display
export function formatShortcut(shortcut: KeyboardShortcut): string {
  const parts: string[] = [];

  if (shortcut.metaKey) parts.push('⌘');
  if (shortcut.ctrlKey) parts.push('Ctrl');
  if (shortcut.altKey) parts.push('Alt');
  if (shortcut.shiftKey) parts.push('Shift');

  parts.push(shortcut.key.toUpperCase());

  return parts.join('+');
}
