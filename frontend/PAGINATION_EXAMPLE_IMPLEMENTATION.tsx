/**
 * EXAMPLE: Customer Invoices Page with Pagination
 * 
 * This file demonstrates how to integrate the PaginationControls component
 * into an existing page. Copy this pattern to update other pages.
 * 
 * File location: /frontend/src/app/customer-invoices/page.tsx
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useClient } from '@/contexts/ClientContext';
import { PaginationControls } from '@/components/PaginationControls';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { motion } from 'framer-motion';

interface CustomerInvoice {
  id: string;
  invoice_number: string;
  customer_name: string;
  customer_org_number: string | null;
  invoice_date: string;
  due_date: string;
  amount_excl_vat: number;
  vat_amount: number;
  total_amount: number;
  currency: string;
  payment_status: string;
  created_at: string;
}

interface PaginatedResponse {
  items: CustomerInvoice[];
  total: number;
  limit: number;
  offset: number;
  page_number: number;
}

export default function CustomerInvoicesPage() {
  const { selectedClient, isLoading: clientLoading } = useClient();
  const clientId = selectedClient?.id;

  // ===== PAGINATION STATE =====
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  // ===== DATA STATE =====
  const [invoices, setInvoices] = useState<CustomerInvoice[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  // ===== FILTER STATE =====
  const [paymentStatus, setPaymentStatus] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // ===== EFFECTS =====
  
  // Fetch invoices when pagination or filters change
  useEffect(() => {
    if (clientId) {
      fetchInvoices();
    }
  }, [currentPage, pageSize, paymentStatus, searchQuery, clientId]);

  // ===== FETCH FUNCTIONS =====

  const fetchInvoices = async () => {
    if (!clientId) return;

    setLoading(true);
    try {
      // Calculate offset based on current page
      const offset = (currentPage - 1) * pageSize;

      // Build query URL with pagination and filters
      const params = new URLSearchParams({
        client_id: clientId,
        limit: pageSize.toString(),
        offset: offset.toString(),
      });

      // Add optional filters
      if (paymentStatus) {
        params.append('payment_status', paymentStatus);
      }
      if (searchQuery) {
        params.append('search', searchQuery);
      }

      const url = `http://localhost:8000/api/customer-invoices?${params}`;
      const response = await fetch(url);

      if (response.ok) {
        const data: PaginatedResponse = await response.json();
        setInvoices(data.items);
        setTotal(data.total);
      } else {
        console.error('Failed to fetch invoices:', response.statusText);
      }
    } catch (error) {
      console.error('Failed to fetch invoices:', error);
    } finally {
      setLoading(false);
    }
  };

  // ===== EVENT HANDLERS =====

  const handlePaymentStatusChange = (status: string) => {
    setPaymentStatus(status);
    setCurrentPage(1); // Reset to first page when filtering
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setCurrentPage(1); // Reset to first page when searching
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    // Scroll to top of list
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handlePageSizeChange = (size: number) => {
    setPageSize(size);
    setCurrentPage(1); // Reset to first page when changing page size
  };

  // ===== HELPER FUNCTIONS =====

  const getPaymentStatusBadge = (status: string) => {
    const styles: Record<string, { bg: string; text: string }> = {
      paid: { bg: 'bg-green-100', text: 'text-green-800' },
      unpaid: { bg: 'bg-red-100', text: 'text-red-800' },
      partial: { bg: 'bg-yellow-100', text: 'text-yellow-800' },
      overdue: { bg: 'bg-orange-100', text: 'text-orange-800' },
    };

    const style = styles[status] || styles.unpaid;

    const labels: Record<string, string> = {
      paid: 'Betalt',
      unpaid: 'Ubetalt',
      partial: 'Delvis betalt',
      overdue: 'Forfalt',
    };

    return (
      <Badge className={`${style.bg} ${style.text}`}>
        {labels[status] || status}
      </Badge>
    );
  };

  const formatCurrency = (amount: number, currency: string = 'NOK') => {
    return new Intl.NumberFormat('no-NO', {
      style: 'currency',
      currency,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('no-NO');
  };

  // ===== RENDER =====

  if (clientLoading || !clientId) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <p className="text-gray-500">Velg en klient for å se fakturaer</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* ===== HEADER ===== */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Kundefakturaer</h1>
          <p className="text-gray-600 mt-1">
            Administrer og spor utgående fakturaer
          </p>
        </div>

        <Button
          onClick={() => {
            // Navigate to create invoice page
            // router.push('/customer-invoices/new');
          }}
          className="bg-blue-600 hover:bg-blue-700"
        >
          + Ny faktura
        </Button>
      </div>

      {/* ===== FILTERS ===== */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:gap-4">
            {/* Search */}
            <div className="flex-1">
              <label className="text-sm font-medium block mb-2">
                Søk i kunde eller fakturanummer
              </label>
              <Input
                type="text"
                placeholder="Søk..."
                value={searchQuery}
                onChange={handleSearchChange}
                className="w-full"
              />
            </div>

            {/* Payment Status Filter */}
            <div className="w-full md:w-48">
              <label className="text-sm font-medium block mb-2">
                Betalingsstatus
              </label>
              <Select value={paymentStatus} onValueChange={handlePaymentStatusChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Alle statuser" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Alle statuser</SelectItem>
                  <SelectItem value="paid">Betalt</SelectItem>
                  <SelectItem value="unpaid">Ubetalt</SelectItem>
                  <SelectItem value="partial">Delvis betalt</SelectItem>
                  <SelectItem value="overdue">Forfalt</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Clear Filters */}
            {(paymentStatus || searchQuery) && (
              <Button
                variant="outline"
                onClick={() => {
                  setPaymentStatus('');
                  setSearchQuery('');
                  setCurrentPage(1);
                }}
              >
                Nullstill filtre
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* ===== INVOICE LIST ===== */}
      <div className="space-y-3">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-500">Laster fakturaer...</p>
            </div>
          </div>
        ) : invoices.length > 0 ? (
          invoices.map((invoice, index) => (
            <motion.div
              key={invoice.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: index * 0.05 }}
            >
              <Card className="hover:shadow-md transition-shadow">
                <CardContent className="pt-6">
                  <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                    {/* Invoice Info */}
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className="text-lg font-semibold">
                            {invoice.invoice_number}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {invoice.customer_name}
                            {invoice.customer_org_number &&
                              ` (${invoice.customer_org_number})`}
                          </p>
                        </div>
                      </div>

                      {/* Dates */}
                      <div className="flex gap-4 text-sm text-gray-500">
                        <span>
                          <strong>Fakturadato:</strong> {formatDate(invoice.invoice_date)}
                        </span>
                        <span>
                          <strong>Forfallsdato:</strong> {formatDate(invoice.due_date)}
                        </span>
                      </div>
                    </div>

                    {/* Amount and Status */}
                    <div className="flex flex-col items-end gap-3">
                      <div className="text-right">
                        <p className="text-lg font-bold">
                          {formatCurrency(invoice.total_amount, invoice.currency)}
                        </p>
                        <p className="text-xs text-gray-500">
                          Eksl. mva:{' '}
                          {formatCurrency(invoice.amount_excl_vat, invoice.currency)}
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        {getPaymentStatusBadge(invoice.payment_status)}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            // View invoice details
                            // router.push(`/customer-invoices/${invoice.id}`);
                          }}
                        >
                          Vis
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))
        ) : (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-12">
                <p className="text-gray-500 text-lg">
                  {searchQuery || paymentStatus
                    ? 'Ingen fakturaer funnet som matcher dine søkekriterier'
                    : 'Ingen fakturaer funnet'}
                </p>
                {(searchQuery || paymentStatus) && (
                  <Button
                    variant="outline"
                    className="mt-4"
                    onClick={() => {
                      setPaymentStatus('');
                      setSearchQuery('');
                      setCurrentPage(1);
                    }}
                  >
                    Nullstill filtre
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* ===== PAGINATION ===== */}
      {total > 0 && (
        <Card>
          <CardContent className="pt-6">
            <PaginationControls
              currentPage={currentPage}
              pageSize={pageSize}
              total={total}
              onPageChange={handlePageChange}
              onPageSizeChange={handlePageSizeChange}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
