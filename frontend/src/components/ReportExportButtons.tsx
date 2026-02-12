"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { FileDown, FileSpreadsheet, Loader2 } from "lucide-react";

interface ReportExportButtonsProps {
  reportType: 'saldobalanse' | 'resultat' | 'balanse' | 'hovedbok' | 'supplier-ledger' | 'customer-ledger';
  clientId: string;
  fromDate?: string;
  toDate?: string;
  accountFrom?: string;
  accountTo?: string;
}

export function ReportExportButtons({
  reportType,
  clientId,
  fromDate,
  toDate,
  accountFrom,
  accountTo,
}: ReportExportButtonsProps) {
  const [exporting, setExporting] = useState<'pdf' | 'excel' | null>(null);

  const handleExport = async (format: 'pdf' | 'excel') => {
    setExporting(format);
    try {
      // Build query params
      const params = new URLSearchParams({
        client_id: clientId,
      });

      if (fromDate) params.append('from_date', fromDate);
      if (toDate) params.append('to_date', toDate);
      if (accountFrom) params.append('account_from', accountFrom);
      if (accountTo) params.append('account_to', accountTo);

      // Construct URL
      const url = `http://localhost:8000/api/reports/${reportType}/${format}?${params.toString()}`;

      // Trigger download
      window.open(url, '_blank');
    } catch (error) {
      console.error(`Export to ${format} failed:`, error);
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="flex flex-col sm:flex-row gap-2">
      <Button
        onClick={() => handleExport('pdf')}
        variant="outline"
        disabled={exporting !== null}
        size="sm"
      >
        {exporting === 'pdf' ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <FileDown className="mr-2 h-4 w-4" />
        )}
        {exporting === 'pdf' ? 'Laster ned...' : 'Last ned PDF'}
      </Button>
      <Button
        onClick={() => handleExport('excel')}
        variant="outline"
        disabled={exporting !== null}
        size="sm"
      >
        {exporting === 'excel' ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <FileSpreadsheet className="mr-2 h-4 w-4" />
        )}
        {exporting === 'excel' ? 'Laster ned...' : 'Last ned Excel'}
      </Button>
    </div>
  );
}
