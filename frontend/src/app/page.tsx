'use client';

import { ClientListDashboard } from '@/components/ClientListDashboard';
import { MiniStatusWidget } from '@/components/MiniStatusWidget';
import { ViewModeToggle } from '@/components/ViewModeToggle';
import { TaskTypeFilter } from '@/components/TaskTypeFilter';
import { RightPanel } from '@/components/RightPanel';
import { useViewMode } from '@/contexts/ViewModeContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function Home() {
  const { viewMode, selectedItem } = useViewMode();
  const router = useRouter();

  // Redirect to dashboard when in client mode
  useEffect(() => {
    if (viewMode === 'client') {
      router.push('/dashboard');
    }
  }, [viewMode, router]);

  // Show multi-client dashboard in multi-client mode (Unified Dashboard - Forslag 1 + Task 6)
  if (viewMode === 'multi-client') {
    return (
      <div className="h-full flex flex-col">
        {/* Top Bar with Toggles */}
        <div className="flex justify-between items-center p-4 border-b bg-background">
          <ViewModeToggle />
          <TaskTypeFilter />
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex gap-6 p-6 overflow-hidden">
          {/* Left: Mini status widget + Client list (60%) */}
          <div className="flex-[6] min-w-0 flex flex-col">
            <MiniStatusWidget />
            <div className="flex-1 min-h-0">
              <ClientListDashboard />
            </div>
          </div>
          
          {/* Right: Details + Chat Panel (40%) */}
          <div className="flex-[4] min-w-0">
            <RightPanel selectedItem={selectedItem} type="client" />
          </div>
        </div>
      </div>
    );
  }

  // Fallback while redirecting
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-muted-foreground">Loading...</div>
    </div>
  );
}
