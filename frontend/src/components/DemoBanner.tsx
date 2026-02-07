'use client';

import { useState, useEffect } from 'react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function DemoBanner() {
  const [showBanner, setShowBanner] = useState(false);
  const [isDemoEnv, setIsDemoEnv] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    // Check if we're in demo environment
    const checkDemoEnvironment = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/demo/status');
        const data = await response.json();
        
        if (data.demo_environment_exists) {
          setIsDemoEnv(true);
          setShowBanner(true);
        }
      } catch (error) {
        // If endpoint doesn't exist or fails, assume not demo
        console.debug('Not in demo environment');
      }
    };

    checkDemoEnvironment();
  }, []);

  if (!isDemoEnv || !showBanner || dismissed) {
    return null;
  }

  return (
    <Alert className="rounded-none border-l-0 border-r-0 border-t-0 bg-yellow-50 border-yellow-200">
      <div className="flex items-center justify-between w-full">
        <div className="flex items-center space-x-3">
          <AlertTriangle className="h-5 w-5 text-yellow-600" />
          <div>
            <AlertDescription className="text-yellow-800 font-medium">
              🎭 Demo Environment - This is test data only. Changes will not affect production.
            </AlertDescription>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setDismissed(true)}
          className="text-yellow-600 hover:text-yellow-800"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </Alert>
  );
}
