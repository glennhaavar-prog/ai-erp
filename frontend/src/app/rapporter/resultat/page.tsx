"use client";

import { useState, useEffect } from "react";

interface LineItem {
  account_number: string;
  account_name: string;
  amount: number;
}

interface ResultatResponse {
  client_id: string;
  from_date: string | null;
  to_date: string | null;
  inntekter: LineItem[];
  sum_inntekter: number;
  kostnader: LineItem[];
  sum_kostnader: number;
  resultat: number;
}

export default function ResultatPage() {
  const [data, setData] = useState<ResultatResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [clientId] = useState("8f6d593d-cb4e-42eb-a51c-a7b1dab660dc");
  const [fromDate, setFromDate] = useState<string>("");
  const [toDate, setToDate] = useState<string>("");

  const fetchResultat = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({ client_id: clientId });
      if (fromDate) params.append("from_date", fromDate);
      if (toDate) params.append("to_date", toDate);

      const response = await fetch(`http://localhost:8000/api/reports/resultat?${params}`);
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
    fetchResultat();
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
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Resultatregnskap
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Inntekter og kostnader {fromDate && toDate ? `${fromDate} - ${toDate}` : "alle perioder"}
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
        <div className="mt-4 flex gap-2">
          <button
            onClick={fetchResultat}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-md font-medium"
          >
            {loading ? "Laster..." : "Oppdater"}
          </button>
          <button
            onClick={() => {
              setFromDate("");
              setToDate("");
            }}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md font-medium"
          >
            Nullstill
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Inntekter - Task 17: Green accent with left border */}
        <div className="bg-card border border-border rounded-lg overflow-hidden border-l-4 border-l-success">
          <div className="px-4 py-3 bg-success/5 border-b border-success/20">
            <h2 className="font-semibold text-green-800 dark:text-green-300">
              Inntekter (Konto 3000-3999)
            </h2>
          </div>
          <div className="p-4 space-y-2">
            {data.inntekter.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">Ingen inntekter i perioden</p>
            ) : (
              data.inntekter.map((item) => (
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
                  <span className="text-sm font-mono font-medium text-green-600 dark:text-green-400">
                    {formatAmount(item.amount)}
                  </span>
                </div>
              ))
            )}
          </div>
          <div className="px-4 py-3 bg-green-50 dark:bg-green-900/20 border-t border-green-200 dark:border-green-800">
            <div className="flex justify-between items-center">
              <span className="font-semibold text-green-800 dark:text-green-300">
                Sum inntekter
              </span>
              <span className="text-lg font-mono font-bold text-green-600 dark:text-green-400">
                {formatAmount(data.sum_inntekter)}
              </span>
            </div>
          </div>
        </div>

        {/* Kostnader - Task 17: Red accent with left border */}
        <div className="bg-card border border-border rounded-lg overflow-hidden border-l-4 border-l-destructive">
          <div className="px-4 py-3 bg-destructive/5 border-b border-destructive/20">
            <h2 className="font-semibold text-red-800 dark:text-red-300">
              Kostnader (Konto 4000-8999)
            </h2>
          </div>
          <div className="p-4 space-y-2 max-h-96 overflow-y-auto">
            {data.kostnader.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">Ingen kostnader i perioden</p>
            ) : (
              data.kostnader.map((item) => (
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
                  <span className="text-sm font-mono font-medium text-red-600 dark:text-red-400">
                    {formatAmount(item.amount)}
                  </span>
                </div>
              ))
            )}
          </div>
          <div className="px-4 py-3 bg-red-50 dark:bg-red-900/20 border-t border-red-200 dark:border-red-800">
            <div className="flex justify-between items-center">
              <span className="font-semibold text-red-800 dark:text-red-300">
                Sum kostnader
              </span>
              <span className="text-lg font-mono font-bold text-red-600 dark:text-red-400">
                {formatAmount(data.sum_kostnader)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Resultat - Task 17: Teal accent for results */}
      <div className="bg-primary/5 border-2 border-primary/30 rounded-lg overflow-hidden shadow-glow-teal">
        <div className="px-6 py-4">
          <div className="flex justify-between items-center">
            <span className="text-xl font-bold text-foreground">
              Resultat før skatt
            </span>
            <span
              className={`text-3xl font-mono font-bold tabular-nums ${
                data.resultat >= 0
                  ? "text-success"
                  : "text-destructive"
              }`}
            >
              {formatAmount(data.resultat)}
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            {data.resultat >= 0 ? "Overskudd" : "Underskudd"} = Inntekter - Kostnader
          </p>
        </div>
      </div>
    </div>
  );
}
