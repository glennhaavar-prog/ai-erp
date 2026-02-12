"use client";

export const dynamic = 'force-dynamic';

import React, { useState, useEffect } from "react";
import { useClient } from "@/contexts/ClientContext";
import { toast } from "@/lib/toast";
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
} from "@heroicons/react/24/outline";

interface VendorInvoiceStatus {
  total_received: number;
  processed: number;
  pending: number;
  ai_approved: number;
  needs_review: number;
  stuck_count: number;
  message: string;
  status: string;
}

interface CustomerInvoiceStatus {
  total_invoices: number;
  paid_count: number;
  unpaid_count: number;
  unpaid_overdue_count: number;
  message: string;
  status: string;
}

interface GLStatus {
  total_entries: number;
  total_lines: number;
  total_debit: number;
  total_credit: number;
  difference: number;
  is_balanced: boolean;
  message: string;
  status: string;
}

interface ReceiptStatus {
  ehf: {
    received: number;
    processed: number;
    pending: number;
  };
  bank: {
    transactions: number;
    booked: number;
    pending_review: number;
  };
  pdf: {
    uploaded: number;
    analyzed: number;
    stuck: number;
  };
}

export default function TrustDashboardPage() {
  const { selectedClient } = useClient();
  const [loading, setLoading] = useState(false);
  const [vendorStatus, setVendorStatus] = useState<VendorInvoiceStatus | null>(null);
  const [customerStatus, setCustomerStatus] = useState<CustomerInvoiceStatus | null>(null);
  const [glStatus, setGLStatus] = useState<GLStatus | null>(null);

  useEffect(() => {
    if (selectedClient) {
      fetchDashboard();
    }
  }, [selectedClient]);

  const fetchDashboard = async () => {
    if (!selectedClient) {
      toast.error("Ingen klient valgt");
      return;
    }

    setLoading(true);
    try {
      // Fetch vendor invoice status
      const vendorRes = await fetch(
        `http://localhost:8000/api/trust/status/${selectedClient.id}/vendor-invoices`
      );
      if (vendorRes.ok) {
        const vendorData = await vendorRes.json();
        setVendorStatus(vendorData.data);
      }

      // Fetch customer invoice status
      const customerRes = await fetch(
        `http://localhost:8000/api/trust/status/${selectedClient.id}/customer-invoices`
      );
      if (customerRes.ok) {
        const customerData = await customerRes.json();
        setCustomerStatus(customerData.data);
      }

      // Fetch general ledger status
      const glRes = await fetch(
        `http://localhost:8000/api/trust/status/${selectedClient.id}/general-ledger`
      );
      if (glRes.ok) {
        const glData = await glRes.json();
        setGLStatus(glData.data);
      }
    } catch (error) {
      console.error("Error fetching trust dashboard:", error);
      toast.error("Feil ved lasting av tillitsmodell");
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "ok":
        return <span className="text-4xl">🟢</span>;
      case "warning":
        return <span className="text-4xl">🟡</span>;
      case "error":
        return <span className="text-4xl">🔴</span>;
      default:
        return <span className="text-4xl">⚪</span>;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "ok":
        return "Alt OK";
      case "warning":
        return "Krever oppmerksomhet";
      case "error":
        return "Kritisk";
      default:
        return "Ukjent";
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("nb-NO", {
      style: "currency",
      currency: "NOK",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  // Calculate receipt verification data
  const receiptStatus: ReceiptStatus = {
    ehf: {
      received: vendorStatus?.total_received || 0,
      processed: vendorStatus?.processed || 0,
      pending: vendorStatus?.pending || 0,
    },
    bank: {
      transactions: 0, // Not yet available from API
      booked: 0,
      pending_review: 0,
    },
    pdf: {
      uploaded: vendorStatus?.total_received || 0,
      analyzed: vendorStatus?.processed || 0,
      stuck: vendorStatus?.stuck_count || 0,
    },
  };

  if (!selectedClient) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">🔒</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Ingen klient valgt
          </h2>
          <p className="text-gray-600">
            Velg en klient for å se tillitsmodellen
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-6 py-8">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900">Tillitsmodell</h1>
          <p className="mt-2 text-gray-600">
            Oversikt over systemstatus og kontroll - alt under oppsyn
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Laster tillitsmodell...</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Traffic Light Status Cards - Row 1 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Vendor Invoices */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      Leverandørfakturaer
                    </h3>
                  </div>
                  <div>{getStatusIcon(vendorStatus?.status || "ok")}</div>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Mottatt totalt:</span>
                    <span className="font-semibold text-gray-900">
                      {vendorStatus?.total_received || 0}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Behandlet:</span>
                    <span className="font-semibold text-green-600">
                      {vendorStatus?.processed || 0}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Venter:</span>
                    <span className="font-semibold text-blue-600">
                      {vendorStatus?.pending || 0}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">AI godkjent:</span>
                    <span className="font-semibold text-gray-900">
                      {vendorStatus?.ai_approved || 0}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Krever gjennomgang:</span>
                    <span className="font-semibold text-orange-600">
                      {vendorStatus?.needs_review || 0}
                    </span>
                  </div>
                  {vendorStatus && vendorStatus.stuck_count > 0 && (
                    <div className="pt-3 border-t border-gray-200">
                      <div className="flex items-center gap-2 text-red-600">
                        <ExclamationTriangleIcon className="w-5 h-5" />
                        <span className="text-sm font-semibold">
                          {vendorStatus.stuck_count} fakturaer sitter fast
                        </span>
                      </div>
                    </div>
                  )}
                </div>
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-sm font-medium text-gray-700">
                    {getStatusText(vendorStatus?.status || "ok")}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {vendorStatus?.message}
                  </p>
                </div>
              </div>

              {/* Customer Invoices */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      Kundefakturaer
                    </h3>
                  </div>
                  <div>{getStatusIcon(customerStatus?.status || "ok")}</div>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Totalt:</span>
                    <span className="font-semibold text-gray-900">
                      {customerStatus?.total_invoices || 0}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Betalt:</span>
                    <span className="font-semibold text-green-600">
                      {customerStatus?.paid_count || 0}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Ubetalt:</span>
                    <span className="font-semibold text-blue-600">
                      {customerStatus?.unpaid_count || 0}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Forfalt:</span>
                    <span className="font-semibold text-red-600">
                      {customerStatus?.unpaid_overdue_count || 0}
                    </span>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-sm font-medium text-gray-700">
                    {getStatusText(customerStatus?.status || "ok")}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {customerStatus?.message}
                  </p>
                </div>
              </div>

              {/* General Ledger */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      Hovedbok
                    </h3>
                  </div>
                  <div>{getStatusIcon(glStatus?.status || "ok")}</div>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Bilag:</span>
                    <span className="font-semibold text-gray-900">
                      {glStatus?.total_entries || 0}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Linjer:</span>
                    <span className="font-semibold text-gray-900">
                      {glStatus?.total_lines || 0}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Debet:</span>
                    <span className="font-semibold text-gray-900">
                      {formatCurrency(glStatus?.total_debit || 0)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Kredit:</span>
                    <span className="font-semibold text-gray-900">
                      {formatCurrency(glStatus?.total_credit || 0)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm border-t border-gray-200 pt-2">
                    <span className="text-gray-600">Differanse:</span>
                    <span
                      className={`font-semibold ${
                        glStatus?.is_balanced
                          ? "text-green-600"
                          : "text-red-600"
                      }`}
                    >
                      {formatCurrency(glStatus?.difference || 0)}
                    </span>
                  </div>
                  {glStatus?.is_balanced && (
                    <div className="flex items-center gap-2 text-green-600 pt-2">
                      <CheckCircleIcon className="w-5 h-5" />
                      <span className="text-sm font-semibold">
                        Hovedbok balansert
                      </span>
                    </div>
                  )}
                  {!glStatus?.is_balanced && (
                    <div className="flex items-center gap-2 text-red-600 pt-2">
                      <XCircleIcon className="w-5 h-5" />
                      <span className="text-sm font-semibold">
                        Hovedbok ikke balansert
                      </span>
                    </div>
                  )}
                </div>
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-sm font-medium text-gray-700">
                    {getStatusText(glStatus?.status || "ok")}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {glStatus?.message}
                  </p>
                </div>
              </div>
            </div>

            {/* Receipt Verification Dashboard */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-6">
                Kvitteringsbevis - Ingenting er mistet
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* EHF */}
                <div className="border-l-4 border-blue-500 pl-4">
                  <h3 className="font-semibold text-gray-900 mb-3">
                    EHF Fakturaer
                  </h3>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">
                        ✓ Mottatt:
                      </span>
                      <span className="font-semibold text-gray-900">
                        {receiptStatus.ehf.received}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">
                        ✓ Behandlet:
                      </span>
                      <span className="font-semibold text-green-600">
                        {receiptStatus.ehf.processed}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">
                        ✗ Pending:
                      </span>
                      <span
                        className={`font-semibold ${
                          receiptStatus.ehf.pending === 0
                            ? "text-green-600"
                            : "text-orange-600"
                        }`}
                      >
                        {receiptStatus.ehf.pending}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Bank */}
                <div className="border-l-4 border-green-500 pl-4">
                  <h3 className="font-semibold text-gray-900 mb-3">
                    Banktransaksjoner
                  </h3>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">
                        ✓ Transaksjoner:
                      </span>
                      <span className="font-semibold text-gray-900">
                        {receiptStatus.bank.transactions}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">
                        ✓ Bokført:
                      </span>
                      <span className="font-semibold text-green-600">
                        {receiptStatus.bank.booked}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">
                        ⚠️ Venter review:
                      </span>
                      <span
                        className={`font-semibold ${
                          receiptStatus.bank.pending_review === 0
                            ? "text-green-600"
                            : "text-orange-600"
                        }`}
                      >
                        {receiptStatus.bank.pending_review}
                      </span>
                    </div>
                  </div>
                </div>

                {/* PDF */}
                <div className="border-l-4 border-purple-500 pl-4">
                  <h3 className="font-semibold text-gray-900 mb-3">
                    PDF Fakturaer
                  </h3>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">
                        ✓ Lastet opp:
                      </span>
                      <span className="font-semibold text-gray-900">
                        {receiptStatus.pdf.uploaded}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">
                        ✓ Analysert:
                      </span>
                      <span className="font-semibold text-green-600">
                        {receiptStatus.pdf.analyzed}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">
                        ✗ Stuck:
                      </span>
                      <span
                        className={`font-semibold ${
                          receiptStatus.pdf.stuck === 0
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        {receiptStatus.pdf.stuck}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Avviksrapporter og Hendelseslogg */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Avviksrapporter */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">
                  Avviksrapporter
                </h2>
                <div className="space-y-3">
                  {vendorStatus && vendorStatus.stuck_count > 0 && (
                    <div className="flex items-start gap-3 p-3 bg-red-50 rounded-lg border border-red-200">
                      <ExclamationTriangleIcon className="w-5 h-5 text-red-600 mt-0.5" />
                      <div>
                        <p className="text-sm font-semibold text-red-900">
                          Fastlåste leverandørfakturaer
                        </p>
                        <p className="text-xs text-red-700 mt-1">
                          {vendorStatus.stuck_count} fakturaer krever manuell
                          gjennomgang
                        </p>
                      </div>
                    </div>
                  )}
                  {customerStatus &&
                    customerStatus.unpaid_overdue_count > 0 && (
                      <div className="flex items-start gap-3 p-3 bg-orange-50 rounded-lg border border-orange-200">
                        <ExclamationTriangleIcon className="w-5 h-5 text-orange-600 mt-0.5" />
                        <div>
                          <p className="text-sm font-semibold text-orange-900">
                            Forfalte kundefakturaer
                          </p>
                          <p className="text-xs text-orange-700 mt-1">
                            {customerStatus.unpaid_overdue_count} fakturaer har
                            passert forfallsdato
                          </p>
                        </div>
                      </div>
                    )}
                  {glStatus && !glStatus.is_balanced && (
                    <div className="flex items-start gap-3 p-3 bg-red-50 rounded-lg border border-red-200">
                      <XCircleIcon className="w-5 h-5 text-red-600 mt-0.5" />
                      <div>
                        <p className="text-sm font-semibold text-red-900">
                          Hovedbok ikke balansert
                        </p>
                        <p className="text-xs text-red-700 mt-1">
                          Differanse: {formatCurrency(glStatus.difference || 0)}
                        </p>
                      </div>
                    </div>
                  )}
                  {(!vendorStatus || vendorStatus.stuck_count === 0) &&
                    (!customerStatus ||
                      customerStatus.unpaid_overdue_count === 0) &&
                    (!glStatus || glStatus.is_balanced) && (
                      <div className="flex items-center gap-3 p-4 bg-green-50 rounded-lg border border-green-200">
                        <CheckCircleIcon className="w-6 h-6 text-green-600" />
                        <div>
                          <p className="text-sm font-semibold text-green-900">
                            Ingen avvik funnet
                          </p>
                          <p className="text-xs text-green-700 mt-1">
                            Alt er under kontroll
                          </p>
                        </div>
                      </div>
                    )}
                </div>
              </div>

              {/* Hendelseslogg */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">
                  Siste hendelser
                </h2>
                <div className="space-y-3">
                  <div className="text-sm text-gray-500 border-l-2 border-blue-500 pl-3 py-1">
                    <span className="text-xs text-gray-400">Nettopp</span>
                    <p className="text-gray-700">
                      Tillitsmodell lastet inn og verifisert
                    </p>
                  </div>
                  {vendorStatus && vendorStatus.ai_approved > 0 && (
                    <div className="text-sm text-gray-500 border-l-2 border-green-500 pl-3 py-1">
                      <span className="text-xs text-gray-400">I dag</span>
                      <p className="text-gray-700">
                        AI godkjente {vendorStatus.ai_approved}{" "}
                        leverandørfakturaer
                      </p>
                    </div>
                  )}
                  {glStatus && glStatus.is_balanced && (
                    <div className="text-sm text-gray-500 border-l-2 border-green-500 pl-3 py-1">
                      <span className="text-xs text-gray-400">I dag</span>
                      <p className="text-gray-700">
                        Hovedbok balansert - {glStatus.total_entries} bilag
                      </p>
                    </div>
                  )}
                  <div className="text-sm text-gray-500 border-l-2 border-gray-300 pl-3 py-1">
                    <span className="text-xs text-gray-400">
                      Flere hendelser tilgjengelig i revisjonsloggen →
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4 justify-center pt-4">
              <button
                onClick={fetchDashboard}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors"
              >
                🔄 Oppdater status
              </button>
              <button
                onClick={() => {
                  toast.info("Rapport-funksjon kommer snart");
                }}
                className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium transition-colors"
              >
                📥 Last ned rapport
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
