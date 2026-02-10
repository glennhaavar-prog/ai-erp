"use client";

import { useState, useEffect } from "react";
import { useClient } from "@/contexts/ClientContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { AlertCircle, FileText, TrendingUp, Calendar, DollarSign } from "lucide-react";

interface SupplierLedgerEntry {
  id: string;
  supplier_name: string;
  supplier_org_number: string;
  invoice_number: string;
  invoice_date: string;
  due_date: string;
  amount: number;
  remaining_amount: number;
  currency: string;
  status: string;
  days_overdue: number;
}

interface AgingData {
  not_due: number;
  "0_30_days": number;
  "31_60_days": number;
  "61_90_days": number;
  "90_plus_days": number;
}

export default function SupplierLedgerPage() {
  const { selectedClient, isLoading: clientLoading } = useClient();
  const [entries, setEntries] = useState<SupplierLedgerEntry[]>([]);
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
        `http://localhost:8000/supplier-ledger/?client_id=${cid}&status=${statusFilter}`
      );
      const data = await response.json();
      setEntries(data.entries || []);
    } catch (error) {
      console.error("Error fetching supplier ledger:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAging = async (cid: string) => {
    try {
      const response = await fetch(
        `http://localhost:8000/supplier-ledger/aging?client_id=${cid}`
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

  const getStatusBadge = (status: string, daysOverdue: number) => {
    if (status === "paid") {
      return <Badge variant="default" className="bg-green-500">Betalt</Badge>;
    }
    if (daysOverdue > 30) {
      return <Badge variant="destructive">Forfalt ({daysOverdue} dager)</Badge>;
    }
    if (daysOverdue > 0) {
      return <Badge variant="secondary">Forfalt ({daysOverdue} dager)</Badge>;
    }
    return <Badge variant="outline">Åpen</Badge>;
  };

  if (clientLoading || loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center">
          {clientLoading ? "Laster klientinformasjon..." : "Laster leverandørreskontro..."}
        </div>
      </div>
    );
  }

  if (!selectedClient) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center text-muted-foreground">
          Velg en klient fra menyen øverst for å se leverandørreskontro
        </div>
      </div>
    );
  }

  const totalRemaining = entries.reduce((sum, e) => sum + e.remaining_amount, 0);

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Leverandørreskontro</h1>
        <p className="text-muted-foreground">
          Oversikt over leverandørfakturaer og betalingsstatus
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
                <CardTitle className="text-sm font-medium">0-30 Dager</CardTitle>
                <AlertCircle className="h-4 w-4 text-yellow-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(aging["0_30_days"])}</div>
                <p className="text-xs text-muted-foreground">
                  {((aging["0_30_days"] / totalRemaining) * 100 || 0).toFixed(1)}%
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">30+ Dager</CardTitle>
                <AlertCircle className="h-4 w-4 text-red-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatCurrency(aging["31_60_days"] + aging["61_90_days"] + aging["90_plus_days"])}
                </div>
                <p className="text-xs text-muted-foreground">Krever oppfølging</p>
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
          <CardTitle>Åpne Poster ({entries.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Leverandør</th>
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
                    <tr key={entry.id} className="border-b hover:bg-muted/50">
                      <td className="p-2">
                        <div className="font-medium">{entry.supplier_name}</div>
                        <div className="text-sm text-muted-foreground">
                          {entry.supplier_org_number}
                        </div>
                      </td>
                      <td className="p-2">{entry.invoice_number}</td>
                      <td className="p-2">{formatDate(entry.invoice_date)}</td>
                      <td className="p-2">{formatDate(entry.due_date)}</td>
                      <td className="text-right p-2">{formatCurrency(entry.amount)}</td>
                      <td className="text-right p-2 font-medium">
                        {formatCurrency(entry.remaining_amount)}
                      </td>
                      <td className="p-2">{getStatusBadge(entry.status, entry.days_overdue)}</td>
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
