'use client';

import { ClientListDashboard } from '@/components/ClientListDashboard';
import { FixedChatPanel } from '@/components/FixedChatPanel';
import { MiniStatusWidget } from '@/components/MiniStatusWidget';
import { useViewMode } from '@/contexts/ViewModeContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function Home() {
  const { viewMode } = useViewMode();
  const router = useRouter();

  // Redirect to dashboard when in client mode
  useEffect(() => {
    if (viewMode === 'client') {
      router.push('/dashboard');
    }
  }, [viewMode, router]);

  // Show multi-client dashboard in multi-client mode (Unified Dashboard - Forslag 1)
  if (viewMode === 'multi-client') {
    return (
      <div className="h-full flex gap-6 p-6">
        {/* Left: Mini status widget + Client list (60%) */}
        <div className="flex-[6] min-w-0 flex flex-col">
          <MiniStatusWidget />
          <div className="flex-1 min-h-0">
            <ClientListDashboard />
          </div>
        </div>
        
        {/* Right: Fixed chat panel (40%) */}
        <div className="flex-[4] min-w-0">
          <FixedChatPanel />
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
