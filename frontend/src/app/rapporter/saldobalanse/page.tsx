"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

interface Balance {
  account_number: string;
  account_name: string;
  total_debit: number;
  total_credit: number;
  balance: number;
}

interface SaldobalanseResponse {
  client_id: string;
  from_date: string | null;
  to_date: string | null;
  account_from: string | null;
  account_to: string | null;
  balances: Balance[];
  total_debit: number;
  total_credit: number;
  is_balanced: boolean;
}

export default function SaldobalansePage() {
  const router = useRouter();
  const [data, setData] = useState<SaldobalanseResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [clientId] = useState("8f6d593d-cb4e-42eb-a51c-a7b1dab660dc"); // Demo client
  const [fromDate, setFromDate] = useState<string>("");
  const [toDate, setToDate] = useState<string>("");
  const [accountFrom, setAccountFrom] = useState<string>("");
  const [accountTo, setAccountTo] = useState<string>("");

  const fetchSaldobalanse = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        client_id: clientId,
      });

      if (fromDate) params.append("from_date", fromDate);
      if (toDate) params.append("to_date", toDate);
      if (accountFrom) params.append("account_from", accountFrom);
      if (accountTo) params.append("account_to", accountTo);

      const response = await fetch(`http://localhost:8000/api/reports/saldobalanse?${params}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSaldobalanse();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat("nb-NO", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  if (loading && !data) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
          <div className="space-y-2">
            {[...Array(10)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-200 dark:bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-800 dark:text-red-200">Feil ved henting av data: {error}</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Saldobalanse
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Kontobalanse per {toDate || "i dag"}
          </p>
        </div>
        
        {data.is_balanced && (
          <div className="flex items-center gap-2 px-4 py-2 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <span className="text-green-600 dark:text-green-400 text-sm font-medium">
              ✓ Balanse OK
            </span>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Fra-dato
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
              Til-dato
            </label>
            <input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Konto fra
            </label>
            <input
              type="text"
              value={accountFrom}
              onChange={(e) => setAccountFrom(e.target.value)}
              placeholder="f.eks. 3000"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Konto til
            </label>
            <input
              type="text"
              value={accountTo}
              onChange={(e) => setAccountTo(e.target.value)}
              placeholder="f.eks. 8999"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
            />
          </div>
        </div>
        <div className="mt-4 flex gap-2">
          <button
            onClick={fetchSaldobalanse}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-md font-medium"
          >
            {loading ? "Laster..." : "Oppdater"}
          </button>
          <button
            onClick={() => {
              setFromDate("");
              setToDate("");
              setAccountFrom("");
              setAccountTo("");
            }}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md font-medium"
          >
            Nullstill
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Konto
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Kontonavn
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Debet
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Kredit
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Saldo
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {data.balances.map((balance, idx) => (
                <tr
                  key={balance.account_number}
                  className="hover:bg-gray-50 dark:hover:bg-gray-900/50"
                >
                  <td className="px-4 py-3 text-sm font-mono text-blue-600 dark:text-blue-400 hover:underline cursor-pointer">
                    <button
                      onClick={() => router.push(`/rapporter/hovedbok?account_number=${balance.account_number}`)}
                      className="hover:underline"
                    >
                      {balance.account_number}
                    </button>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">
                    {balance.account_name}
                  </td>
                  <td className="px-4 py-3 text-sm text-right font-mono text-gray-900 dark:text-white">
                    {formatAmount(balance.total_debit)}
                  </td>
                  <td className="px-4 py-3 text-sm text-right font-mono text-gray-900 dark:text-white">
                    {formatAmount(balance.total_credit)}
                  </td>
                  <td
                    className={`px-4 py-3 text-sm text-right font-mono font-medium ${
                      balance.balance >= 0
                        ? "text-gray-900 dark:text-white"
                        : "text-red-600 dark:text-red-400"
                    }`}
                  >
                    {formatAmount(balance.balance)}
                  </td>
                </tr>
              ))}
              {/* Total row */}
              <tr className="bg-gray-50 dark:bg-gray-900 font-bold">
                <td colSpan={2} className="px-4 py-3 text-sm text-gray-900 dark:text-white">
                  SUM
                </td>
                <td className="px-4 py-3 text-sm text-right font-mono text-gray-900 dark:text-white">
                  {formatAmount(data.total_debit)}
                </td>
                <td className="px-4 py-3 text-sm text-right font-mono text-gray-900 dark:text-white">
                  {formatAmount(data.total_credit)}
                </td>
                <td className="px-4 py-3 text-sm text-right font-mono text-gray-900 dark:text-white">
                  {formatAmount(data.total_debit - data.total_credit)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Info box */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <p className="text-sm text-blue-800 dark:text-blue-200">
          <strong>Saldobalanse:</strong> Viser saldo per konto for valgt periode. 
          Total debet skal alltid være lik total kredit. 
          Klikk på en konto for å se hovedbok.
        </p>
      </div>
    </div>
  );
}
