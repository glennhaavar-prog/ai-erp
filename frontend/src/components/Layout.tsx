'use client';

import React from 'react';
import { Navigation } from './Navigation';
import { KontaliLogo } from './icons/KontaliLogo';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card border-b border-border">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <KontaliLogo size={40} showText={false} />
              <div>
                <h1 className="text-2xl font-heading font-bold text-foreground">Kontali ERP</h1>
                <p className="text-sm text-muted-foreground">AI-drevet regnskapsautomatisering</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <button className="px-4 py-2 bg-card hover:bg-muted rounded-xl text-foreground transition-colors border border-border">
                Innstillinger
              </button>
              <div className="w-10 h-10 bg-gradient-primary rounded-full flex items-center justify-center text-white font-semibold shadow-glow-indigo">
                KE
              </div>
            </div>
          </div>
          
          {/* Navigation Menu */}
          <div className="mt-4">
            <Navigation />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-card border-t border-border mt-12">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between text-sm text-muted">
            <div className="flex items-center gap-2">
              <KontaliLogo size={24} showText={false} />
              <span>© 2026 Kontali ERP</span>
            </div>
            <div className="flex gap-4">
              <a href="#" className="hover:text-primary transition-colors">Hjelp</a>
              <a href="#" className="hover:text-primary transition-colors">API Docs</a>
              <a href="#" className="hover:text-primary transition-colors">Status</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
