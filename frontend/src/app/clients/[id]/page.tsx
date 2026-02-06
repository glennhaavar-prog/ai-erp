"use client";

import { Layout } from '@/components/Layout';
import Link from 'next/link';
import { useParams } from 'next/navigation';

export default function ClientPage() {
  const params = useParams();
  const clientId = params?.id as string;

  return (
    <Layout>
      <div className="p-6 max-w-7xl mx-auto">
        {/* Back to Multi-Client */}
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium"
          >
            ← Back to Multi-Client Dashboard
          </Link>
        </div>

        {/* Client Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Client View
          </h1>
          <p className="text-gray-600">Client ID: {clientId}</p>
        </div>

        {/* Client-Specific Sections */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Customer Reports */}
          <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">📊 Customer Reports</h2>
            <p className="text-gray-600 mb-4">View and generate customer-specific reports</p>
            <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
              View Reports
            </button>
          </div>

          {/* Member Reports */}
          <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">👥 Member Reports</h2>
            <p className="text-gray-600 mb-4">Access member-specific data and analytics</p>
            <button className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">
              View Members
            </button>
          </div>

          {/* Reporting */}
          <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-purple-500">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">📈 Reporting</h2>
            <p className="text-gray-600 mb-4">Generate compliance and financial reports</p>
            <button className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700">
              Generate Reports
            </button>
          </div>

          {/* Other Client Functions */}
          <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-orange-500">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">⚙️ Client Settings</h2>
            <p className="text-gray-600 mb-4">Manage client configuration and preferences</p>
            <button className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700">
              Settings
            </button>
          </div>
        </div>

        {/* Paradigm Explanation */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">
            💡 Kontali's Multi-Client Paradigm
          </h3>
          <p className="text-blue-800">
            <strong>Traditional systems (PowerOffice/Tripletex):</strong> You work one client at a time, switching context entirely.
          </p>
          <p className="text-blue-800 mt-2">
            <strong>Kontali approach:</strong> Start with multi-client view (all unsure cases), then drill down to client-specific work when needed.
          </p>
        </div>
      </div>
    </Layout>
  );
}
