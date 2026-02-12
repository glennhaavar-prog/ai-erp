/**
 * Keyboard Shortcuts Help Overlay
 * Shows all available shortcuts when user presses "?"
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { KeyboardShortcut, formatShortcut } from '@/hooks/useKeyboardShortcuts';

const DEFAULT_SHORTCUTS: KeyboardShortcut[] = [
  // Navigation
  {
    key: 'k',
    metaKey: true,
    description: 'Åpne global søk',
    category: 'navigation',
    global: true,
    action: () => {},
  },
  {
    key: 'j',
    description: 'Neste rad i liste',
    category: 'navigation',
    action: () => {},
  },
  {
    key: 'k',
    description: 'Forrige rad i liste',
    category: 'navigation',
    action: () => {},
  },
  {
    key: 'Enter',
    description: 'Åpne valgt element',
    category: 'navigation',
    action: () => {},
  },
  {
    key: 'Escape',
    description: 'Lukk modal/avbryt',
    category: 'navigation',
    global: true,
    action: () => {},
  },
  {
    key: '?',
    shiftKey: true,
    description: 'Vis denne hjelpen',
    category: 'navigation',
    global: true,
    action: () => {},
  },

  // Actions
  {
    key: 'n',
    description: 'Ny (avhenger av side)',
    category: 'actions',
    action: () => {},
  },
  {
    key: 'd',
    description: 'Slett valgt',
    category: 'actions',
    action: () => {},
  },

  // Editing
  {
    key: 'e',
    description: 'Rediger',
    category: 'editing',
    action: () => {},
  },
  {
    key: 's',
    metaKey: true,
    description: 'Lagre',
    category: 'editing',
    global: true,
    action: () => {},
  },
];

interface KeyboardShortcutsHelpProps {
  additionalShortcuts?: KeyboardShortcut[];
}

export function KeyboardShortcutsHelp({ additionalShortcuts = [] }: KeyboardShortcutsHelpProps) {
  const [open, setOpen] = useState(false);

  // Listen for help shortcut
  useEffect(() => {
    const handleHelp = () => setOpen(true);
    document.addEventListener('keyboard:help', handleHelp);
    return () => document.removeEventListener('keyboard:help', handleHelp);
  }, []);

  // Also listen for direct key press as backup
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '?' && e.shiftKey) {
        e.preventDefault();
        setOpen(true);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const allShortcuts = [...DEFAULT_SHORTCUTS, ...additionalShortcuts];

  const groupedShortcuts = allShortcuts.reduce((acc, shortcut) => {
    if (!acc[shortcut.category]) {
      acc[shortcut.category] = [];
    }
    acc[shortcut.category].push(shortcut);
    return acc;
  }, {} as Record<string, KeyboardShortcut[]>);

  const categoryTitles = {
    navigation: 'Navigasjon',
    actions: 'Handlinger',
    editing: 'Redigering',
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span>⌨️</span> Tastatursnarveier
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {Object.entries(groupedShortcuts).map(([category, shortcuts]) => (
            <div key={category}>
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                {categoryTitles[category as keyof typeof categoryTitles] || category}
              </h3>
              
              <div className="space-y-2">
                {shortcuts.map((shortcut, index) => (
                  <div
                    key={`${category}-${index}`}
                    className="flex items-center justify-between py-2 px-3 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800/50"
                  >
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {shortcut.description}
                    </span>
                    
                    <div className="flex items-center gap-1">
                      {formatShortcut(shortcut).split('+').map((key, i, arr) => (
                        <React.Fragment key={i}>
                          <kbd className="inline-flex items-center justify-center px-2 py-1 text-xs font-semibold text-gray-800 dark:text-gray-200 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded">
                            {key}
                          </kbd>
                          {i < arr.length - 1 && (
                            <span className="text-gray-400 text-xs">+</span>
                          )}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="pt-4 border-t border-gray-200 dark:border-gray-800">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            💡 Tips: De fleste snarveier fungerer bare når du ikke skriver i et tekstfelt.
            Unntak er merket med stjerne (*).
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Provider component to include at app root
export function KeyboardShortcutsProvider({ children }: { children: React.ReactNode }) {
  // Load user preferences from localStorage
  useEffect(() => {
    const preferences = localStorage.getItem('keyboard_shortcuts_preferences');
    if (preferences) {
      try {
        const parsed = JSON.parse(preferences);
        // Apply user customizations here if needed
        console.log('Loaded keyboard preferences:', parsed);
      } catch (e) {
        console.error('Failed to load keyboard preferences:', e);
      }
    }
  }, []);

  return (
    <>
      {children}
      <KeyboardShortcutsHelp />
    </>
  );
}
