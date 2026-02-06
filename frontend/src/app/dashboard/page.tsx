import { Layout } from '@/components/Layout';
import TrustDashboard from '@/components/TrustDashboard';
import ReceiptVerificationDashboard from '@/components/ReceiptVerificationDashboard';

export default function DashboardPage() {
  return (
    <Layout>
      <div className="space-y-8">
        {/* Receipt Verification Dashboard - Primary view for accountant */}
        <ReceiptVerificationDashboard />
        
        {/* Trust Dashboard - System-wide monitoring */}
        <div className="pt-8 border-t border-gray-700">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">System Monitoring</h2>
          <TrustDashboard />
        </div>
      </div>
    </Layout>
  );
}
