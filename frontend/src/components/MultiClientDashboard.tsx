"use client";

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface Task {
  id: string;
  type: string;
  category: string;
  client_id: string;
  client_name: string;
  description: string;
  confidence: number;
  created_at: string;
  priority: 'high' | 'medium' | 'low';
  data: {
    invoice_id?: string;
    vendor_name?: string;
    amount?: number;
    invoice_number?: string;
  };
}

interface DashboardData {
  tenant_id: string;
  total_clients: number;
  clients: Array<{ id: string; name: string }>;
  tasks: Task[];
  summary: {
    total_tasks: number;
    by_category: {
      invoicing: number;
      bank: number;
      reporting: number;
    };
  };
  timestamp: string;
}

type CategoryFilter = 'all' | 'invoicing' | 'bank' | 'reporting';

export function MultiClientDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<CategoryFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Mock tenant ID for now - in real app this comes from auth context
  const mockTenantId = '00000000-0000-0000-0000-000000000001';

  useEffect(() => {
    fetchTasks();
  }, [selectedCategory]);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const url = `http://localhost:8000/api/dashboard/multi-client/tasks?tenant_id=${mockTenantId}${selectedCategory !== 'all' ? `&category=${selectedCategory}` : ''}`;
      const response = await fetch(url);
      if (response.ok) {
        const result = await response.json();
        setData(result);
      }
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredTasks = data?.tasks.filter(task =>
    task.client_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    task.description.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'invoicing': return '📄';
      case 'bank': return '🏦';
      case 'reporting': return '📊';
      default: return '📋';
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Multi-Client Dashboard
          </h1>
          <p className="text-gray-600">
            {data ? `${data.total_clients} active clients • ${data.summary.total_tasks} tasks need attention` : 'Loading...'}
          </p>
        </div>
        
        {/* Client Switcher */}
        {data && data.clients.length > 0 && (
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-600 font-medium">Quick Jump:</label>
            <select
              onChange={(e) => {
                if (e.target.value) {
                  window.location.href = `/clients/${e.target.value}`;
                }
              }}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
              defaultValue=""
            >
              <option value="">Select a client...</option>
              {data.clients.map(client => (
                <option key={client.id} value={client.id}>
                  {client.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Category Filter Tabs */}
      <div className="mb-6 flex space-x-2 border-b border-gray-200">
        {(['all', 'invoicing', 'bank', 'reporting'] as CategoryFilter[]).map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              selectedCategory === cat
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            {cat === 'all' ? '📋 All Tasks' : `${getCategoryIcon(cat)} ${cat.charAt(0).toUpperCase() + cat.slice(1)}`}
            {data && cat !== 'all' && (
              <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-gray-100">
                {data.summary.by_category[cat as keyof typeof data.summary.by_category]}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search tasks or clients..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Tasks List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading tasks...</p>
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="text-center py-12 bg-green-50 rounded-lg border border-green-200">
          <div className="text-4xl mb-2">✅</div>
          <h3 className="text-lg font-semibold text-green-900 mb-1">All Clear!</h3>
          <p className="text-green-700">No tasks need attention right now.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredTasks.map((task) => (
            <motion.div
              key={task.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`border rounded-lg p-4 hover:shadow-md transition-shadow ${getPriorityColor(task.priority)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <span className="text-2xl">{getCategoryIcon(task.category)}</span>
                    <div>
                      <h3 className="font-semibold text-gray-900">{task.client_name}</h3>
                      <p className="text-sm text-gray-600">{task.description}</p>
                    </div>
                  </div>
                  
                  {task.data.vendor_name && (
                    <div className="ml-11 mt-2 text-sm text-gray-700">
                      <p><strong>Vendor:</strong> {task.data.vendor_name}</p>
                      {task.data.invoice_number && <p><strong>Invoice #:</strong> {task.data.invoice_number}</p>}
                      {task.data.amount && <p><strong>Amount:</strong> {task.data.amount.toFixed(2)} NOK</p>}
                    </div>
                  )}
                </div>
                
                <div className="text-right">
                  <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${getPriorityColor(task.priority)}`}>
                    {task.priority.toUpperCase()}
                  </span>
                  <p className="text-xs text-gray-500 mt-2">
                    {new Date(task.created_at).toLocaleString('nb-NO')}
                  </p>
                  <div className="mt-2">
                    <span className="text-xs text-gray-600">AI Confidence:</span>
                    <div className="w-20 h-2 bg-gray-200 rounded-full mt-1">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${task.confidence}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-600">{task.confidence}%</span>
                  </div>
                </div>
              </div>
              
              <div className="mt-3 flex space-x-2">
                <button
                  onClick={() => window.location.href = `/review-queue/${task.id}`}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm font-medium"
                >
                  Review Now
                </button>
                <button
                  onClick={() => window.location.href = `/clients/${task.client_id}`}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm font-medium"
                >
                  View Client
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
