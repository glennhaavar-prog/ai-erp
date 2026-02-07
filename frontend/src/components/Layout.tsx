'use client';

import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import Copilot from './Copilot';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="flex h-screen overflow-hidden bg-bg-darkest">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Area */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Topbar */}
        <Topbar />

        {/* Content */}
        <main className="flex-1 overflow-y-auto px-8 py-7 bg-bg-darkest scrollbar-thin scrollbar-thumb-border-light scrollbar-track-transparent">
          {children}
        </main>
      </div>

      {/* AI Copilot - Context-Aware Assistant */}
      <Copilot />
    </div>
  );
};
