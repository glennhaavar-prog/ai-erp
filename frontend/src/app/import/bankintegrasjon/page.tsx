"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ConnectionStatus } from '@/components/Tink/ConnectionStatus';
import { AccountsList } from '@/components/Tink/AccountsList';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Download, CheckCircle2, ArrowRight } from 'lucide-react';

interface TinkStatus {
  connected: boolean;
  bank_name?: string;
  last_sync?: string;
  credential_id?: string;
}

interface BankAccount {
  id: string;
  bank_name: string;
  account_number: string;
  balance: number;
  account_type: string;
}

interface Transaction {
  id: string;
  date: string;
  description: string;
  amount: number;
  account_number: string;
}

export default function BankintegrasjonPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<TinkStatus | null>(null);
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Date range for sync (default: last 90 days)
  const [fromDate, setFromDate] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() - 90);
    return date.toISOString().split('T')[0];
  });
  const [toDate, setToDate] = useState(() => new Date().toISOString().split('T')[0]);

  const fetchStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/tink/status');
      if (response.ok) {
        const data = await response.json();
        setStatus(data);

        // If connected, fetch accounts
        if (data.connected) {
          fetchAccounts();
          fetchRecentTransactions();
        }
      }
    } catch (error) {
      console.error('Failed to fetch Tink status:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAccounts = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/tink/accounts');
      if (response.ok) {
        const data = await response.json();
        setAccounts(data.accounts || []);
      }
    } catch (error) {
      console.error('Failed to fetch accounts:', error);
    }
  };

  const fetchRecentTransactions = async () => {
    try {
      // Fetch recent transactions from the database
      // This would typically be a separate endpoint
      const response = await fetch('http://localhost:8000/api/transactions?limit=10');
      if (response.ok) {
        const data = await response.json();
        setRecentTransactions(data.transactions || []);
      }
    } catch (error) {
      console.error('Failed to fetch transactions:', error);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleConnect = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/tink/authorize');
      if (response.ok) {
        const data = await response.json();
        // Redirect to Tink OAuth page
        window.location.href = data.authorization_url;
      } else {
        setMessage({ type: 'error', text: 'Kunne ikke starte tilkobling til Tink' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Feil ved tilkobling til Tink' });
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('Er du sikker på at du vil koble fra Tink?')) return;

    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/tink/disconnect', {
        method: 'DELETE',
      });
      if (response.ok) {
        setStatus({ connected: false });
        setAccounts([]);
        setRecentTransactions([]);
        setMessage({ type: 'success', text: 'Koblet fra Tink' });
      } else {
        setMessage({ type: 'error', text: 'Kunne ikke koble fra Tink' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Feil ved frakobling fra Tink' });
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    try {
      setSyncing(true);
      setMessage(null);
      
      const response = await fetch('http://localhost:8000/api/tink/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from_date: fromDate,
          to_date: toDate,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setMessage({
          type: 'success',
          text: `${data.transactions_count || 0} transaksjoner importert`,
        });
        fetchRecentTransactions();
        
        // Update last sync time
        if (status) {
          setStatus({ ...status, last_sync: new Date().toISOString() });
        }
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'Kunne ikke synkronisere transaksjoner' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Feil ved synkronisering' });
    } finally {
      setSyncing(false);
    }
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('nb-NO', {
      style: 'currency',
      currency: 'NOK',
    }).format(amount);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Bankintegrasjon (Tink)
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Koble til DNB via Tink for automatisk import av transaksjoner
        </p>
      </div>

      {/* Messages */}
      {message && (
        <Alert className={message.type === 'success' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}>
          <AlertDescription className={message.type === 'success' ? 'text-green-800' : 'text-red-800'}>
            {message.text}
          </AlertDescription>
        </Alert>
      )}

      {/* Connection Status */}
      <ConnectionStatus
        isConnected={status?.connected || false}
        bankName={status?.bank_name}
        lastSyncTime={status?.last_sync}
        loading={loading}
        onDisconnect={handleDisconnect}
      />

      {/* Connect Button (if not connected) */}
      {!loading && !status?.connected && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <div className="text-center space-y-4">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                Koble til DNB via Tink
              </h3>
              <p className="text-gray-600 dark:text-gray-400 max-w-md">
                Med Tink kan du automatisk importere banktransaksjoner direkte fra DNB.
                Dette sparer tid og reduserer feil.
              </p>
              <Button
                onClick={handleConnect}
                size="lg"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Kobler til...
                  </>
                ) : (
                  <>
                    Koble til DNB via Tink
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sync Section (if connected) */}
      {status?.connected && (
        <Card>
          <CardHeader>
            <CardTitle>Synkroniser transaksjoner</CardTitle>
            <CardDescription>
              Hent transaksjoner fra banken din for en valgt periode
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Fra dato
                  </label>
                  <input
                    type="date"
                    value={fromDate}
                    onChange={(e) => setFromDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Til dato
                  </label>
                  <input
                    type="date"
                    value={toDate}
                    onChange={(e) => setToDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                  />
                </div>
              </div>
              <Button
                onClick={handleSync}
                disabled={syncing}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {syncing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Synkroniserer...
                  </>
                ) : (
                  <>
                    <Download className="mr-2 h-4 w-4" />
                    Hent transaksjoner
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Accounts List (if connected) */}
      {status?.connected && accounts.length > 0 && (
        <AccountsList
          accounts={accounts}
          onAccountClick={(accountId) => {
            console.log('Account clicked:', accountId);
            // Could navigate to account details page
          }}
        />
      )}

      {/* Recent Transactions Preview */}
      {status?.connected && recentTransactions.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Siste transaksjoner</CardTitle>
                <CardDescription>De 10 siste importerte transaksjonene</CardDescription>
              </div>
              <Button
                variant="outline"
                onClick={() => router.push('/bank-reconciliation')}
              >
                Se alle transaksjoner
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-900">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Dato
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Beskrivelse
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Beløp
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Konto
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {recentTransactions.map((transaction) => (
                    <tr key={transaction.id} className="hover:bg-gray-50 dark:hover:bg-gray-900/50">
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                        {new Date(transaction.date).toLocaleDateString('nb-NO')}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">
                        {transaction.description}
                      </td>
                      <td className={`px-4 py-3 text-sm text-right font-mono font-medium ${
                        transaction.amount >= 0
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}>
                        {formatAmount(transaction.amount)}
                      </td>
                      <td className="px-4 py-3 text-sm font-mono text-gray-600 dark:text-gray-400">
                        {transaction.account_number}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Info Box */}
      <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <CardContent className="pt-6">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            <strong>Hvordan det fungerer:</strong> Tink er en sikker tjeneste som lar deg koble til
            banken din og automatisk importere transaksjoner. Du godkjenner tilkoblingen via BankID,
            og deretter kan du hente transaksjoner direkte inn i Kontali ERP.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
