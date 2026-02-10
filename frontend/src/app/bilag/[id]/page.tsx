"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import PDFViewer from "@/components/PDFViewer";

interface VoucherLine {
  line_number: number;
  account_number: string;
  account_name: string;
  line_description: string;
  debit_amount: number;
  credit_amount: number;
  vat_code: string | null;
  vat_amount: number | null;
}

interface AuditEntry {
  id: string;
  action: string;
  changed_by_type: string;
  changed_by_name: string;
  timestamp: string;
  reason: string | null;
}

interface Voucher {
  id: string;
  voucher_number: string;
  voucher_series: string;
  entry_date: string;
  accounting_date: string;
  period: string;
  fiscal_year: number;
  description: string;
  source_type: string;
  lines: VoucherLine[];
  total_debit: number;
  total_credit: number;
  is_balanced: boolean;
  document: {
    url: string;
    type: string;
  } | null;
  created_at: string;
}

export default function BilagPage() {
  const params = useParams();
  const router = useRouter();
  const voucherId = params?.id as string;

  const [voucher, setVoucher] = useState<Voucher | null>(null);
  const [auditTrail, setAuditTrail] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const clientId = "8f6d593d-cb4e-42eb-a51c-a7b1dab660dc"; // Demo client
        
        // Fetch voucher details
        const voucherResponse = await fetch(
          `http://localhost:8000/api/vouchers/${voucherId}?client_id=${clientId}`
        );
        
        if (!voucherResponse.ok) {
          throw new Error(`HTTP error! status: ${voucherResponse.status}`);
        }

        const voucherData = await voucherResponse.json();
        setVoucher(voucherData);
        
        // Fetch audit trail
        try {
          const auditResponse = await fetch(
            `http://localhost:8000/api/vouchers/${voucherId}/audit-trail?client_id=${clientId}`
          );
          
          if (auditResponse.ok) {
            const auditData = await auditResponse.json();
            setAuditTrail(auditData.entries || []);
          }
        } catch (auditErr) {
          console.warn("Could not fetch audit trail:", auditErr);
          // Non-critical, continue
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    if (voucherId) {
      fetchData();
    }
  }, [voucherId]);

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

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !voucher) {
    return (
      <div className="p-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-800 dark:text-red-200">
            Feil ved henting av bilag: {error || "Bilag ikke funnet"}
          </p>
          <button
            onClick={() => router.back()}
            className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md font-medium"
          >
            Tilbake
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.back()}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              ← Tilbake
            </button>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Bilag {voucher.voucher_number}
            </h1>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {voucher.description}
          </p>
        </div>

        {voucher.is_balanced && (
          <div className="flex items-center gap-2 px-4 py-2 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <span className="text-green-600 dark:text-green-400 text-sm font-medium">
              ✓ Balanserer
            </span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left side: Document viewer */}
        <div className="space-y-4">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Bilagsinformasjon
            </h2>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Bilagsnummer:</span>
                <span className="text-sm font-mono font-medium text-gray-900 dark:text-white">
                  {voucher.voucher_number}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Serie:</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {voucher.voucher_series}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Bilagsdato:</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {formatDate(voucher.entry_date)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Bokføringsdato:</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {formatDate(voucher.accounting_date)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Periode:</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {voucher.period}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Kilde:</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {voucher.source_type}
                </span>
              </div>
            </div>
          </div>

          {/* Document viewer */}
          <PDFViewer 
            documentUrl={voucher.document?.url || null}
            documentType={voucher.document?.type}
          />
        </div>

        {/* Right side: Accounting lines */}
        <div className="space-y-4">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <div className="px-4 py-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Kontering ({voucher.lines.length} linjer)
              </h2>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-900">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">#</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Konto</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Beskrivelse</th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Debet</th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Kredit</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {voucher.lines.map((line) => (
                    <tr key={line.line_number} className="hover:bg-gray-50 dark:hover:bg-gray-900/50">
                      <td className="px-3 py-3 text-sm text-gray-500 dark:text-gray-400">
                        {line.line_number}
                      </td>
                      <td className="px-3 py-3">
                        <div className="text-sm font-mono font-medium text-gray-900 dark:text-white">
                          {line.account_number}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {line.account_name}
                        </div>
                      </td>
                      <td className="px-3 py-3 text-sm text-gray-900 dark:text-white">
                        {line.line_description}
                        {line.vat_code && (
                          <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                            MVA: {line.vat_code}
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-3 text-sm text-right font-mono text-gray-900 dark:text-white">
                        {line.debit_amount > 0 ? formatAmount(line.debit_amount) : "—"}
                      </td>
                      <td className="px-3 py-3 text-sm text-right font-mono text-gray-900 dark:text-white">
                        {line.credit_amount > 0 ? formatAmount(line.credit_amount) : "—"}
                      </td>
                    </tr>
                  ))}
                  {/* Total row */}
                  <tr className="bg-gray-50 dark:bg-gray-900 font-bold">
                    <td colSpan={3} className="px-3 py-3 text-sm text-gray-900 dark:text-white">
                      SUM
                    </td>
                    <td className="px-3 py-3 text-sm text-right font-mono text-gray-900 dark:text-white">
                      {formatAmount(voucher.total_debit)}
                    </td>
                    <td className="px-3 py-3 text-sm text-right font-mono text-gray-900 dark:text-white">
                      {formatAmount(voucher.total_credit)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Balance check */}
          <div className={`border-2 rounded-lg p-4 ${
            voucher.is_balanced
              ? "bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-700"
              : "bg-red-50 dark:bg-red-900/20 border-red-300 dark:border-red-700"
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <h3 className={`font-semibold ${
                  voucher.is_balanced
                    ? "text-green-800 dark:text-green-300"
                    : "text-red-800 dark:text-red-300"
                }`}>
                  {voucher.is_balanced ? "✓ Bilaget balanserer" : "⚠️ Bilaget balanserer IKKE"}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Debet skal være lik kredit
                </p>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-600 dark:text-gray-400">Differanse:</div>
                <div className={`text-lg font-mono font-bold ${
                  voucher.is_balanced
                    ? "text-green-600 dark:text-green-400"
                    : "text-red-600 dark:text-red-400"
                }`}>
                  {formatAmount(Math.abs(voucher.total_debit - voucher.total_credit))}
                </div>
              </div>
            </div>
          </div>

          {/* Audit Trail */}
          {auditTrail.length > 0 && (
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <div className="px-4 py-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  📋 Revisjonslogg
                </h2>
              </div>
              <div className="p-4 space-y-3">
                {auditTrail.map((entry) => (
                  <div
                    key={entry.id}
                    className="border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-900/20 pl-4 py-2 rounded-r"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-blue-800 dark:text-blue-300">
                            {entry.action === "create" ? "Opprettet" : "Endret"}
                          </span>
                          <span className="text-sm text-gray-600 dark:text-gray-400">
                            av {entry.changed_by_name}
                          </span>
                          {entry.changed_by_type === "ai_agent" && (
                            <span className="text-xs px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 rounded-full">
                              AI
                            </span>
                          )}
                        </div>
                        {entry.reason && (
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {entry.reason}
                          </p>
                        )}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 text-right ml-4">
                        {formatDate(entry.timestamp)}
                        <br />
                        {new Date(entry.timestamp).toLocaleTimeString("nb-NO", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
