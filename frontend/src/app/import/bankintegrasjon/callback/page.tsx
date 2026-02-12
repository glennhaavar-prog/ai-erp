"use client";

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [message, setMessage] = useState('Behandler tilkobling...');

  useEffect(() => {
    const handleCallback = async () => {
      if (!searchParams) {
        setStatus('error');
        setMessage('Ingen parametre mottatt fra Tink');
        return;
      }

      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const error = searchParams.get('error');

      // Check for OAuth errors
      if (error) {
        setStatus('error');
        setMessage(`Tilkobling avbrutt: ${error}`);
        return;
      }

      // Validate required parameters
      if (!code || !state) {
        setStatus('error');
        setMessage('Mangler nødvendige parametre fra Tink');
        return;
      }

      try {
        // Call backend to complete OAuth flow
        const response = await fetch('http://localhost:8000/api/tink/callback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            code,
            state,
          }),
        });

        if (response.ok) {
          const data = await response.json();
          setStatus('success');
          setMessage(data.message || 'Banken er nå tilkoblet!');
          
          // Redirect to main page after 2 seconds
          setTimeout(() => {
            router.push('/import/bankintegrasjon');
          }, 2000);
        } else {
          const errorData = await response.json();
          setStatus('error');
          setMessage(errorData.detail || 'Kunne ikke fullføre tilkobling');
        }
      } catch (error) {
        setStatus('error');
        setMessage('Nettverksfeil ved tilkobling til backend');
        console.error('Callback error:', error);
      }
    };

    handleCallback();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-6">
      <Card className="max-w-md w-full">
        <CardContent className="pt-6">
          <div className="text-center space-y-4">
            {status === 'processing' && (
              <>
                <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Kobler til Tink...
                </h2>
                <p className="text-gray-600 dark:text-gray-400">{message}</p>
              </>
            )}

            {status === 'success' && (
              <>
                <CheckCircle2 className="h-12 w-12 text-green-600 mx-auto" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Tilkobling vellykket!
                </h2>
                <Alert className="bg-green-50 border-green-200">
                  <AlertDescription className="text-green-800">{message}</AlertDescription>
                </Alert>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Omdirigerer til bankintegrasjon...
                </p>
              </>
            )}

            {status === 'error' && (
              <>
                <XCircle className="h-12 w-12 text-red-600 mx-auto" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Tilkobling feilet
                </h2>
                <Alert className="bg-red-50 border-red-200">
                  <AlertDescription className="text-red-800">{message}</AlertDescription>
                </Alert>
                <div className="flex gap-2 justify-center mt-4">
                  <Button
                    onClick={() => router.push('/import/bankintegrasjon')}
                    variant="outline"
                  >
                    Gå tilbake
                  </Button>
                  <Button
                    onClick={() => window.location.reload()}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    Prøv på nytt
                  </Button>
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function TinkCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-6">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Laster...
              </h2>
            </div>
          </CardContent>
        </Card>
      </div>
    }>
      <CallbackContent />
    </Suspense>
  );
}
