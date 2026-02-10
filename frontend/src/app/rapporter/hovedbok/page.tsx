"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import DateQuickPicker from "@/components/DateQuickPicker";

interface HovedbokEntry {
  entry_id: string;
  voucher_number: string;
  accounting_date: string;
  entry_description: string;
  account_number: string;
  line_description: string;
  debit_amount: number;
  credit_amount: number;
  vat_code: string | null;
  vat_amount: number | null;
}

interface HovedbokResponse {
  client_id: string;
  account_number: string | null;
  from_date: string | null;
  to_date: string | null;
  opening_balance: number | null;
  closing_balance: number | null;
  entries: HovedbokEntry[];
  count: number;
  limit: number;
  offset: number;
}

function HovedbokPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [data, setData] = useState<HovedbokResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [clientId] = useState("8f6d593d-cb4e-42eb-a51c-a7b1dab660dc");
  const [accountNumber, setAccountNumber] = useState<string>(searchParams?.get("account_number") || "");
  const [accountFrom, setAccountFrom] = useState<string>("");
  const [accountTo, setAccountTo] = useState<string>("");
  const [fromDate, setFromDate] = useState<string>("");
  const [toDate, setToDate] = useState<string>("");

  const fetchHovedbok = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({ client_id: clientId });
      // Support both single account (backward compat) and range
      if (accountNumber) {
        params.append("account_number", accountNumber);
      } else {
        if (accountFrom) params.append("account_from", accountFrom);
        if (accountTo) params.append("account_to", accountTo);
      }
      if (fromDate) params.append("from_date", fromDate);
      if (toDate) params.append("to_date", toDate);
      params.append("limit", "100");

      const response = await fetch(`http://localhost:8000/api/reports/hovedbok?${params}`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHovedbok();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleQuickDateChange = (from: string, to: string) => {
    setFromDate(from);
    setToDate(to);
    // Auto-fetch after setting dates
    setTimeout(() => {
      const params = new URLSearchParams({ client_id: clientId });
      if (accountNumber) {
        params.append("account_number", accountNumber);
      } else {
        if (accountFrom) params.append("account_from", accountFrom);
        if (accountTo) params.append("account_to", accountTo);
      }
      if (from) params.append("from_date", from);
      if (to) params.append("to_date", to);
      params.append("limit", "100");
      
      setLoading(true);
      fetch(`http://localhost:8000/api/reports/hovedbok?${params}`)
        .then((response) => response.json())
        .then((result) => setData(result))
        .catch((err) => setError(err instanceof Error ? err.message : "Unknown error"))
        .finally(() => setLoading(false));
    }, 50);
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat("nb-NO", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("nb-NO");
  };

  if (loading && !data) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-800 dark:text-red-200">Feil: {error}</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Hovedbok
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {data.account_number
            ? `Konto ${data.account_number} - ${data.count} posteringer`
            : `Alle kontoer - ${data.count} posteringer`}
        </p>
      </div>

      {/* Filters - FIX: Kontorange (fra/til) */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Fra kontonummer
            </label>
            <input
              type="text"
              value={accountFrom}
              onChange={(e) => {
                setAccountFrom(e.target.value);
                setAccountNumber(""); // Clear single account if using range
              }}
              placeholder="f.eks. 6000"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Til kontonummer
            </label>
            <input
              type="text"
              value={accountTo}
              onChange={(e) => {
                setAccountTo(e.target.value);
                setAccountNumber(""); // Clear single account if using range
              }}
              placeholder="f.eks. 6999"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
            />
          </div>
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
        </div>

        {/* Quick date picker */}
        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Hurtigvalg
          </label>
          <DateQuickPicker onDateChange={handleQuickDateChange} />
        </div>

        <div className="mt-4 flex gap-2">
          <button
            onClick={fetchHovedbok}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-md font-medium"
          >
            {loading ? "Laster..." : "Oppdater"}
          </button>
          <button
            onClick={() => {
              setAccountNumber("");
              setAccountFrom("");
              setAccountTo("");
              setFromDate("");
              setToDate("");
            }}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md font-medium"
          >
            Nullstill
          </button>
        </div>
      </div>

      {/* Saldo summary (hvis spesifikk konto) */}
      {data.account_number && (data.opening_balance !== null || data.closing_balance !== null) && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="grid grid-cols-3 gap-4">
            {data.opening_balance !== null && (
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Inngående saldo</div>
                <div className="text-xl font-mono font-bold text-gray-900 dark:text-white">
                  {formatAmount(data.opening_balance)}
                </div>
              </div>
            )}
            <div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Bevegelser</div>
              <div className="text-xl font-mono font-bold text-blue-600 dark:text-blue-400">
                {data.entries.length > 0
                  ? formatAmount(
                      data.entries.reduce((sum, e) => sum + e.debit_amount - e.credit_amount, 0)
                    )
                  : "0,00"}
              </div>
            </div>
            {data.closing_balance !== null && (
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Utgående saldo</div>
                <div className="text-xl font-mono font-bold text-gray-900 dark:text-white">
                  {formatAmount(data.closing_balance)}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Dato
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Bilag
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Konto
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Beskrivelse
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Debet
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Kredit
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  MVA
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {data.entries.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                    Ingen posteringer funnet for valgt periode
                  </td>
                </tr>
              ) : (
                data.entries.map((entry, idx) => (
                  <tr
                    key={`${entry.entry_id}-${idx}`}
                    className="hover:bg-gray-50 dark:hover:bg-gray-900/50 cursor-pointer"
                  >
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-white whitespace-nowrap">
                      {formatDate(entry.accounting_date)}
                    </td>
                    <td className="px-4 py-3">
                      {/* TASK 11 FIX: Større, tydeligere bilagsnummer (Glenn feedback 6:20-6:50) */}
                      <button
                        onClick={() => router.push(`/bilag/${entry.entry_id}`)}
                        className="text-base font-mono font-semibold text-blue-700 dark:text-blue-300 hover:text-blue-900 dark:hover:text-blue-100 hover:underline cursor-pointer transition-colors"
                      >
                        {entry.voucher_number}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-sm font-mono text-gray-900 dark:text-white">
                      {entry.account_number}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-white max-w-xs truncate">
                      {entry.line_description || entry.entry_description}
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-mono text-gray-900 dark:text-white">
                      {entry.debit_amount > 0 ? formatAmount(entry.debit_amount) : "—"}
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-mono text-gray-900 dark:text-white">
                      {entry.credit_amount > 0 ? formatAmount(entry.credit_amount) : "—"}
                    </td>
                    <td className="px-4 py-3 text-sm text-center text-gray-600 dark:text-gray-400">
                      {entry.vat_code || "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Info */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <p className="text-sm text-blue-800 dark:text-blue-200">
          <strong>Hovedbok:</strong> Kronologisk oversikt over alle posteringer. 
          Filtrer på kontonummer for å se posteringer per konto.
          Klikk på bilagsnummer for å se detaljer.
        </p>
      </div>
    </div>
  );
}

export default function HovedbokPage() {
  return (
    <Suspense fallback={
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    }>
      <HovedbokPageContent />
    </Suspense>
  );
}
