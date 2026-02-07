'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';

interface ReviewItemDetail {
  id: string;
  supplier: string;
  supplierOrgNumber?: string;
  amount: number;
  amountExclVat: number;
  vatAmount: number;
  currency: string;
  invoiceNumber: string;
  invoiceDate: string;
  dueDate?: string;
  description: string;
  status: string;
  priority: string;
  confidence: number;
  aiSuggestion: any;
  aiReasoning?: string;
  issueCategory: string;
  createdAt: string;
  reviewedAt?: string;
  reviewedBy?: string;
}

interface ReviewQueueDetailProps {
  itemId: string;
}

export const ReviewQueueDetail: React.FC<ReviewQueueDetailProps> = ({ itemId }) => {
  const router = useRouter();
  const [item, setItem] = useState<ReviewItemDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [notes, setNotes] = useState('');

  useEffect(() => {
    fetchItem();
  }, [itemId]);

  const fetchItem = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/review-queue/${itemId}`);
      if (response.ok) {
        const data = await response.json();
        setItem(data);
      }
    } catch (error) {
      console.error('Failed to fetch review item:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    setActionLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/review-queue/${itemId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes })
      });
      
      if (response.ok) {
        alert('✅ Approved and booked to General Ledger!');
        router.push('/');
      } else {
        const error = await response.json();
        alert(`❌ Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Failed to approve:', error);
      alert('❌ Failed to approve');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    setActionLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/review-queue/${itemId}/correct`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          bookingEntries: [], // TODO: Implement manual correction UI
          notes 
        })
      });
      
      if (response.ok) {
        alert('✅ Marked for correction!');
        router.push('/');
      } else {
        const error = await response.json();
        alert(`❌ Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Failed to reject:', error);
      alert('❌ Failed to reject');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!item) {
    return (
      <div className="text-center py-12">
        <p className="text-xl text-gray-600">Review item not found</p>
        <button
          onClick={() => router.push('/')}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => router.push('/')}
          className="text-blue-600 hover:text-blue-700 flex items-center gap-2 mb-4"
        >
          ← Back to Dashboard
        </button>
        <h1 className="text-3xl font-bold text-gray-900">Review Invoice</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Invoice Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Invoice Info Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-lg shadow-md p-6"
          >
            <h2 className="text-xl font-semibold mb-4 text-gray-900">Invoice Information</h2>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-gray-600">Supplier</label>
                <p className="font-medium text-gray-900">{item.supplier}</p>
                {item.supplierOrgNumber && (
                  <p className="text-sm text-gray-500">Org: {item.supplierOrgNumber}</p>
                )}
              </div>
              
              <div>
                <label className="text-sm text-gray-600">Invoice Number</label>
                <p className="font-medium text-gray-900">{item.invoiceNumber}</p>
              </div>
              
              <div>
                <label className="text-sm text-gray-600">Invoice Date</label>
                <p className="font-medium text-gray-900">{new Date(item.invoiceDate).toLocaleDateString('nb-NO')}</p>
              </div>
              
              {item.dueDate && (
                <div>
                  <label className="text-sm text-gray-600">Due Date</label>
                  <p className="font-medium text-gray-900">{new Date(item.dueDate).toLocaleDateString('nb-NO')}</p>
                </div>
              )}
              
              <div>
                <label className="text-sm text-gray-600">Amount (excl. VAT)</label>
                <p className="font-medium text-gray-900">{item.amountExclVat.toLocaleString('nb-NO')} {item.currency}</p>
              </div>
              
              <div>
                <label className="text-sm text-gray-600">VAT Amount</label>
                <p className="font-medium text-gray-900">{item.vatAmount.toLocaleString('nb-NO')} {item.currency}</p>
              </div>
              
              <div className="col-span-2">
                <label className="text-sm text-gray-600">Total Amount</label>
                <p className="text-2xl font-bold text-gray-900">{item.amount.toLocaleString('nb-NO')} {item.currency}</p>
              </div>
            </div>
          </motion.div>

          {/* AI Suggestion Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-lg shadow-md p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">AI Booking Suggestion</h2>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Confidence:</span>
                <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                  item.confidence >= 70 ? 'bg-green-100 text-green-800' :
                  item.confidence >= 50 ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {item.confidence}%
                </span>
              </div>
            </div>

            {item.aiReasoning && (
              <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-gray-700">
                  <strong>AI Reasoning:</strong> {item.aiReasoning}
                </p>
              </div>
            )}

            {/* Booking Lines */}
            {item.aiSuggestion?.lines && (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 px-3 text-sm font-semibold text-gray-700">Account</th>
                      <th className="text-left py-2 px-3 text-sm font-semibold text-gray-700">Description</th>
                      <th className="text-right py-2 px-3 text-sm font-semibold text-gray-700">Debit</th>
                      <th className="text-right py-2 px-3 text-sm font-semibold text-gray-700">Credit</th>
                      <th className="text-center py-2 px-3 text-sm font-semibold text-gray-700">VAT</th>
                    </tr>
                  </thead>
                  <tbody>
                    {item.aiSuggestion.lines.map((line: any, idx: number) => (
                      <tr key={idx} className="border-b border-gray-100">
                        <td className="py-2 px-3 font-mono text-sm text-gray-900">{line.account}</td>
                        <td className="py-2 px-3 text-sm text-gray-700">{line.description}</td>
                        <td className="py-2 px-3 text-right text-sm font-medium text-gray-900">
                          {line.debit > 0 ? line.debit.toLocaleString('nb-NO') : '-'}
                        </td>
                        <td className="py-2 px-3 text-right text-sm font-medium text-gray-900">
                          {line.credit > 0 ? line.credit.toLocaleString('nb-NO') : '-'}
                        </td>
                        <td className="py-2 px-3 text-center text-sm text-gray-600">
                          {line.vat_code || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </motion.div>

          {/* Notes */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-lg shadow-md p-6"
          >
            <h2 className="text-xl font-semibold mb-4 text-gray-900">Notes (Optional)</h2>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add any notes about this review..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={4}
            />
          </motion.div>
        </div>

        {/* Right: Actions */}
        <div className="lg:col-span-1">
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white rounded-lg shadow-md p-6 sticky top-6"
          >
            <h2 className="text-xl font-semibold mb-4 text-gray-900">Actions</h2>
            
            <div className="space-y-3">
              <button
                onClick={handleApprove}
                disabled={actionLoading}
                className="w-full px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 font-medium transition-colors"
              >
                {actionLoading ? 'Processing...' : '✓ Approve & Book'}
              </button>
              
              <button
                onClick={handleReject}
                disabled={actionLoading}
                className="w-full px-4 py-3 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:bg-gray-400 font-medium transition-colors"
              >
                {actionLoading ? 'Processing...' : '✎ Correct Manually'}
              </button>
              
              <button
                onClick={() => router.push('/')}
                disabled={actionLoading}
                className="w-full px-4 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 font-medium transition-colors"
              >
                Cancel
              </button>
            </div>

            {/* Status Info */}
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Status</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Priority:</span>
                  <span className={`font-medium ${
                    item.priority === 'high' ? 'text-red-600' :
                    item.priority === 'medium' ? 'text-yellow-600' :
                    'text-green-600'
                  }`}>
                    {item.priority.toUpperCase()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Category:</span>
                  <span className="font-medium text-gray-900">{item.issueCategory}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Created:</span>
                  <span className="font-medium text-gray-900">
                    {new Date(item.createdAt).toLocaleDateString('nb-NO')}
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};
