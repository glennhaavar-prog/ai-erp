'use client';

import { useState } from 'react';
import { ClientListDashboard } from '@/components/ClientListDashboard';
import { MiniStatusWidget } from '@/components/MiniStatusWidget';
import { ViewModeToggle } from '@/components/ViewModeToggle';
import { TaskTypeFilter } from '@/components/TaskTypeFilter';
import { RightPanel } from '@/components/RightPanel';
import { useViewMode } from '@/contexts/ViewModeContext';
import ReceiptVerificationDashboard from '@/components/ReceiptVerificationDashboard';
import TrustDashboard from '@/components/TrustDashboard';
import { DashboardMetricsCards } from '@/components/DashboardMetricsCards';
import AutoBookingDashboard from '@/components/AutoBookingDashboard';

type DashboardTab = 'overview' | 'multi-client' | 'verification' | 'auto-booking' | 'system';

export default function Home() {
  const { viewMode, selectedItem } = useViewMode();
  const [activeTab, setActiveTab] = useState<DashboardTab>('overview');

  // Tab Navigation
  const tabs: { id: DashboardTab; label: string; icon: string }[] = [
    { id: 'overview', label: 'Oversikt', icon: '📊' },
    { id: 'multi-client', label: 'Klient Oversikt', icon: '👥' },
    { id: 'verification', label: 'Bilagsføring', icon: '📄' },
    { id: 'auto-booking', label: 'Auto-Bokføring', icon: '🤖' },
    { id: 'system', label: 'System Status', icon: '⚙️' },
  ];

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Top Bar with Tab Navigation */}
      <div className="border-b bg-background">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-2">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all
                  ${
                    activeTab === tab.id
                      ? 'bg-accent-blue text-white shadow-md'
                      : 'text-text-secondary hover:bg-bg-hover hover:text-text-primary'
                  }
                `}
              >
                <span className="text-lg">{tab.icon}</span>
                <span className="text-sm">{tab.label}</span>
              </button>
            ))}
          </div>

          {activeTab === 'multi-client' && (
            <div className="flex items-center gap-4">
              <ViewModeToggle />
              <TaskTypeFilter />
            </div>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'overview' && (
          <div className="h-full overflow-auto">
            <DashboardMetricsCards />
          </div>
        )}

        {activeTab === 'multi-client' && (
          <div className="h-full flex gap-6 p-6 overflow-hidden">
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
        )}

        {activeTab === 'verification' && (
          <div className="h-full overflow-auto">
            <ReceiptVerificationDashboard />
          </div>
        )}

        {activeTab === 'auto-booking' && (
          <div className="h-full overflow-auto">
            <AutoBookingDashboard />
          </div>
        )}

        {activeTab === 'system' && (
          <div className="h-full overflow-auto p-6">
            <div className="max-w-7xl mx-auto">
              <h2 className="text-2xl font-bold text-foreground mb-4">System Monitoring</h2>
              <TrustDashboard />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
