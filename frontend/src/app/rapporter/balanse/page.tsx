"use client";

import { useState, useEffect } from "react";

interface BalanceItem {
  account_number: string;
  account_name: string;
  balance: number;
}

interface BalanseResponse {
  client_id: string;
  balance_date: string;
  eiendeler: BalanceItem[];
  sum_eiendeler: number;
  gjeld_egenkapital: BalanceItem[];
  sum_gjeld_egenkapital: number;
  is_balanced: boolean;
}

export default function BalansePage() {
  const [data, setData] = useState<BalanseResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [clientId] = useState("8f6d593d-cb4e-42eb-a51c-a7b1dab660dc");
  const [balanceDate, setBalanceDate] = useState<string>("");

  const fetchBalanse = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({ client_id: clientId });
      if (balanceDate) params.append("to_date", balanceDate);

      const response = await fetch(`http://localhost:8000/api/reports/balanse?${params}`);
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
    fetchBalanse();
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Balanserapport
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Per {data.balance_date}
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

      {/* Date filter */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
        <div className="flex items-end gap-4">
          <div className="flex-1 max-w-xs">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Balansedato
            </label>
            <input
              type="date"
              value={balanceDate}
              onChange={(e) => setBalanceDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
            />
          </div>
          <button
            onClick={fetchBalanse}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-md font-medium"
          >
            {loading ? "Laster..." : "Oppdater"}
          </button>
          <button
            onClick={() => setBalanceDate("")}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md font-medium"
          >
            I dag
          </button>
        </div>
      </div>

      {/* Balance sheet */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* EIENDELER (Assets) */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <div className="px-4 py-3 bg-blue-50 dark:bg-blue-900/20 border-b border-blue-200 dark:border-blue-800">
            <h2 className="font-semibold text-blue-800 dark:text-blue-300">
              EIENDELER (Konto 1000-1999)
            </h2>
          </div>
          <div className="p-4 space-y-2">
            {data.eiendeler.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">Ingen eiendeler registrert</p>
            ) : (
              data.eiendeler.map((item) => (
                <div
                  key={item.account_number}
                  className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-900/50 cursor-pointer"
                >
                  <div>
                    <span className="text-sm font-mono text-gray-600 dark:text-gray-400">
                      {item.account_number}
                    </span>
                    <span className="text-sm text-gray-900 dark:text-white ml-2">
                      {item.account_name}
                    </span>
                  </div>
                  <span className="text-sm font-mono font-medium text-gray-900 dark:text-white">
                    {formatAmount(item.balance)}
                  </span>
                </div>
              ))
            )}
          </div>
          <div className="px-4 py-3 bg-blue-50 dark:bg-blue-900/20 border-t border-blue-200 dark:border-blue-800">
            <div className="flex justify-between items-center">
              <span className="font-semibold text-blue-800 dark:text-blue-300">
                Sum eiendeler
              </span>
              <span className="text-lg font-mono font-bold text-blue-600 dark:text-blue-400">
                {formatAmount(data.sum_eiendeler)}
              </span>
            </div>
          </div>
        </div>

        {/* GJELD & EGENKAPITAL (Liabilities & Equity) */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <div className="px-4 py-3 bg-purple-50 dark:bg-purple-900/20 border-b border-purple-200 dark:border-purple-800">
            <h2 className="font-semibold text-purple-800 dark:text-purple-300">
              GJELD & EGENKAPITAL (Konto 2000-2999)
            </h2>
          </div>
          <div className="p-4 space-y-2">
            {data.gjeld_egenkapital.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">Ingen gjeld/egenkapital registrert</p>
            ) : (
              data.gjeld_egenkapital.map((item) => (
                <div
                  key={item.account_number}
                  className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-900/50 cursor-pointer"
                >
                  <div>
                    <span className="text-sm font-mono text-gray-600 dark:text-gray-400">
                      {item.account_number}
                    </span>
                    <span className="text-sm text-gray-900 dark:text-white ml-2">
                      {item.account_name}
                    </span>
                  </div>
                  <span className="text-sm font-mono font-medium text-gray-900 dark:text-white">
                    {formatAmount(Math.abs(item.balance))}
                  </span>
                </div>
              ))
            )}
          </div>
          <div className="px-4 py-3 bg-purple-50 dark:bg-purple-900/20 border-t border-purple-200 dark:border-purple-800">
            <div className="flex justify-between items-center">
              <span className="font-semibold text-purple-800 dark:text-purple-300">
                Sum gjeld & egenkapital
              </span>
              <span className="text-lg font-mono font-bold text-purple-600 dark:text-purple-400">
                {formatAmount(data.sum_gjeld_egenkapital)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Balance check - Task 15: Improved error message */}
      <div className={`border-2 rounded-lg p-4 ${
        data.is_balanced
          ? "bg-success/10 border-success/30"
          : "bg-destructive/10 border-destructive/30"
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h3 className={`font-semibold flex items-center gap-2 ${
              data.is_balanced
                ? "text-success"
                : "text-destructive"
            }`}>
              {data.is_balanced ? "✓ Balansen balanserer" : "⚠️ Balansen balanserer ikke"}
            </h3>
            <p className="text-sm text-muted-foreground mt-1">
              Eiendeler skal være lik gjeld + egenkapital
            </p>
            {!data.is_balanced && (
              <div className="mt-3 flex items-center gap-3">
                <button className="text-sm text-primary hover:text-accent font-medium underline transition-colors">
                  Hvordan fikse dette? →
                </button>
                <button className="text-sm text-foreground hover:text-primary font-medium px-3 py-1.5 bg-background border border-border rounded-md hover:border-primary transition-all">
                  Se hovedbok
                </button>
              </div>
            )}
          </div>
          <div className="text-right">
            <div className="text-sm text-muted-foreground">Differanse:</div>
            <div className={`text-lg font-mono font-bold tabular-nums ${
              data.is_balanced
                ? "text-success"
                : "text-destructive"
            }`}>
              {formatAmount(data.sum_eiendeler - data.sum_gjeld_egenkapital)}
            </div>
          </div>
        </div>
      </div>

      {/* Info box */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <p className="text-sm text-blue-800 dark:text-blue-200">
          <strong>Balanserapport:</strong> Viser bedriftens økonomiske stilling per valgt dato.
          Eiendeler (det bedriften eier) skal alltid være lik gjeld + egenkapital (hvordan eiendelene er finansiert).
        </p>
      </div>
    </div>
  );
}
