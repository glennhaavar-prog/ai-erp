'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  AlertCircle, 
  CheckCircle2, 
  RefreshCw, 
  Play, 
  Trash2,
  Database,
  FileText,
  CreditCard,
  BookOpen,
  Users,
} from 'lucide-react';

interface DemoStatus {
  demo_environment_exists: boolean;
  tenant?: {
    id: string;
    name: string;
    org_number: string;
  };
  stats?: {
    clients: number;
    vendor_invoices: number;
    customer_invoices: number;
    total_invoices: number;
    bank_transactions: number;
    general_ledger_entries: number;
    chart_of_accounts: number;
  };
  last_reset?: string;
  message?: string;
}

interface TaskStatus {
  task_id: string;
  status: string;
  progress?: number;
  message?: string;
  stats?: any;
  error?: string;
}

export default function DemoControlPage() {
  const [status, setStatus] = useState<DemoStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null);
  
  // Configuration
  const [config, setConfig] = useState({
    invoices_per_client: 20,
    customer_invoices_per_client: 10,
    transactions_per_client: 30,
    high_confidence_ratio: 0.7,
    include_duplicates: true,
    include_edge_cases: true,
  });

  useEffect(() => {
    fetchStatus();
  }, []);

  useEffect(() => {
    // Poll for task status if a task is running
    if (taskStatus && (taskStatus.status === 'running' || taskStatus.status === 'started')) {
      const interval = setInterval(() => {
        pollTaskStatus(taskStatus.task_id);
      }, 2000);
      setPollInterval(interval);
      return () => clearInterval(interval);
    } else if (pollInterval) {
      clearInterval(pollInterval);
      setPollInterval(null);
    }
  }, [taskStatus]);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/demo/status');
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      console.error('Error fetching status:', error);
    } finally {
      setLoading(false);
    }
  };

  const pollTaskStatus = async (taskId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/demo/task/${taskId}`);
      const data = await response.json();
      setTaskStatus(data);

      // Refresh main status when task completes
      if (data.status === 'completed' || data.status === 'failed') {
        await fetchStatus();
      }
    } catch (error) {
      console.error('Error polling task:', error);
    }
  };

  const handleRunTest = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/demo/run-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error('Failed to start test data generation');
      }

      const data = await response.json();
      setTaskStatus(data);
    } catch (error) {
      console.error('Error running test:', error);
      alert('Failed to start test data generation');
    }
  };

  const handleReset = async () => {
    if (!confirm('⚠️ This will delete ALL demo data (invoices, transactions, GL entries). Are you sure?')) {
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/api/demo/reset', {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to reset demo environment');
      }

      const data = await response.json();
      alert(`✅ Demo environment reset successfully!\n\nDeleted:\n- ${data.deleted_counts.vendor_invoices} vendor invoices\n- ${data.deleted_counts.customer_invoices} customer invoices\n- ${data.deleted_counts.bank_transactions} bank transactions\n- ${data.deleted_counts.general_ledger_entries} GL entries`);
      
      await fetchStatus();
      setTaskStatus(null);
    } catch (error) {
      console.error('Error resetting:', error);
      alert('Failed to reset demo environment');
    }
  };

  if (loading) {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      </div>
    );
  }

  if (!status?.demo_environment_exists) {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>No Demo Environment Found</AlertTitle>
          <AlertDescription>
            {status?.message || 'Please run the demo environment setup script first.'}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">🎭 Demo Environment Control</h1>
        <p className="text-gray-600 mt-2">
          Manage demo data and generate test scenarios
        </p>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tenant</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{status.tenant?.name}</div>
            <p className="text-xs text-muted-foreground">
              Org: {status.tenant?.org_number}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Clients</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{status.stats?.clients}</div>
            <p className="text-xs text-muted-foreground">
              {status.stats?.chart_of_accounts} accounts total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Last Reset</CardTitle>
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {status.last_reset
                ? new Date(status.last_reset).toLocaleDateString()
                : 'Never'}
            </div>
            <p className="text-xs text-muted-foreground">
              {status.last_reset
                ? new Date(status.last_reset).toLocaleTimeString()
                : 'No resets yet'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Data Statistics */}
      <Card>
        <CardHeader>
          <CardTitle>Current Data</CardTitle>
          <CardDescription>Statistics for demo environment</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="flex items-center space-x-3">
              <FileText className="h-8 w-8 text-blue-500" />
              <div>
                <p className="text-sm text-gray-600">Vendor Invoices</p>
                <p className="text-2xl font-bold">{status.stats?.vendor_invoices || 0}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <FileText className="h-8 w-8 text-green-500" />
              <div>
                <p className="text-sm text-gray-600">Customer Invoices</p>
                <p className="text-2xl font-bold">{status.stats?.customer_invoices || 0}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <CreditCard className="h-8 w-8 text-purple-500" />
              <div>
                <p className="text-sm text-gray-600">Bank Transactions</p>
                <p className="text-2xl font-bold">{status.stats?.bank_transactions || 0}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <BookOpen className="h-8 w-8 text-orange-500" />
              <div>
                <p className="text-sm text-gray-600">GL Entries</p>
                <p className="text-2xl font-bold">{status.stats?.general_ledger_entries || 0}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Test Data Generator */}
      <Card>
        <CardHeader>
          <CardTitle>Generate Test Data</CardTitle>
          <CardDescription>
            Create realistic test data with edge cases for AI testing
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label>Vendor Invoices per Client</Label>
              <Input
                type="number"
                value={config.invoices_per_client}
                onChange={(e) =>
                  setConfig({ ...config, invoices_per_client: parseInt(e.target.value) })
                }
              />
            </div>
            <div>
              <Label>Customer Invoices per Client</Label>
              <Input
                type="number"
                value={config.customer_invoices_per_client}
                onChange={(e) =>
                  setConfig({ ...config, customer_invoices_per_client: parseInt(e.target.value) })
                }
              />
            </div>
            <div>
              <Label>Bank Transactions per Client</Label>
              <Input
                type="number"
                value={config.transactions_per_client}
                onChange={(e) =>
                  setConfig({ ...config, transactions_per_client: parseInt(e.target.value) })
                }
              />
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="duplicates"
              checked={config.include_duplicates}
              onChange={(e) =>
                setConfig({ ...config, include_duplicates: e.target.checked })
              }
            />
            <Label htmlFor="duplicates">Include duplicate invoices</Label>
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="edge-cases"
              checked={config.include_edge_cases}
              onChange={(e) =>
                setConfig({ ...config, include_edge_cases: e.target.checked })
              }
            />
            <Label htmlFor="edge-cases">Include edge cases (low confidence)</Label>
          </div>

          {taskStatus && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">{taskStatus.message}</span>
                <span className="text-sm text-gray-600">{taskStatus.status}</span>
              </div>
              {taskStatus.progress !== undefined && (
                <Progress value={taskStatus.progress} className="mt-2" />
              )}
              {taskStatus.stats && (
                <div className="mt-3 text-sm text-gray-600">
                  <p>✅ Vendors: {taskStatus.stats.vendors_created}</p>
                  <p>✅ Vendor Invoices: {taskStatus.stats.vendor_invoices_created}</p>
                  <p>✅ Customer Invoices: {taskStatus.stats.customer_invoices_created}</p>
                  <p>✅ Bank Transactions: {taskStatus.stats.bank_transactions_created}</p>
                </div>
              )}
              {taskStatus.error && (
                <Alert variant="destructive" className="mt-3">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{taskStatus.error}</AlertDescription>
                </Alert>
              )}
            </div>
          )}

          <div className="flex space-x-3">
            <Button
              onClick={handleRunTest}
              disabled={taskStatus?.status === 'running'}
              className="flex items-center space-x-2"
            >
              <Play className="h-4 w-4" />
              <span>Run Test</span>
            </Button>

            <Button variant="outline" onClick={fetchStatus}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh Status
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Reset Section */}
      <Card className="border-red-200">
        <CardHeader>
          <CardTitle className="text-red-600">Danger Zone</CardTitle>
          <CardDescription>
            Reset will delete all demo data but preserve clients and accounts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            variant="destructive"
            onClick={handleReset}
            className="flex items-center space-x-2"
          >
            <Trash2 className="h-4 w-4" />
            <span>Reset Demo Environment</span>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
