'use client';

import { ClientListDashboard } from '@/components/ClientListDashboard';
import { FixedChatPanel } from '@/components/FixedChatPanel';
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

  // Show multi-client dashboard in multi-client mode
  if (viewMode === 'multi-client') {
    return (
      <div className="h-full flex gap-6 p-6">
        {/* Left: Client list with traffic lights (60%) */}
        <div className="flex-[6] min-w-0">
          <ClientListDashboard />
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
