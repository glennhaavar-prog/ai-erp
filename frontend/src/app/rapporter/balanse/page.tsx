"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import DateQuickPicker from "@/components/DateQuickPicker";
import { ReportExportButtons } from "@/components/ReportExportButtons";

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
  udisponert_overskudd: number;
  is_balanced: boolean;
}

export default function BalansePage() {
  const router = useRouter();
  const [data, setData] = useState<BalanseResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [clientId] = useState("8f6d593d-cb4e-42eb-a51c-a7b1dab660dc");
  const [balanceDate, setBalanceDate] = useState<string>("");

  const handleDrilldown = (accountNumber: string) => {
    const params = new URLSearchParams({ account_number: accountNumber });
    if (balanceDate) params.append("to_date", balanceDate);
    router.push(`/rapporter/hovedbok?${params.toString()}`);
  };

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

  const handleQuickDateChange = (_from: string, to: string) => {
    setBalanceDate(to);
    // Auto-fetch after setting date
    setTimeout(() => {
      const params = new URLSearchParams({ client_id: clientId });
      if (to) params.append("to_date", to);
      
      setLoading(true);
      fetch(`http://localhost:8000/api/reports/balanse?${params}`)
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

  // Skill Gjeld (2000-2499) fra Egenkapital (2500-2999)
  const gjeld = data.gjeld_egenkapital.filter(item => 
    item.account_number >= "2000" && item.account_number < "2500"
  );
  const egenkapital = data.gjeld_egenkapital.filter(item => 
    item.account_number >= "2500" && item.account_number < "3000"
  );

  const sum_gjeld = gjeld.reduce((sum, item) => sum + Math.abs(item.balance), 0);
  const sum_egenkapital = egenkapital.reduce((sum, item) => sum + Math.abs(item.balance), 0);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Balanserapport
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Per {data.balance_date}
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          {data.is_balanced && (
            <div className="flex items-center gap-2 px-4 py-2 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
              <span className="text-green-600 dark:text-green-400 text-sm font-medium">
                ✓ Balanse OK
              </span>
            </div>
          )}
          <ReportExportButtons
            reportType="balanse"
            clientId={clientId}
            toDate={balanceDate}
          />
        </div>
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

        {/* Quick date picker */}
        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Hurtigvalg
          </label>
          <DateQuickPicker onDateChange={handleQuickDateChange} />
        </div>
      </div>

      {/* LAYOUT FIX: Vertical layout (not side-by-side) */}
      <div className="space-y-6">
        
        {/* EIENDELER - Top section */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden border-l-4 border-l-blue-500">
          <div className="px-4 py-3 bg-blue-50 dark:bg-blue-900/20 border-b border-blue-200 dark:border-blue-800">
            <h2 className="font-semibold text-lg text-blue-800 dark:text-blue-300">
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
                  className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-900/50"
                >
                  <div>
                    <span className="text-sm font-mono text-gray-600 dark:text-gray-400">
                      {item.account_number}
                    </span>
                    <span className="text-sm text-gray-900 dark:text-white ml-2">
                      {item.account_name}
                    </span>
                  </div>
                  <span 
                    onClick={() => handleDrilldown(item.account_number)}
                    className="text-sm font-mono font-medium text-gray-900 dark:text-white cursor-pointer hover:underline hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                  >
                    {formatAmount(item.balance)}
                  </span>
                </div>
              ))
            )}
          </div>
          <div className="px-4 py-3 bg-blue-50 dark:bg-blue-900/20 border-t border-blue-200 dark:border-blue-800">
            <div className="flex justify-between items-center">
              <span className="font-bold text-blue-800 dark:text-blue-300">
                Sum eiendeler
              </span>
              <span className="text-xl font-mono font-bold text-blue-600 dark:text-blue-400">
                {formatAmount(data.sum_eiendeler)}
              </span>
            </div>
          </div>
        </div>

        {/* GJELD OG EGENKAPITAL - Below eiendeler */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden border-l-4 border-l-purple-500">
          <div className="px-4 py-3 bg-purple-50 dark:bg-purple-900/20 border-b border-purple-200 dark:border-purple-800">
            <h2 className="font-semibold text-lg text-purple-800 dark:text-purple-300">
              GJELD OG EGENKAPITAL
            </h2>
          </div>
          <div className="p-4 space-y-6">
            
            {/* GJELD (2000-2499) først */}
            <div>
              <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">
                Gjeld (Konto 2000-2499)
              </h3>
              <div className="space-y-1 pl-4">
                {gjeld.length === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400">Ingen gjeld registrert</p>
                ) : (
                  gjeld.map((item) => (
                    <div
                      key={item.account_number}
                      className="flex justify-between items-center py-1.5 hover:bg-gray-50 dark:hover:bg-gray-900/50"
                    >
                      <div>
                        <span className="text-sm font-mono text-gray-600 dark:text-gray-400">
                          {item.account_number}
                        </span>
                        <span className="text-sm text-gray-900 dark:text-white ml-2">
                          {item.account_name}
                        </span>
                      </div>
                      <span 
                        onClick={() => handleDrilldown(item.account_number)}
                        className="text-sm font-mono font-medium text-gray-900 dark:text-white cursor-pointer hover:underline hover:text-purple-600 dark:hover:text-purple-400 transition-colors"
                      >
                        {formatAmount(Math.abs(item.balance))}
                      </span>
                    </div>
                  ))
                )}
              </div>
              <div className="flex justify-between items-center mt-2 pt-2 border-t border-gray-200 dark:border-gray-700 pl-4 pr-2">
                <span className="font-semibold text-sm text-gray-700 dark:text-gray-300">
                  Sum gjeld
                </span>
                <span className="text-base font-mono font-bold text-gray-900 dark:text-white">
                  {formatAmount(sum_gjeld)}
                </span>
              </div>
            </div>

            {/* EGENKAPITAL (2500-2999) under gjeld */}
            <div>
              <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">
                Egenkapital (Konto 2500-2999)
              </h3>
              <div className="space-y-1 pl-4">
                {egenkapital.length === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400">Ingen egenkapital registrert</p>
                ) : (
                  egenkapital.map((item) => (
                    <div
                      key={item.account_number}
                      className="flex justify-between items-center py-1.5 hover:bg-gray-50 dark:hover:bg-gray-900/50"
                    >
                      <div>
                        <span className="text-sm font-mono text-gray-600 dark:text-gray-400">
                          {item.account_number}
                        </span>
                        <span className="text-sm text-gray-900 dark:text-white ml-2">
                          {item.account_name}
                        </span>
                      </div>
                      <span 
                        onClick={() => handleDrilldown(item.account_number)}
                        className="text-sm font-mono font-medium text-gray-900 dark:text-white cursor-pointer hover:underline hover:text-purple-600 dark:hover:text-purple-400 transition-colors"
                      >
                        {formatAmount(Math.abs(item.balance))}
                      </span>
                    </div>
                  ))
                )}
              </div>
              <div className="flex justify-between items-center mt-2 pt-2 border-t border-gray-200 dark:border-gray-700 pl-4 pr-2">
                <span className="font-semibold text-sm text-gray-700 dark:text-gray-300">
                  Sum egenkapital
                </span>
                <span className="text-base font-mono font-bold text-gray-900 dark:text-white">
                  {formatAmount(sum_egenkapital)}
                </span>
              </div>
            </div>

          </div>
          
          {/* Sum gjeld og egenkapital */}
          <div className="px-4 py-3 bg-purple-50 dark:bg-purple-900/20 border-t-2 border-purple-300 dark:border-purple-700">
            <div className="flex justify-between items-center">
              <span className="font-bold text-purple-800 dark:text-purple-300">
                Sum gjeld og egenkapital
              </span>
              <span className="text-xl font-mono font-bold text-purple-600 dark:text-purple-400">
                {formatAmount(data.sum_gjeld_egenkapital)}
              </span>
            </div>
          </div>
        </div>

      </div>

      {/* Balance check */}
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
          Udisponert overskudd ({formatAmount(data.udisponert_overskudd)}) er automatisk inkludert under egenkapital.
        </p>
      </div>
    </div>
  );
}
