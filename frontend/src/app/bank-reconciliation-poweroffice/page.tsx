"use client";

export const dynamic = 'force-dynamic';

import React, { useState, useEffect, useCallback } from "react";
import { useClient } from "@/contexts/ClientContext";
import { toast } from "@/lib/toast";
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XMarkIcon,
  ChevronDownIcon,
  QuestionMarkCircleIcon,
} from "@heroicons/react/24/outline";


// ===== TYPE DEFINITIONS =====

interface BankTransaction {
  id: string;
  date: string;
  amount: number;
  description: string;
  reference?: string;
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

interface UnmatchedTransaction {
  transaction: BankTransaction;
  kid_match?: MatchingResult;
  bilagsnummer_match?: MatchingResult;
  beløp_match?: MatchingResult;
  kombinasjon_match?: MatchingResult;
  best_match?: MatchingResult;
  confidence_category: "high" | "medium" | "low" | "none";
}

interface AutoMatchResponse {
  processed: number;
  matched_high_confidence: number;
  matched_medium_confidence: number;
  matched_low_confidence: number;
  unmatched: number;
  items: UnmatchedTransaction[];
}


// ===== MAIN COMPONENT =====

export default function BankavstemningPowerOfficePage() {
  const { selectedClient } = useClient();
  
  // UI State
  const [activeTab, setActiveTab] = useState<"kid" | "bilagsnummer" | "beløp" | "kombinasjon">("kid");
  const [selectedTransactionId, setSelectedTransactionId] = useState<string | null>(null);
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false);
  
  // Data State
  const [unmatchedTransactions, setUnmatchedTransactions] = useState<UnmatchedTransaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [autoMatching, setAutoMatching] = useState(false);
  const [matchStats, setMatchStats] = useState({
    total: 0,
    matched_high: 0,
    matched_medium: 0,
    matched_low: 0,
    unmatched: 0,
  });
  
  // Filters
  const [dateRange, setDateRange] = useState({ start: "", end: "" });
  const [amountRange, setAmountRange] = useState({ min: 0, max: 100000 });
  const [showHighConfidenceOnly, setShowHighConfidenceOnly] = useState(false);
  
  // Load unmatched transactions on component mount
  useEffect(() => {
    if (selectedClient) {
      loadUnmatchedTransactions();
    }
  }, [selectedClient]);
  
  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === "/") {
        e.preventDefault();
        setShowKeyboardHelp(!showKeyboardHelp);
      }
      
      // Tab navigation with Ctrl+1-4
      if (e.ctrlKey) {
        if (e.key === "1") setActiveTab("kid");
        if (e.key === "2") setActiveTab("bilagsnummer");
        if (e.key === "3") setActiveTab("beløp");
        if (e.key === "4") setActiveTab("kombinasjon");
      }
      
      // Navigate with j/k (vi-style)
      const selectedIdx = unmatchedTransactions.findIndex(
        t => t.transaction.id === selectedTransactionId
      );
      if (e.key === "j" && selectedIdx < unmatchedTransactions.length - 1) {
        setSelectedTransactionId(unmatchedTransactions[selectedIdx + 1].transaction.id);
      }
      if (e.key === "k" && selectedIdx > 0) {
        setSelectedTransactionId(unmatchedTransactions[selectedIdx - 1].transaction.id);
      }
      
      // Accept match with 'a'
      if (e.key === "a" && selectedTransactionId) {
        const selected = unmatchedTransactions.find(
          t => t.transaction.id === selectedTransactionId
        );
        if (selected?.best_match?.matched_voucher_id) {
          acceptMatch(selected.transaction.id, selected.best_match.matched_voucher_id);
        }
      }
    };
    
    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, [selectedTransactionId, unmatchedTransactions]);
  
  // ===== API CALLS =====
  
  const loadUnmatchedTransactions = async () => {
    if (!selectedClient) return;
    
    setLoading(true);
    try {
      // TODO: Replace with actual API call
      // For now, mock data for demonstration
      
      const mockData: UnmatchedTransaction[] = [
        {
          transaction: {
            id: "txn_1",
            date: "2026-02-05",
            amount: -5250.00,
            description: "Invoice INV-2024-001 paid",
            reference: "KID12345678",
          },
          kid_match: {
            bank_transaction_id: "txn_1",
            matched_voucher_id: "v_1",
            category: "kid",
            confidence: 100,
            reason: "Exact KID match",
            primary_match: {
              id: "v_1",
              voucher_number: "INV-2024-001",
              date: "2026-02-05",
              amount: 5250.00,
              description: "Customer invoice",
              confidence: 100,
            },
            suggested_alternatives: [],
          },
          best_match: {
            bank_transaction_id: "txn_1",
            matched_voucher_id: "v_1",
            category: "kid",
            confidence: 100,
            reason: "Exact KID match",
            primary_match: {
              id: "v_1",
              voucher_number: "INV-2024-001",
              date: "2026-02-05",
              amount: 5250.00,
              description: "Customer invoice",
            },
            suggested_alternatives: [],
          },
          confidence_category: "high",
        },
        {
          transaction: {
            id: "txn_2",
            date: "2026-02-06",
            amount: -3500.00,
            description: "Payment REF#8765",
            reference: "",
          },
          bilagsnummer_match: {
            bank_transaction_id: "txn_2",
            matched_voucher_id: "v_2",
            category: "bilagsnummer",
            confidence: 95,
            reason: "Voucher number match: 8765",
            primary_match: {
              id: "v_2",
              voucher_number: "8765",
              date: "2026-02-05",
              amount: 3500.00,
              description: "Supplier payment",
              confidence: 95,
            },
            suggested_alternatives: [],
          },
          best_match: {
            bank_transaction_id: "txn_2",
            matched_voucher_id: "v_2",
            category: "bilagsnummer",
            confidence: 95,
            reason: "Voucher number match",
            primary_match: {
              id: "v_2",
              voucher_number: "8765",
              date: "2026-02-05",
              amount: 3500.00,
              description: "Supplier payment",
            },
            suggested_alternatives: [],
          },
          confidence_category: "high",
        },
        {
          transaction: {
            id: "txn_3",
            date: "2026-02-10",
            amount: 12500.00,
            description: "Bank deposit from customer ABC",
            reference: "",
          },
          beløp_match: {
            bank_transaction_id: "txn_3",
            matched_voucher_id: "v_3",
            category: "beløp",
            confidence: 85,
            reason: "Amount match: 12500 NOK, 2 days difference",
            primary_match: {
              id: "v_3",
              voucher_number: "INV-2024-002",
              date: "2026-02-08",
              amount: 12500.00,
              description: "Customer ABC invoice",
              confidence: 85,
            },
            suggested_alternatives: [
              {
                id: "v_3b",
                voucher_number: "INV-2024-003",
                date: "2026-02-11",
                amount: 12500.00,
                description: "Customer ABC payment",
                confidence: 80,
              },
            ],
          },
          best_match: {
            bank_transaction_id: "txn_3",
            matched_voucher_id: "v_3",
            category: "beløp",
            confidence: 85,
            reason: "Amount match with date proximity",
            primary_match: {
              id: "v_3",
              voucher_number: "INV-2024-002",
              date: "2026-02-08",
              amount: 12500.00,
              description: "Customer ABC invoice",
            },
            suggested_alternatives: [],
          },
          confidence_category: "high",
        },
        {
          transaction: {
            id: "txn_4",
            date: "2026-02-12",
            amount: -750.00,
            description: "Unknown payment reference unclear",
            reference: "",
          },
          kombinasjon_match: {
            bank_transaction_id: "txn_4",
            matched_voucher_id: undefined,
            category: "kombinasjon",
            confidence: 45,
            reason: "No clear match criteria met",
            suggested_alternatives: [
              {
                id: "v_4a",
                voucher_number: "9001",
                date: "2026-02-10",
                amount: 750.00,
                description: "Office supplies",
                confidence: 65,
              },
              {
                id: "v_4b",
                voucher_number: "9002",
                date: "2026-02-15",
                amount: 745.00,
                description: "Miscellaneous expenses",
                confidence: 50,
              },
            ],
          },
          best_match: undefined,
          confidence_category: "low",
        },
      ];
      
      setUnmatchedTransactions(mockData);
      setMatchStats({
        total: mockData.length,
        matched_high: mockData.filter(t => t.confidence_category === "high").length,
        matched_medium: mockData.filter(t => t.confidence_category === "medium").length,
        matched_low: mockData.filter(t => t.confidence_category === "low").length,
        unmatched: mockData.filter(t => t.confidence_category === "none").length,
      });
      
      if (mockData.length > 0) {
        setSelectedTransactionId(mockData[0].transaction.id);
      }
    } catch (error) {
      console.error("Error loading transactions:", error);
      toast.error("Feil ved lasting av transaksjoner");
    } finally {
      setLoading(false);
    }
  };
  
  const acceptMatch = async (transactionId: string, voucherId: string) => {
    try {
      // TODO: Call API to confirm match
      toast.success(`Match confirmed: ${transactionId} → ${voucherId}`);
      
      // Remove from unmatched list
      setUnmatchedTransactions(prev =>
        prev.filter(t => t.transaction.id !== transactionId)
      );
    } catch (error) {
      toast.error("Feil ved bekreftelse av match");
    }
  };
  
  const rejectMatch = (transactionId: string) => {
    // Mark as rejected/manually reviewed
    toast.info("Match marked as rejected");
    setUnmatchedTransactions(prev =>
      prev.filter(t => t.transaction.id !== transactionId)
    );
  };
  
  const runAutoMatch = async () => {
    if (!selectedClient) return;
    
    setAutoMatching(true);
    try {
      // TODO: Call auto-matching API endpoint
      toast.success("Auto-matching completed");
      loadUnmatchedTransactions();
    } catch (error) {
      toast.error("Feil ved auto-matching");
    } finally {
      setAutoMatching(false);
    }
  };
  
  // ===== HELPER FUNCTIONS =====
  
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return "text-green-600 bg-green-50 border-green-200";
    if (confidence >= 70) return "text-yellow-600 bg-yellow-50 border-yellow-200";
    if (confidence > 0) return "text-orange-600 bg-orange-50 border-orange-200";
    return "text-gray-600 bg-gray-50 border-gray-200";
  };
  
  const getConfidenceBadgeClass = (confidence: number) => {
    if (confidence >= 90) return "bg-green-100 text-green-800";
    if (confidence >= 70) return "bg-yellow-100 text-yellow-800";
    if (confidence > 0) return "bg-orange-100 text-orange-800";
    return "bg-gray-100 text-gray-800";
  };
  
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("nb-NO", {
      style: "currency",
      currency: "NOK",
      minimumFractionDigits: 2,
    }).format(amount);
  };
  
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("nb-NO", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
  };
  
  // Get matches for active tab
  const getTabMatches = (): UnmatchedTransaction[] => {
    let filtered = unmatchedTransactions;
    
    if (showHighConfidenceOnly) {
      filtered = filtered.filter(t => t.confidence_category === "high");
    }
    
    return filtered.filter(t => {
      const match =
        activeTab === "kid" ? t.kid_match :
        activeTab === "bilagsnummer" ? t.bilagsnummer_match :
        activeTab === "beløp" ? t.beløp_match :
        t.kombinasjon_match;
      
      return match && match.confidence > 0;
    });
  };
  
  const selectedTransaction = unmatchedTransactions.find(
    t => t.transaction.id === selectedTransactionId
  );
  
  const tabMatches = getTabMatches();
  
  const getMatchForTab = (txn: UnmatchedTransaction): MatchingResult | undefined => {
    if (activeTab === "kid") return txn.kid_match;
    if (activeTab === "bilagsnummer") return txn.bilagsnummer_match;
    if (activeTab === "beløp") return txn.beløp_match;
    return txn.kombinasjon_match;
  };
  
  
  // ===== RENDER =====
  
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Bankavstemming</h1>
              <p className="text-sm text-gray-600 mt-1">
                PowerOffice Design | Intelligente matchingsalgoritmer
              </p>
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowKeyboardHelp(!showKeyboardHelp)}
                className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                title="Ctrl+/"
              >
                <QuestionMarkCircleIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
          
          {/* Stats Bar */}
          <div className="grid grid-cols-5 gap-4 text-sm">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="text-blue-600 font-semibold">{matchStats.total}</div>
              <div className="text-blue-700 text-xs">Transaksjoner</div>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="text-green-600 font-semibold">{matchStats.matched_high}</div>
              <div className="text-green-700 text-xs">Høy sikkerhet (&gt;90%)</div>
            </div>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <div className="text-yellow-600 font-semibold">{matchStats.matched_medium}</div>
              <div className="text-yellow-700 text-xs">Middels sikkerhet (70-90%)</div>
            </div>
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
              <div className="text-orange-600 font-semibold">{matchStats.matched_low}</div>
              <div className="text-orange-700 text-xs">Lav sikkerhet (&lt;70%)</div>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
              <div className="text-gray-600 font-semibold">{matchStats.unmatched}</div>
              <div className="text-gray-700 text-xs">Uten forslag</div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Keyboard Help Modal */}
      {showKeyboardHelp && (
        <div className="bg-blue-50 border-b border-blue-200 px-6 py-4">
          <div className="max-w-7xl mx-auto">
            <h3 className="font-semibold text-blue-900 mb-2">Tastatursnarveier</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-blue-800">
              <div><kbd className="bg-white px-2 py-1 rounded border">Ctrl+1</kbd> KID</div>
              <div><kbd className="bg-white px-2 py-1 rounded border">Ctrl+2</kbd> Bilagsnummer</div>
              <div><kbd className="bg-white px-2 py-1 rounded border">Ctrl+3</kbd> Beløp</div>
              <div><kbd className="bg-white px-2 py-1 rounded border">Ctrl+4</kbd> Kombinasjon</div>
              <div><kbd className="bg-white px-2 py-1 rounded border">j</kbd> Neste</div>
              <div><kbd className="bg-white px-2 py-1 rounded border">k</kbd> Forrige</div>
              <div><kbd className="bg-white px-2 py-1 rounded border">a</kbd> Godta</div>
              <div><kbd className="bg-white px-2 py-1 rounded border">Ctrl+/</kbd> Hjelp</div>
            </div>
          </div>
        </div>
      )}
      
      {/* Main Content - Split View */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-12 gap-6 h-[calc(100vh-400px)]">
          
          {/* Left: Transaction List */}
          <div className="col-span-5 flex flex-col bg-white rounded-lg border border-gray-200 shadow-sm">
            {/* Tabs */}
            <div className="flex border-b border-gray-200 overflow-x-auto">
              <button
                onClick={() => setActiveTab("kid")}
                className={`px-4 py-3 font-medium text-sm transition-colors whitespace-nowrap ${
                  activeTab === "kid"
                    ? "text-blue-600 border-b-2 border-blue-600 bg-blue-50"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                🔑 KID
              </button>
              <button
                onClick={() => setActiveTab("bilagsnummer")}
                className={`px-4 py-3 font-medium text-sm transition-colors whitespace-nowrap ${
                  activeTab === "bilagsnummer"
                    ? "text-blue-600 border-b-2 border-blue-600 bg-blue-50"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                📄 Bilagsnummer
              </button>
              <button
                onClick={() => setActiveTab("beløp")}
                className={`px-4 py-3 font-medium text-sm transition-colors whitespace-nowrap ${
                  activeTab === "beløp"
                    ? "text-blue-600 border-b-2 border-blue-600 bg-blue-50"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                💰 Beløp
              </button>
              <button
                onClick={() => setActiveTab("kombinasjon")}
                className={`px-4 py-3 font-medium text-sm transition-colors whitespace-nowrap ${
                  activeTab === "kombinasjon"
                    ? "text-blue-600 border-b-2 border-blue-600 bg-blue-50"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                🔍 Kombinasjon
              </button>
            </div>
            
            {/* Transaction List */}
            <div className="flex-1 overflow-y-auto">
              {loading ? (
                <div className="p-6 text-center">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <p className="mt-2 text-gray-600">Laster transaksjoner...</p>
                </div>
              ) : tabMatches.length === 0 ? (
                <div className="p-6 text-center text-gray-500">
                  Ingen transaksjoner for denne kategorien
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {tabMatches.map((txn) => {
                    const isSelected = txn.transaction.id === selectedTransactionId;
                    const match = getMatchForTab(txn);
                    
                    return (
                      <button
                        key={txn.transaction.id}
                        onClick={() => setSelectedTransactionId(txn.transaction.id)}
                        className={`w-full text-left px-4 py-3 transition-colors ${
                          isSelected
                            ? "bg-blue-100 border-l-4 border-blue-600"
                            : "hover:bg-gray-50"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <div className="text-sm font-medium text-gray-900">
                            {formatDate(txn.transaction.date)}
                          </div>
                          {match && (
                            <span
                              className={`text-xs px-2 py-1 rounded-full font-medium ${getConfidenceBadgeClass(
                                match.confidence
                              )}`}
                            >
                              {Math.round(match.confidence)}%
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-gray-600 truncate">
                          {txn.transaction.description}
                        </div>
                        <div className="text-sm font-medium text-gray-900 mt-1">
                          {formatCurrency(txn.transaction.amount)}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
            
            {/* Action Buttons */}
            <div className="border-t border-gray-200 p-4 bg-gray-50 space-y-2">
              <button
                onClick={runAutoMatch}
                disabled={autoMatching || loading}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {autoMatching ? "Kjører auto-matching..." : "🤖 Match alle"}
              </button>
              <button
                onClick={() => setShowHighConfidenceOnly(!showHighConfidenceOnly)}
                className={`w-full py-2 px-4 rounded-lg font-medium transition-colors ${
                  showHighConfidenceOnly
                    ? "bg-green-100 text-green-700 border border-green-300"
                    : "bg-gray-200 text-gray-700 border border-gray-300"
                }`}
              >
                {showHighConfidenceOnly ? "✓ Høy sikkerhet aktivert" : "Kun høy sikkerhet"}
              </button>
            </div>
          </div>
          
          {/* Right: Match Details */}
          <div className="col-span-7 flex flex-col bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
            {selectedTransaction ? (
              <>
                {/* Transaction Details Header */}
                <div
                  className={`p-6 border-b border-gray-200 ${getConfidenceColor(
                    selectedTransaction.best_match?.confidence || 0
                  )}`}
                >
                  <h3 className="font-semibold text-lg mb-4">
                    {formatDate(selectedTransaction.transaction.date)} •{" "}
                    {formatCurrency(selectedTransaction.transaction.amount)}
                  </h3>
                  <div className="bg-white bg-opacity-70 p-3 rounded border">
                    <div className="text-sm text-gray-600 mb-1">Bankbeskrivelse</div>
                    <div className="font-medium text-gray-900">
                      {selectedTransaction.transaction.description}
                    </div>
                    {selectedTransaction.transaction.reference && (
                      <div className="text-xs text-gray-500 mt-2">
                        Ref: {selectedTransaction.transaction.reference}
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Match Results - All 4 Categories */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                  {/* KID Match */}
                  {selectedTransaction.kid_match && (
                    <MatchCategory
                      title="KID-matching"
                      result={selectedTransaction.kid_match}
                      formatCurrency={formatCurrency}
                      formatDate={formatDate}
                    />
                  )}
                  
                  {/* Bilagsnummer Match */}
                  {selectedTransaction.bilagsnummer_match && (
                    <MatchCategory
                      title="Bilagsnummer-matching"
                      result={selectedTransaction.bilagsnummer_match}
                      formatCurrency={formatCurrency}
                      formatDate={formatDate}
                    />
                  )}
                  
                  {/* Beløp Match */}
                  {selectedTransaction.beløp_match && (
                    <MatchCategory
                      title="Beløp-matching"
                      result={selectedTransaction.beløp_match}
                      formatCurrency={formatCurrency}
                      formatDate={formatDate}
                    />
                  )}
                  
                  {/* Kombinasjon Match */}
                  {selectedTransaction.kombinasjon_match && (
                    <MatchCategory
                      title="Kombinasjon-matching"
                      result={selectedTransaction.kombinasjon_match}
                      formatCurrency={formatCurrency}
                      formatDate={formatDate}
                    />
                  )}
                </div>
                
                {/* Action Buttons */}
                <div className="border-t border-gray-200 p-4 bg-gray-50 flex gap-2">
                  {selectedTransaction.best_match?.matched_voucher_id ? (
                    <>
                      <button
                        onClick={() =>
                          selectedTransaction.best_match &&
                          acceptMatch(
                            selectedTransaction.transaction.id,
                            selectedTransaction.best_match.matched_voucher_id!
                          )
                        }
                        className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
                      >
                        <CheckCircleIcon className="w-4 h-4" />
                        Godta match (a)
                      </button>
                      <button
                        onClick={() => rejectMatch(selectedTransaction.transaction.id)}
                        className="flex-1 bg-red-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-red-700 transition-colors flex items-center justify-center gap-2"
                      >
                        <XMarkIcon className="w-4 h-4" />
                        Avvis
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => toast.info("Manuell oppføring - ikke implementert ennå")}
                      className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-gray-700 transition-colors flex items-center justify-center gap-2"
                    >
                      <ExclamationTriangleIcon className="w-4 h-4" />
                      Manuell oppføring
                    </button>
                  )}
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                Velg en transaksjon for å se detaljer
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


// ===== SUB-COMPONENT: MATCH CATEGORY =====

interface MatchCategoryProps {
  title: string;
  result: any;
  formatCurrency: (n: number) => string;
  formatDate: (d: string) => string;
}

function MatchCategory({
  title,
  result,
  formatCurrency,
  formatDate,
}: MatchCategoryProps) {
  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-semibold text-gray-900">{title}</h4>
        <span
          className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
            result.confidence >= 90
              ? "bg-green-100 text-green-800"
              : result.confidence >= 70
              ? "bg-yellow-100 text-yellow-800"
              : "bg-gray-100 text-gray-800"
          }`}
        >
          {Math.round(result.confidence)}%
        </span>
      </div>
      
      <p className="text-sm text-gray-600 mb-3">{result.reason}</p>
      
      {result.primary_match && (
        <div className="bg-blue-50 border border-blue-200 rounded p-3 mb-3">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-gray-600">Bilag:</span>
              <div className="font-medium text-gray-900">
                {result.primary_match.voucher_number}
              </div>
            </div>
            <div>
              <span className="text-gray-600">Beløp:</span>
              <div className="font-medium text-gray-900">
                {formatCurrency(result.primary_match.amount)}
              </div>
            </div>
            <div className="col-span-2">
              <span className="text-gray-600">Beskrivelse:</span>
              <div className="font-medium text-gray-900">
                {result.primary_match.description}
              </div>
            </div>
          </div>
        </div>
      )}
      
      {result.suggested_alternatives && result.suggested_alternatives.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-600 mb-2">Andre forslag:</p>
          <div className="space-y-2">
            {result.suggested_alternatives.map((alt: any, i: number) => (
              <div
                key={i}
                className="bg-gray-50 border border-gray-200 rounded p-2 text-sm"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-900">
                    {alt.voucher_number}
                  </span>
                  {alt.confidence && (
                    <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                      {Math.round(alt.confidence)}%
                    </span>
                  )}
                </div>
                <div className="text-gray-600">{alt.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
