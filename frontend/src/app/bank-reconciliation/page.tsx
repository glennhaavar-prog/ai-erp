"use client";

export const dynamic = 'force-dynamic';

import React, { useState, useEffect } from "react";
import { useClient } from "@/contexts/ClientContext";
import { toast } from "@/lib/toast";
import Link from "next/link";
import {
  ChevronDownIcon,
  ChevronUpIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowDownIcon,
  ArrowUpIcon,
  SparklesIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";

interface BankAccountSummary {
  account_id: string;
  account_number: string;
  account_name: string;
  saldo_i_bank: number;
  saldo_i_go: number;
  differanse: number;
  poster_a_avstemme: number;
  currency: string;
}

interface CategorizedTransaction {
  id: string;
  date: string;
  description: string;
  beløp: number;
  valutakode: string;
  voucher_number?: string;
  status: string;
}

interface ReconciliationCategory {
  category_key: string;
  category_name: string;
  transactions: CategorizedTransaction[];
  total_beløp: number;
}

interface ReconciliationDetail {
  account_id: string;
  account_number: string;
  account_name: string;
  period_start: string;
  period_end: string;
  categories: ReconciliationCategory[];
  saldo_i_go: number;
  korreksjoner_total: number;
  saldo_etter_korreksjoner: number;
  kontoutskrift_saldo: number;
  differanse: number;
  is_balanced: boolean;
  currency: string;
}

interface VoucherMatch {
  id: string;
  voucher_number: string;
  date?: string;
  amount: number;
  description: string;
  reference?: string;
  confidence?: number;
}

interface MatchingResult {
  bank_transaction_id: string;
  matched_voucher_id?: string;
  category: string;
  confidence: number;
  reason: string;
  primary_match?: VoucherMatch;
  suggested_alternatives: VoucherMatch[];
}

interface BankTransactionForMatching {
  id: string;
  date: string;
  amount: number;
  description: string;
  reference?: string;
}

interface UnmatchedTransaction {
  transaction: BankTransactionForMatching;
  kid_match?: MatchingResult;
  bilagsnummer_match?: MatchingResult;
  beløp_match?: MatchingResult;
  kombinasjon_match?: MatchingResult;
  best_match?: MatchingResult;
  confidence_category: string;
}

interface AutoMatchResponse {
  processed: number;
  matched_high_confidence: number;
  matched_medium_confidence: number;
  matched_low_confidence: number;
  unmatched: number;
  items: UnmatchedTransaction[];
}

export default function BankavstemmingPage() {
  const { selectedClient } = useClient();
  const [view, setView] = useState<"overview" | "detail">("overview");
  const [accounts, setAccounts] = useState<BankAccountSummary[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<ReconciliationDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  
  // Matching state
  const [matchingInProgress, setMatchingInProgress] = useState(false);
  const [matchResults, setMatchResults] = useState<AutoMatchResponse | null>(null);
  const [showMatchResults, setShowMatchResults] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState<string | null>(null);
  const [manualMatchType, setManualMatchType] = useState<string>("");

  // Fetch accounts on load
  useEffect(() => {
    if (selectedClient) {
      fetchAccounts();
    }
  }, [selectedClient]);

  const fetchAccounts = async () => {
    if (!selectedClient) {
      toast.error("Ingen klient valgt");
      return;
    }
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/bank/accounts?client_id=${selectedClient.id}`
      );
      if (response.ok) {
        const data = await response.json();
        setAccounts(data);
      } else {
        toast.error("Feil ved lasting av bankkontoer");
      }
    } catch (error) {
      console.error("Error fetching accounts:", error);
      toast.error("Feil ved lasting av bankkontoer");
    } finally {
      setLoading(false);
    }
  };

  const fetchAccountDetail = async (accountId: string) => {
    if (!selectedClient) {
      toast.error("Ingen klient valgt");
      return;
    }
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/bank/accounts/${accountId}/reconciliation?client_id=${selectedClient.id}`
      );
      if (response.ok) {
        const data = await response.json();
        setSelectedAccount(data);
        setView("detail");
        setExpandedCategories(new Set());
      } else {
        toast.error("Feil ved lasting av avstemmingsdetaljer");
      }
    } catch (error) {
      console.error("Error fetching detail:", error);
      toast.error("Feil ved lasting av avstemmingsdetaljer");
    } finally {
      setLoading(false);
    }
  };

  const toggleCategory = (categoryKey: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(categoryKey)) {
      newExpanded.delete(categoryKey);
    } else {
      newExpanded.add(categoryKey);
    }
    setExpandedCategories(newExpanded);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("nb-NO", {
      style: "currency",
      currency: "NOK",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("nb-NO", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
  };

  // ===== MATCHING FUNCTIONS =====

  const runAutoMatch = async () => {
    if (!selectedClient || !selectedAccount) {
      toast.error("Ingen klient eller konto valgt");
      return;
    }

    setMatchingInProgress(true);
    try {
      // Get unmatched transactions from categories
      const unmatchedTransactions: BankTransactionForMatching[] = [];
      
      selectedAccount.categories.forEach((category) => {
        category.transactions.forEach((txn) => {
          if (txn.status !== "matched") {
            unmatchedTransactions.push({
              id: txn.id,
              date: txn.date,
              amount: txn.beløp,
              description: txn.description,
              reference: txn.voucher_number,
            });
          }
        });
      });

      if (unmatchedTransactions.length === 0) {
        toast.info("Ingen transaksjoner å matche");
        setMatchingInProgress(false);
        return;
      }

      const response = await fetch(
        `http://localhost:8000/api/bank/matching/auto?client_id=${selectedClient.id}&bank_account=${selectedAccount.account_number}&min_confidence=70`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(unmatchedTransactions),
        }
      );

      if (response.ok) {
        const data: AutoMatchResponse = await response.json();
        setMatchResults(data);
        setShowMatchResults(true);
        
        toast.success(
          `Auto-matching fullført! ${data.matched_high_confidence} høy sikkerhet, ${data.matched_medium_confidence} medium sikkerhet`
        );
      } else {
        toast.error("Feil ved auto-matching");
      }
    } catch (error) {
      console.error("Auto-match error:", error);
      toast.error("Feil ved auto-matching");
    } finally {
      setMatchingInProgress(false);
    }
  };

  const runManualMatch = async (
    transaction: CategorizedTransaction,
    matchType: string
  ) => {
    if (!selectedClient || !selectedAccount) {
      toast.error("Ingen klient eller konto valgt");
      return;
    }

    setMatchingInProgress(true);
    try {
      const txnData: BankTransactionForMatching = {
        id: transaction.id,
        date: transaction.date,
        amount: transaction.beløp,
        description: transaction.description,
        reference: transaction.voucher_number,
      };

      const endpoint = {
        kid: "/api/bank/matching/kid",
        bilagsnummer: "/api/bank/matching/bilagsnummer",
        beløp: "/api/bank/matching/beløp",
        kombinasjon: "/api/bank/matching/kombinasjon",
      }[matchType];

      if (!endpoint) {
        toast.error("Ukjent matching-type");
        return;
      }

      const response = await fetch(
        `http://localhost:8000${endpoint}?client_id=${selectedClient.id}&bank_account=${selectedAccount.account_number}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(txnData),
        }
      );

      if (response.ok) {
        const result: MatchingResult = await response.json();
        
        if (result.confidence >= 70) {
          toast.success(
            `Match funnet! Sikkerhet: ${result.confidence.toFixed(0)}%`
          );
          // Here you would typically show the match in a modal or sidebar
          console.log("Match result:", result);
        } else if (result.confidence > 0) {
          toast.info(
            `Lav sikkerhet (${result.confidence.toFixed(0)}%). Vurder manuell matching.`
          );
        } else {
          toast.warning("Ingen match funnet");
        }
      } else {
        toast.error("Feil ved matching");
      }
    } catch (error) {
      console.error("Manual match error:", error);
      toast.error("Feil ved matching");
    } finally {
      setMatchingInProgress(false);
      setSelectedTransaction(null);
      setManualMatchType("");
    }
  };

  const getConfidenceBadgeColor = (category: string) => {
    switch (category) {
      case "high":
        return "bg-green-100 text-green-800 border-green-200";
      case "medium":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "low":
        return "bg-orange-100 text-orange-800 border-orange-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getConfidenceLabel = (category: string) => {
    switch (category) {
      case "high":
        return "Høy sikkerhet";
      case "medium":
        return "Medium sikkerhet";
      case "low":
        return "Lav sikkerhet";
      default:
        return "Ingen match";
    }
  };;

  // ===== OVERVIEW VIEW =====
  if (view === "overview") {
    return (
      <div className="min-h-screen bg-white">
        {/* Header */}
        <div className="border-b border-gray-200 bg-white px-6 py-8">
          <div className="max-w-7xl mx-auto">
            <h1 className="text-3xl font-bold text-gray-900">Bankavstemming</h1>
            <p className="mt-2 text-gray-600">
              Oversikt over alle bankkontoer og avstemmingsstatus
            </p>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-7xl mx-auto px-6 py-8">
          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">Laster bankkontoer...</p>
            </div>
          ) : accounts.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
              <div className="text-4xl mb-2">🏦</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-1">
                Ingen bankkontoer
              </h3>
              <p className="text-gray-600">
                Opprett bankkontoer i innstillinger først
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider">
                      Bankkonto
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider">
                      Kontonavn
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-semibold text-gray-900 uppercase tracking-wider">
                      Saldo i bank
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-semibold text-gray-900 uppercase tracking-wider">
                      Saldo i Go
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-semibold text-gray-900 uppercase tracking-wider">
                      Avstemming
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-semibold text-gray-900 uppercase tracking-wider">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {accounts.map((account) => {
                    const isBalanced = Math.abs(account.differanse) < 0.01;
                    return (
                      <tr
                        key={account.account_id}
                        onClick={() => fetchAccountDetail(account.account_id)}
                        className="hover:bg-blue-50 cursor-pointer transition-colors"
                      >
                        <td className="px-6 py-4 text-sm font-medium text-gray-900">
                          {account.account_number}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {account.account_name}
                        </td>
                        <td className="px-6 py-4 text-sm text-right text-gray-900 font-medium">
                          {formatCurrency(account.saldo_i_bank)}
                        </td>
                        <td className="px-6 py-4 text-sm text-right text-gray-900 font-medium">
                          {formatCurrency(account.saldo_i_go)}
                        </td>
                        <td className="px-6 py-4 text-sm text-center text-gray-600">
                          {account.poster_a_avstemme === 0 ? (
                            <span className="text-green-600 font-medium">
                              ✓ Avstemt
                            </span>
                          ) : (
                            <span className="text-blue-600 font-medium">
                              {account.poster_a_avstemme} poster å avstemme
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-sm text-center">
                          {isBalanced ? (
                            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                              <CheckCircleIcon className="w-4 h-4 mr-1" />
                              Balansert
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                              <ExclamationTriangleIcon className="w-4 h-4 mr-1" />
                              Differanse
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ===== DETAIL VIEW =====
  if (selectedAccount) {
    const isBalanced = Math.abs(selectedAccount.differanse) < 0.01;

    return (
      <div className="min-h-screen bg-white">
        {/* Header */}
        <div className="border-b border-gray-200 bg-white px-6 py-6">
          <div className="max-w-7xl mx-auto">
            <button
              onClick={() => setView("overview")}
              className="text-blue-600 hover:text-blue-700 font-medium mb-4 flex items-center gap-1"
            >
              ← Tilbake til oversikt
            </button>
            <h1 className="text-3xl font-bold text-gray-900">
              {selectedAccount.account_name}
            </h1>
            <div className="mt-2 flex items-center gap-4 text-gray-600">
              <span>Konto: {selectedAccount.account_number}</span>
              <span>•</span>
              <span>
                Periode: {formatDate(selectedAccount.period_start)} -{" "}
                {formatDate(selectedAccount.period_end)}
              </span>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-7xl mx-auto px-6 py-8">
          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">Laster detaljer...</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Auto-Matching Section */}
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                      <SparklesIcon className="w-6 h-6 text-blue-600" />
                      Automatisk Matching
                    </h2>
                    <p className="mt-1 text-sm text-gray-600">
                      La systemet automatisk finne matches for transaksjoner
                    </p>
                  </div>
                  <button
                    onClick={runAutoMatch}
                    disabled={matchingInProgress}
                    className={`px-6 py-3 rounded-lg font-semibold text-white transition-all ${
                      matchingInProgress
                        ? "bg-gray-400 cursor-not-allowed"
                        : "bg-blue-600 hover:bg-blue-700 hover:shadow-lg"
                    }`}
                  >
                    {matchingInProgress ? (
                      <div className="flex items-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        Matcher...
                      </div>
                    ) : (
                      "🚀 Auto-Match Alle"
                    )}
                  </button>
                </div>

                {/* Match Results Summary */}
                {matchResults && showMatchResults && (
                  <div className="mt-4 pt-4 border-t border-blue-200">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-semibold text-gray-900">Resultat</h3>
                      <button
                        onClick={() => setShowMatchResults(false)}
                        className="text-gray-500 hover:text-gray-700"
                      >
                        <XMarkIcon className="w-5 h-5" />
                      </button>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      <div className="bg-white rounded-lg p-3 border border-gray-200">
                        <p className="text-xs text-gray-600">Behandlet</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {matchResults.processed}
                        </p>
                      </div>
                      <div className="bg-green-50 rounded-lg p-3 border border-green-200">
                        <p className="text-xs text-green-700">Høy sikkerhet</p>
                        <p className="text-2xl font-bold text-green-600">
                          {matchResults.matched_high_confidence}
                        </p>
                      </div>
                      <div className="bg-yellow-50 rounded-lg p-3 border border-yellow-200">
                        <p className="text-xs text-yellow-700">Medium sikkerhet</p>
                        <p className="text-2xl font-bold text-yellow-600">
                          {matchResults.matched_medium_confidence}
                        </p>
                      </div>
                      <div className="bg-orange-50 rounded-lg p-3 border border-orange-200">
                        <p className="text-xs text-orange-700">Lav sikkerhet</p>
                        <p className="text-2xl font-bold text-orange-600">
                          {matchResults.matched_low_confidence}
                        </p>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                        <p className="text-xs text-gray-600">Ingen match</p>
                        <p className="text-2xl font-bold text-gray-600">
                          {matchResults.unmatched}
                        </p>
                      </div>
                    </div>

                    {/* Detailed Match Results */}
                    {matchResults.items.length > 0 && (
                      <div className="mt-4 space-y-2 max-h-96 overflow-y-auto">
                        <h4 className="font-semibold text-gray-900 text-sm mb-2">
                          Detaljerte resultater
                        </h4>
                        {matchResults.items.map((item, idx) => (
                          <div
                            key={idx}
                            className="bg-white rounded-lg p-3 border border-gray-200 text-sm"
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <p className="font-medium text-gray-900">
                                  {item.transaction.description}
                                </p>
                                <p className="text-xs text-gray-600 mt-1">
                                  {formatDate(item.transaction.date)} •{" "}
                                  {formatCurrency(item.transaction.amount)}
                                </p>
                              </div>
                              <span
                                className={`px-2 py-1 rounded-full text-xs font-medium border ${getConfidenceBadgeColor(
                                  item.confidence_category
                                )}`}
                              >
                                {getConfidenceLabel(item.confidence_category)}
                              </span>
                            </div>
                            {item.best_match && (
                              <div className="mt-2 pt-2 border-t border-gray-100">
                                <p className="text-xs text-gray-600">
                                  <strong>Beste match:</strong>{" "}
                                  {item.best_match.reason} (
                                  {item.best_match.confidence.toFixed(0)}%)
                                </p>
                                {item.best_match.primary_match && (
                                  <p className="text-xs text-gray-600 mt-1">
                                    Bilag: {item.best_match.primary_match.voucher_number} •{" "}
                                    {item.best_match.primary_match.description}
                                  </p>
                                )}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Categories - Collapsible Accordions */}
              <div className="space-y-3">
                {selectedAccount.categories.map((category) => {
                  const isExpanded = expandedCategories.has(category.category_key);
                  const hasTransactions = category.transactions.length > 0;

                  return (
                    <div
                      key={category.category_key}
                      className="border border-gray-200 rounded-lg overflow-hidden"
                    >
                      {/* Accordion Header */}
                      <button
                        onClick={() => toggleCategory(category.category_key)}
                        className="w-full px-6 py-4 bg-gray-50 hover:bg-gray-100 flex items-center justify-between transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          {hasTransactions && (
                            <ArrowDownIcon
                              className={`w-4 h-4 text-gray-600 transition-transform ${
                                isExpanded ? "rotate-180" : ""
                              }`}
                            />
                          )}
                          <div className="text-left">
                            <h3 className="font-semibold text-gray-900">
                              {category.category_name}
                            </h3>
                            <p className="text-sm text-gray-600">
                              {category.transactions.length} transaksjoner
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold text-gray-900">
                            {formatCurrency(category.total_beløp)}
                          </p>
                        </div>
                      </button>

                      {/* Accordion Content */}
                      {isExpanded && hasTransactions && (
                        <div className="bg-white">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-100 text-xs">
                              <tr>
                                <th className="px-6 py-3 text-left font-semibold text-gray-900">
                                  Dato
                                </th>
                                <th className="px-6 py-3 text-left font-semibold text-gray-900">
                                  Beskrivelse
                                </th>
                                <th className="px-6 py-3 text-right font-semibold text-gray-900">
                                  Beløp
                                </th>
                                <th className="px-6 py-3 text-center font-semibold text-gray-900">
                                  Valutakode
                                </th>
                                <th className="px-6 py-3 text-center font-semibold text-gray-900">
                                  Handlinger
                                </th>
                              </tr>
                            </thead>
                            <tbody>
                              {category.transactions.map((txn) => (
                                <tr key={txn.id} className="hover:bg-blue-50">
                                  <td className="px-6 py-3 text-sm text-gray-900 whitespace-nowrap">
                                    {formatDate(txn.date)}
                                  </td>
                                  <td className="px-6 py-3 text-sm text-gray-600">
                                    {txn.description}
                                    {txn.voucher_number && (
                                      <div className="text-xs text-gray-500 mt-1">
                                        Bilag: {txn.voucher_number}
                                      </div>
                                    )}
                                  </td>
                                  <td className="px-6 py-3 text-sm text-right font-medium text-gray-900">
                                    {formatCurrency(txn.beløp)}
                                  </td>
                                  <td className="px-6 py-3 text-sm text-center text-gray-600">
                                    {txn.valutakode}
                                  </td>
                                  <td className="px-6 py-3 text-sm text-center">
                                    {txn.status !== "matched" && (
                                      <div className="relative inline-block">
                                        {selectedTransaction === txn.id ? (
                                          <div className="flex items-center gap-2">
                                            <select
                                              value={manualMatchType}
                                              onChange={(e) => {
                                                setManualMatchType(e.target.value);
                                                if (e.target.value) {
                                                  runManualMatch(txn, e.target.value);
                                                }
                                              }}
                                              className="px-3 py-1 border border-gray-300 rounded text-xs bg-white"
                                              disabled={matchingInProgress}
                                            >
                                              <option value="">Velg metode...</option>
                                              <option value="kid">Match KID</option>
                                              <option value="bilagsnummer">Match Bilag</option>
                                              <option value="beløp">Match Beløp</option>
                                              <option value="kombinasjon">Kombinert</option>
                                            </select>
                                            <button
                                              onClick={() => {
                                                setSelectedTransaction(null);
                                                setManualMatchType("");
                                              }}
                                              className="text-gray-400 hover:text-gray-600"
                                            >
                                              <XMarkIcon className="w-4 h-4" />
                                            </button>
                                          </div>
                                        ) : (
                                          <button
                                            onClick={() => setSelectedTransaction(txn.id)}
                                            className="px-3 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium hover:bg-blue-200 transition-colors"
                                          >
                                            Match
                                          </button>
                                        )}
                                      </div>
                                    )}
                                    {txn.status === "matched" && (
                                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                        <CheckCircleIcon className="w-3 h-3 mr-1" />
                                        Matchet
                                      </span>
                                    )}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}

                      {/* Empty State */}
                      {!hasTransactions && (
                        <div className="px-6 py-4 bg-gray-50 text-center">
                          <p className="text-sm text-gray-500">Ingen transaksjoner</p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Summary Section */}
              <div className={`border rounded-lg p-6 ${isBalanced ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"}`}>
                <h2 className="text-lg font-bold text-gray-900 mb-4">
                  Avstemmingsoversikt
                </h2>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  {/* Saldo i Go */}
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Saldo i Go</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatCurrency(selectedAccount.saldo_i_go)}
                    </p>
                  </div>

                  {/* Korreksjoner */}
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Korreksjoner</p>
                    <p
                      className={`text-2xl font-bold ${
                        selectedAccount.korreksjoner_total >= 0
                          ? "text-green-600"
                          : "text-red-600"
                      }`}
                    >
                      {formatCurrency(selectedAccount.korreksjoner_total)}
                    </p>
                  </div>

                  {/* Saldo etter korreksjoner */}
                  <div>
                    <p className="text-sm text-gray-600 mb-1">
                      Saldo etter korreksjoner
                    </p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatCurrency(selectedAccount.saldo_etter_korreksjoner)}
                    </p>
                  </div>

                  {/* Kontoutskrift saldo */}
                  <div>
                    <p className="text-sm text-gray-600 mb-1">
                      Kontoutskrift saldo
                    </p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatCurrency(selectedAccount.kontoutskrift_saldo)}
                    </p>
                  </div>
                </div>

                {/* Divider */}
                <hr className="my-4 border-gray-300" />

                {/* Differanse */}
                <div className="flex items-center justify-between">
                  <p className="text-lg font-semibold text-gray-900">Differanse</p>
                  <div className="text-right">
                    <p
                      className={`text-3xl font-bold ${
                        isBalanced ? "text-green-600" : "text-red-600"
                      }`}
                    >
                      {formatCurrency(selectedAccount.differanse)}
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      {isBalanced ? (
                        <span className="text-green-600 font-medium">
                          ✓ Balansert
                        </span>
                      ) : (
                        <span className="text-red-600 font-medium">
                          ⚠ Krever oppfølging
                        </span>
                      )}
                    </p>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4 justify-end">
                <button
                  onClick={() => {
                    toast.info("Utskrift er ikke implementert ennå");
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium transition-colors"
                >
                  🖨 Skriv ut
                </button>
                <button
                  onClick={() => {
                    toast.info("Eksport til PDF er ikke implementert ennå");
                  }}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors"
                >
                  📥 Eksporter
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return null;
}
