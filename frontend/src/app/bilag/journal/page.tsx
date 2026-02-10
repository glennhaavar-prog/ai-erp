"use client";

import { useState, useEffect } from "react";
import { useClient } from "@/contexts/ClientContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { FileText, Calendar, Filter, Download, Search } from "lucide-react";

interface VoucherEntry {
  id: string;
  voucher_number: string;
  voucher_series: string;
  accounting_date: string;
  voucher_type: string;
  description: string;
  total_debit: number;
  total_credit: number;
  balanced: boolean;
  line_count: number;
  posted_by: string;
  created_at: string;
}

interface VoucherStats {
  total_count: number;
  by_type: Record<string, number>;
  by_posted_by: Record<string, number>;
}

const VOUCHER_TYPES: Record<string, string> = {
  supplier_invoice: "Leverandørfaktura",
  customer_invoice: "Kundefaktura",
  bank_payment: "Bankbetaling",
  bank_receipt: "Bankinnbetaling",
  manual_entry: "Manuell postering",
  salary: "Lønn",
  vat_settlement: "Mva-oppgjør",
  depreciation: "Avskrivning",
  accrual: "Periodisering",
  reversal: "Tilbakeføring",
};

export default function VoucherJournalPage() {
  const { selectedClient, isLoading: clientLoading } = useClient();
  const [entries, setEntries] = useState<VoucherEntry[]>([]);
  const [stats, setStats] = useState<VoucherStats | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [voucherType, setVoucherType] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  useEffect(() => {
    if (selectedClient && selectedClient.id) {
      fetchData(selectedClient.id);
      fetchStats(selectedClient.id);
    }
  }, [selectedClient, voucherType, searchTerm, dateFrom, dateTo]);

  const fetchData = async (cid: string) => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        client_id: cid,
        limit: "100",
      });
      
      if (voucherType && voucherType !== "all") params.append("voucher_type", voucherType);
      if (searchTerm) params.append("search", searchTerm);
      if (dateFrom) params.append("date_from", dateFrom);
      if (dateTo) params.append("date_to", dateTo);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/voucher-journal?${params.toString()}`
      );
      const data = await response.json();
      setEntries(data.entries || []);
    } catch (error) {
      console.error("Error fetching voucher journal:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async (cid: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/voucher-journal/stats?client_id=${cid}`
      );
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("nb-NO", {
      style: "currency",
      currency: "NOK",
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("nb-NO");
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString("nb-NO");
  };

  const getVoucherTypeLabel = (type: string | null) => {
    if (!type) return "Ukjent";
    return VOUCHER_TYPES[type] || type;
  };

  const getPostedByBadge = (postedBy: string | null) => {
    if (!postedBy || postedBy === "AI") {
      return <Badge variant="default" className="bg-blue-500">AI</Badge>;
    }
    return <Badge variant="outline">{postedBy}</Badge>;
  };

  if (clientLoading || loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center">
          {clientLoading ? "Laster klientinformasjon..." : "Laster bilagsjournal..."}
        </div>
      </div>
    );
  }

  if (!selectedClient) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center text-muted-foreground">
          Velg en klient fra menyen øverst for å se bilagsjournal
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Bilagsjournal</h1>
        <p className="text-muted-foreground">
          Kronologisk oversikt over alle transaksjoner
        </p>
      </div>

      {/* Summary Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Totalt Bilag</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_count}</div>
              <p className="text-xs text-muted-foreground">Registrerte transaksjoner</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">AI-Bokførte</CardTitle>
              <FileText className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.by_posted_by?.AI || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                {stats.total_count > 0 ? 
                  ((stats.by_posted_by?.AI || 0) / stats.total_count * 100).toFixed(1) : 0}%
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Leverandørfakturaer</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.by_type?.supplier_invoice || 0}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Kundefakturaer</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.by_type?.customer_invoice || 0}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filtrer
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Bilagstype</label>
              <Select value={voucherType} onValueChange={setVoucherType}>
                <SelectTrigger>
                  <SelectValue placeholder="Alle typer" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Alle typer</SelectItem>
                  {Object.entries(VOUCHER_TYPES).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Fra dato</label>
              <Input 
                type="date" 
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Til dato</label>
              <Input 
                type="date" 
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Søk</label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input 
                  placeholder="Søk i beskrivelse..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Journal Entries */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Bilag ({entries.length})</CardTitle>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Eksporter
          </Button>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Bilag</th>
                  <th className="text-left p-2">Dato</th>
                  <th className="text-left p-2">Type</th>
                  <th className="text-left p-2">Beskrivelse</th>
                  <th className="text-right p-2">Debet</th>
                  <th className="text-right p-2">Kredit</th>
                  <th className="text-left p-2">Bokført av</th>
                </tr>
              </thead>
              <tbody>
                {entries.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center p-8 text-muted-foreground">
                      Ingen bilag funnet
                    </td>
                  </tr>
                ) : (
                  entries.map((entry) => (
                    <tr 
                      key={entry.id} 
                      className="border-b hover:bg-muted/50 cursor-pointer"
                      onClick={() => window.location.href = `/bilag/${entry.id}`}
                    >
                      <td className="p-2">
                        <div className="font-medium">
                          #{entry.voucher_series}-{entry.voucher_number}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {entry.line_count} linjer
                        </div>
                      </td>
                      <td className="p-2">{formatDate(entry.accounting_date)}</td>
                      <td className="p-2">
                        <Badge variant="outline">
                          {getVoucherTypeLabel(entry.voucher_type)}
                        </Badge>
                      </td>
                      <td className="p-2 max-w-xs truncate">{entry.description}</td>
                      <td className="text-right p-2">{formatCurrency(entry.total_debit)}</td>
                      <td className="text-right p-2">{formatCurrency(entry.total_credit)}</td>
                      <td className="p-2">{getPostedByBadge(entry.posted_by)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
