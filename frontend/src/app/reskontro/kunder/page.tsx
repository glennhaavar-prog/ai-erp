"use client";

import { useState, useEffect } from "react";
import { useClient } from "@/contexts/ClientContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AlertCircle, DollarSign, Calendar, TrendingUp } from "lucide-react";

interface CustomerLedgerEntry {
  id: string;
  customer_name: string;
  customer_id: string | null;
  invoice_number: string;
  invoice_date: string;
  due_date: string;
  amount: number;
  remaining_amount: number;
  currency: string;
  status: string;
  status_label: string;
  days_overdue: number;
  kid_number: string | null;
}

interface AgingData {
  not_due: number;
  "0_30_days": number;
  "31_60_days": number;
  "61_90_days": number;
  "90_plus_days": number;
}

export default function CustomerLedgerPage() {
  const { selectedClient, isLoading: clientLoading } = useClient();
  const [entries, setEntries] = useState<CustomerLedgerEntry[]>([]);
  const [aging, setAging] = useState<AgingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("open");

  useEffect(() => {
    if (selectedClient && selectedClient.id) {
      fetchData(selectedClient.id);
      fetchAging(selectedClient.id);
    }
  }, [selectedClient, statusFilter]);

  const fetchData = async (cid: string) => {
    try {
      setLoading(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/customer-ledger?client_id=${cid}&status=${statusFilter}`
      );
      const data = await response.json();
      setEntries(data.entries || []);
    } catch (error) {
      console.error("Error fetching customer ledger:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAging = async (cid: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/customer-ledger/aging?client_id=${cid}`
      );
      const data = await response.json();
      setAging(data.aging);
    } catch (error) {
      console.error("Error fetching aging data:", error);
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

  const getStatusBadge = (statusLabel: string, daysOverdue: number) => {
    if (statusLabel.includes("kritisk")) {
      return <Badge variant="destructive">{statusLabel}</Badge>;
    }
    if (statusLabel.includes("Forfalt")) {
      return <Badge variant="secondary" className="bg-orange-100 text-orange-800">{statusLabel}</Badge>;
    }
    if (statusLabel.includes("Forfaller snart")) {
      return <Badge variant="outline" className="border-yellow-500 text-yellow-700">{statusLabel}</Badge>;
    }
    if (statusLabel.includes("Betalt")) {
      return <Badge variant="default" className="bg-green-500">Betalt</Badge>;
    }
    return <Badge variant="outline">{statusLabel}</Badge>;
  };

  if (clientLoading || loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center">
          {clientLoading ? "Laster klientinformasjon..." : "Laster kundereskontro..."}
        </div>
      </div>
    );
  }

  if (!selectedClient) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center text-muted-foreground">
          Velg en klient fra menyen øverst for å se kundereskontro
        </div>
      </div>
    );
  }

  const totalRemaining = entries.reduce((sum, e) => sum + e.remaining_amount, 0);
  const overdueEntries = entries.filter(e => e.days_overdue > 0);
  const totalOverdue = overdueEntries.reduce((sum, e) => sum + e.remaining_amount, 0);

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Kundereskontro</h1>
        <p className="text-muted-foreground">
          Oversikt over kundefakturaer og betalingsstatus
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Totalt Åpent</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalRemaining)}</div>
            <p className="text-xs text-muted-foreground">{entries.length} fakturaer</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Forfalt</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{formatCurrency(totalOverdue)}</div>
            <p className="text-xs text-muted-foreground">{overdueEntries.length} fakturaer</p>
          </CardContent>
        </Card>

        {aging && (
          <>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Ikke Forfalt</CardTitle>
                <Calendar className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(aging.not_due)}</div>
                <p className="text-xs text-muted-foreground">
                  {((aging.not_due / totalRemaining) * 100 || 0).toFixed(1)}%
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">90+ Dager</CardTitle>
                <AlertCircle className="h-4 w-4 text-red-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {formatCurrency(aging["90_plus_days"])}
                </div>
                <p className="text-xs text-muted-foreground">Kritisk oppfølging</p>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Filtrer status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="open">Åpne</SelectItem>
                <SelectItem value="overdue">Forfalte</SelectItem>
                <SelectItem value="partially_paid">Delvis betalt</SelectItem>
                <SelectItem value="paid">Betalt</SelectItem>
                <SelectItem value="all">Alle</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Entries Table */}
      <Card>
        <CardHeader>
          <CardTitle>Fakturaer ({entries.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Kunde</th>
                  <th className="text-left p-2">Fakturanr</th>
                  <th className="text-left p-2">Dato</th>
                  <th className="text-left p-2">Forfaller</th>
                  <th className="text-right p-2">Beløp</th>
                  <th className="text-right p-2">Åpent</th>
                  <th className="text-left p-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {entries.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center p-8 text-muted-foreground">
                      Ingen poster funnet
                    </td>
                  </tr>
                ) : (
                  entries.map((entry) => (
                    <tr 
                      key={entry.id} 
                      className={`border-b hover:bg-muted/50 ${
                        entry.days_overdue > 60 ? 'bg-red-50' : 
                        entry.days_overdue > 0 ? 'bg-orange-50' : ''
                      }`}
                    >
                      <td className="p-2">
                        <div className="font-medium">{entry.customer_name}</div>
                        {entry.kid_number && (
                          <div className="text-sm text-muted-foreground">
                            KID: {entry.kid_number}
                          </div>
                        )}
                      </td>
                      <td className="p-2">{entry.invoice_number}</td>
                      <td className="p-2">{formatDate(entry.invoice_date)}</td>
                      <td className="p-2">{formatDate(entry.due_date)}</td>
                      <td className="text-right p-2">{formatCurrency(entry.amount)}</td>
                      <td className="text-right p-2 font-medium">
                        {formatCurrency(entry.remaining_amount)}
                      </td>
                      <td className="p-2">
                        {getStatusBadge(entry.status_label, entry.days_overdue)}
                      </td>
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
