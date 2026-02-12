"use client";

import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface ConnectionStatusProps {
  isConnected: boolean;
  bankName?: string;
  lastSyncTime?: string;
  loading?: boolean;
  onDisconnect: () => void;
}

export function ConnectionStatus({
  isConnected,
  bankName,
  lastSyncTime,
  loading,
  onDisconnect,
}: ConnectionStatusProps) {
  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {isConnected ? (
            <>
              <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
              <span>Tilkoblet</span>
            </>
          ) : (
            <>
              <XCircle className="h-5 w-5 text-gray-400" />
              <span>Ikke tilkoblet</span>
            </>
          )}
        </CardTitle>
        <CardDescription>
          {isConnected
            ? 'Din bank er tilkoblet via Tink'
            : 'Koble til banken din for automatisk import'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isConnected ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Bank</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {bankName || 'Ukjent bank'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Sist synkronisert</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {lastSyncTime
                    ? new Date(lastSyncTime).toLocaleString('nb-NO', {
                        dateStyle: 'short',
                        timeStyle: 'short',
                      })
                    : 'Aldri'}
                </p>
              </div>
            </div>
            <Button
              variant="outline"
              onClick={onDisconnect}
              className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              Koble fra
            </Button>
          </div>
        ) : (
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Du må koble til banken din før du kan synkronisere transaksjoner automatisk.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
