'use client';

import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { Play, CheckCircle2, XCircle, Loader2 } from 'lucide-react';

interface TaskStatus {
  task_id: string;
  status: string;
  progress?: number;
  message?: string;
  stats?: {
    vendors_created: number;
    vendor_invoices_created: number;
    customer_invoices_created: number;
    bank_transactions_created: number;
  };
  error?: string;
}

export default function DemoTestButton() {
  const [isOpen, setIsOpen] = useState(false);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [isDemoEnv, setIsDemoEnv] = useState(false);

  useEffect(() => {
    // Check if we're in demo environment
    const checkDemoEnvironment = async () => {
      try {
        const response = await fetch('http://localhost:8000/demo/status');
        const data = await response.json();
        setIsDemoEnv(data.demo_environment_exists);
      } catch (error) {
        console.debug('Not in demo environment');
      }
    };

    checkDemoEnvironment();
  }, []);

  useEffect(() => {
    // Poll for task status if a task is running
    if (taskStatus && (taskStatus.status === 'running' || taskStatus.status === 'started')) {
      const interval = setInterval(() => {
        pollTaskStatus(taskStatus.task_id);
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [taskStatus]);

  const pollTaskStatus = async (taskId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/demo/task/${taskId}`);
      const data = await response.json();
      setTaskStatus(data);
    } catch (error) {
      console.error('Error polling task:', error);
    }
  };

  const handleRunTest = async () => {
    try {
      // Default configuration optimized for Skattefunn demo
      const config = {
        invoices_per_client: 20,
        customer_invoices_per_client: 10,
        transactions_per_client: 30,
        high_confidence_ratio: 0.7,
        include_duplicates: true,
        include_edge_cases: true,
      };

      const response = await fetch('http://localhost:8000/demo/run-test', {
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
      toast.error('Feil ved oppstart av testdata-generering');
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    // Reset after a delay to allow animation
    setTimeout(() => {
      if (taskStatus?.status === 'completed' || taskStatus?.status === 'failed') {
        setTaskStatus(null);
      }
    }, 300);
  };

  if (!isDemoEnv) {
    return null;
  }

  return (
    <>
      <Button
        onClick={() => setIsOpen(true)}
        className="bg-purple-600 hover:bg-purple-700 text-white font-semibold px-6 py-3 rounded-lg shadow-lg flex items-center space-x-2 transition-all hover:scale-105"
        size="lg"
      >
        <Play className="h-5 w-5" />
        <span>Kjør Test</span>
      </Button>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Generer testdata</DialogTitle>
            <DialogDescription>
              Dette vil generere realistiske testdata for demo-miljøet.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {!taskStatus ? (
              <div className="space-y-3">
                <p className="text-sm text-gray-600">
                  Dette vil generere:
                </p>
                <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                  <li>~20 leverandørfakturaer per klient</li>
                  <li>~10 kundefakturaer per klient</li>
                  <li>~30 banktransaksjoner per klient</li>
                  <li>Variert kompleksitet (høy/lav tillit)</li>
                  <li>Duplikater og edge cases</li>
                </ul>
                <p className="text-sm text-amber-600 font-medium mt-4">
                  ⚠️ Dette vil legge til nye testdata i systemet.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Status Indicator */}
                <div className="flex items-center space-x-3">
                  {taskStatus.status === 'running' || taskStatus.status === 'started' ? (
                    <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
                  ) : taskStatus.status === 'completed' ? (
                    <CheckCircle2 className="h-6 w-6 text-green-500" />
                  ) : taskStatus.status === 'failed' ? (
                    <XCircle className="h-6 w-6 text-red-500" />
                  ) : null}
                  <span className="font-medium">{taskStatus.message}</span>
                </div>

                {/* Progress Bar */}
                {taskStatus.progress !== undefined && (
                  <div>
                    <Progress value={taskStatus.progress} className="h-2" />
                    <p className="text-xs text-gray-500 mt-1 text-right">
                      {taskStatus.progress}%
                    </p>
                  </div>
                )}

                {/* Statistics */}
                {taskStatus.stats && (
                  <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                    <p className="text-sm font-semibold text-gray-700">Generert:</p>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-gray-600">Leverandører:</span>
                        <span className="font-semibold ml-2">{taskStatus.stats.vendors_created}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Fakturaer:</span>
                        <span className="font-semibold ml-2">{taskStatus.stats.vendor_invoices_created}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Kundefakturaer:</span>
                        <span className="font-semibold ml-2">{taskStatus.stats.customer_invoices_created}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Transaksjoner:</span>
                        <span className="font-semibold ml-2">{taskStatus.stats.bank_transactions_created}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Error Message */}
                {taskStatus.error && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p className="text-sm text-red-600">{taskStatus.error}</p>
                  </div>
                )}
              </div>
            )}
          </div>

          <DialogFooter>
            {!taskStatus ? (
              <>
                <Button variant="outline" onClick={() => setIsOpen(false)}>
                  Avbryt
                </Button>
                <Button onClick={handleRunTest}>
                  Fortsett
                </Button>
              </>
            ) : (
              <>
                {(taskStatus.status === 'completed' || taskStatus.status === 'failed') && (
                  <Button onClick={handleClose} className="w-full">
                    Lukk
                  </Button>
                )}
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
