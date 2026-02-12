"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Building2 } from 'lucide-react';

interface BankAccount {
  id: string;
  bank_name: string;
  account_number: string;
  balance: number;
  account_type: string;
}

interface AccountsListProps {
  accounts: BankAccount[];
  onAccountClick?: (accountId: string) => void;
}

export function AccountsList({ accounts, onAccountClick }: AccountsListProps) {
  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('nb-NO', {
      style: 'currency',
      currency: 'NOK',
    }).format(amount);
  };

  if (accounts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Bankkontoer</CardTitle>
          <CardDescription>Ingen bankkontoer funnet</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Tilkoblede bankkontoer</CardTitle>
        <CardDescription>{accounts.length} konto(er) funnet</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Bank
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Kontonummer
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Saldo
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Type
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {accounts.map((account) => (
                <tr
                  key={account.id}
                  onClick={() => onAccountClick?.(account.id)}
                  className={`hover:bg-gray-50 dark:hover:bg-gray-900/50 ${
                    onAccountClick ? 'cursor-pointer' : ''
                  }`}
                >
                  <td className="px-4 py-3 text-sm">
                    <div className="flex items-center gap-2">
                      <Building2 className="h-4 w-4 text-gray-400" />
                      <span className="font-medium text-gray-900 dark:text-white">
                        {account.bank_name}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm font-mono text-gray-600 dark:text-gray-400">
                    {account.account_number}
                  </td>
                  <td className="px-4 py-3 text-sm text-right font-mono font-medium text-gray-900 dark:text-white">
                    {formatAmount(account.balance)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                    {account.account_type}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
