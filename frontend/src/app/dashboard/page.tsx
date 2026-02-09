import TrustDashboard from '@/components/TrustDashboard';
import ReceiptVerificationDashboard from '@/components/ReceiptVerificationDashboard';
import DemoBanner from '@/components/DemoBanner';
import DemoTestButton from '@/components/DemoTestButton';

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-950">
      {/* Demo Banner */}
      <DemoBanner />
      
      <div className="space-y-8 p-6">
        {/* Header with Demo Test Button */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Dashboard</h1>
            <p className="text-gray-400 mt-1">Oversikt over bilag og bokføring</p>
          </div>
          <DemoTestButton />
        </div>

        {/* Receipt Verification Dashboard - Primary view for accountant */}
        <ReceiptVerificationDashboard />
        
        {/* Trust Dashboard - System-wide monitoring */}
        <div className="pt-8 border-t border-gray-700">
          <h2 className="text-2xl font-bold text-gray-200 mb-4">System Monitoring</h2>
          <TrustDashboard />
        </div>
      </div>
    </div>
  );
}
