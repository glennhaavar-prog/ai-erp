"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

interface Client {
  id: string;
  name: string;
  org_number: string;
  base_currency: string;
}

interface Transaction {
  id: string;
  accounting_date: string;
  description: string;
  voucher_number: string;
  debit_total: number;
  credit_total: number;
}

export default function ClientPortalPage() {
  const params = useParams();
  const clientId = params.client_id as string;
  
  const [client, setClient] = useState<Client | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("30"); // days

  useEffect(() => {
    if (clientId) {
      fetchClientData();
    }
  }, [clientId, filter]);

  const fetchClientData = async () => {
    setLoading(true);
    try {
      // Fetch client info
      const clientRes = await fetch(`http://localhost:8000/api/clients/${clientId}`);
      const clientData = await clientRes.json();
      setClient(clientData);

      // Fetch transactions (general ledger entries)
      const glRes = await fetch(
        `http://localhost:8000/api/general-ledger/?client_id=${clientId}&limit=50`
      );
      const glData = await glRes.json();
      
      // Filter by date range
      const now = new Date();
      const filterDate = new Date();
      filterDate.setDate(now.getDate() - parseInt(filter));
      
      const filtered = glData.entries?.filter((entry: any) => {
        const entryDate = new Date(entry.accounting_date);
        return entryDate >= filterDate;
      }) || [];
      
      setTransactions(filtered);
    } catch (error) {
      console.error("Error fetching portal data:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Laster...</p>
        </div>
      </div>
    );
  }

  if (!client) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 text-lg">Klient ikke funnet</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{client.name}</h1>
              <p className="text-gray-600 mt-1">Org.nr: {client.org_number}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">Klientportal</p>
              <p className="text-xs text-gray-400">Powered by Kontali ERP</p>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-8 py-4">
            <button className="text-blue-600 font-semibold border-b-2 border-blue-600 pb-2">
              📊 Transaksjoner
            </button>
            <button className="text-gray-600 hover:text-gray-900 pb-2">
              📈 Rapporter
            </button>
            <button className="text-gray-600 hover:text-gray-900 pb-2">
              ❓ Hjelp
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Filter Bar */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Siste transaksjoner</h2>
            <div className="flex gap-2">
              <button
                onClick={() => setFilter("30")}
                className={`px-4 py-2 rounded-lg text-sm font-medium ${
                  filter === "30"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                Siste 30 dager
              </button>
              <button
                onClick={() => setFilter("90")}
                className={`px-4 py-2 rounded-lg text-sm font-medium ${
                  filter === "90"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                Siste 90 dager
              </button>
              <button
                onClick={() => setFilter("365")}
                className={`px-4 py-2 rounded-lg text-sm font-medium ${
                  filter === "365"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                I år
              </button>
            </div>
          </div>
        </div>

        {/* Transactions Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          {transactions.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">Ingen transaksjoner funnet for valgt periode</p>
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Dato
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Bilag
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Beskrivelse
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Beløp
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {transactions.map((transaction) => {
                  const amount = transaction.debit_total || -transaction.credit_total;
                  const isPositive = amount > 0;

                  return (
                    <tr key={transaction.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(transaction.accounting_date).toLocaleDateString("nb-NO")}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {transaction.voucher_number}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {transaction.description}
                      </td>
                      <td
                        className={`px-6 py-4 whitespace-nowrap text-sm text-right font-medium ${
                          isPositive ? "text-green-600" : "text-red-600"
                        }`}
                      >
                        {isPositive ? "+" : ""}
                        {amount.toLocaleString("nb-NO", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}{" "}
                        kr
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* AI Chat Prompt */}
        <div className="mt-8 bg-blue-50 border-2 border-blue-200 rounded-lg p-6 text-center">
          <p className="text-blue-900 font-medium mb-2">
            💬 Har du spørsmål om regnskapet ditt?
          </p>
          <p className="text-blue-700 text-sm">
            Klikk på AI-assistenten nede til høyre for å chatte!
          </p>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-6 py-6 text-center text-sm text-gray-500">
          <p>© 2026 Kontali ERP - AI-drevet regnskapsautomatisering</p>
        </div>
      </footer>
    </div>
  );
}
