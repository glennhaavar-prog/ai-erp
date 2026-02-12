/**
 * Dashboard Metrics Cards Component
 * Task 2B - Comprehensive dashboard metrics for Kontali ERP main page
 */
'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  FileText, 
  CreditCard, 
  TrendingUp, 
  TrendingDown, 
  AlertCircle,
  CheckCircle2,
  Clock,
  ArrowRight,
  RefreshCw
} from 'lucide-react';
import { useRouter } from 'next/navigation';

interface DashboardMetrics {
  timestamp: string;
  metrics: {
    ubehandlede_fakturaer: {
      count: number;
      description: string;
      action_url: string;
    };
    bank_til_matching: {
      count: number;
      description: string;
      action_url: string;
    };
    maanedlig_resultat: {
      innevaerende_maaned: {
        amount: number;
        currency: string;
        period: string;
        description: string;
      };
      forrige_maaned: {
        amount: number;
        currency: string;
        period: string;
        description: string;
      };
      change: {
        amount: number;
        percentage: number;
      };
      action_url: string;
    };
    review_queue: {
      total: number;
      by_priority: {
        low: number;
        medium: number;
        high: number;
        urgent: number;
      };
      by_status: {
        pending: number;
        in_progress: number;
        approved: number;
        corrected: number;
        rejected: number;
      };
      action_url: string;
    };
    auto_booking_performance: {
      rate: number;
      total_invoices_30d: number;
      auto_approved_30d: number;
      description: string;
    };
  };
  quick_actions: Array<{
    label: string;
    url: string;
    icon: string;
    badge: number | null;
  }>;
}

export function DashboardMetricsCards() {
  const router = useRouter();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchMetrics = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/dashboard/metrics');
      if (!response.ok) throw new Error('Failed to fetch metrics');
      const data = await response.json();
      setMetrics(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchMetrics();
  };

  const formatCurrency = (amount: number | null | undefined, currency: string = 'NOK') => {
    // Handle null/undefined/non-numeric values
    if (amount == null || isNaN(Number(amount))) {
      return new Intl.NumberFormat('nb-NO', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(0);
    }
    return new Intl.NumberFormat('nb-NO', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(Number(amount));
  };

  const formatPercent = (value: number | null | undefined) => {
    // Handle null/undefined/non-numeric values
    if (value == null || isNaN(Number(value))) {
      return '0.0%';
    }
    const numValue = Number(value);
    const sign = numValue > 0 ? '+' : '';
    return `${sign}${numValue.toFixed(1)}%`;
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-8 w-24 mt-2" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-4 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="p-6">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="w-5 h-5" />
              <span>Kunne ikke laste dashboard-data: {error}</span>
              <Button variant="outline" size="sm" onClick={handleRefresh}>
                Prøv igjen
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { ubehandlede_fakturaer, bank_til_matching, maanedlig_resultat, review_queue, auto_booking_performance } = metrics.metrics;

  return (
    <div className="space-y-6 p-6">
      {/* Header with refresh button */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-foreground">Dashboard</h2>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={refreshing}
          className="gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Oppdater
        </Button>
      </div>

      {/* Main metrics cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Card 1: Ubehandlede fakturaer */}
        <Card 
          className="hover:shadow-lg transition-shadow cursor-pointer border-l-4 border-l-orange-500"
          onClick={() => router.push(ubehandlede_fakturaer.action_url)}
        >
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Ubehandlede fakturaer
              </CardTitle>
              <FileText className="w-5 h-5 text-orange-500" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-3xl font-bold text-foreground">
                {ubehandlede_fakturaer.count}
              </div>
              <p className="text-sm text-muted-foreground">
                {ubehandlede_fakturaer.description}
              </p>
              {ubehandlede_fakturaer.count > 0 && (
                <Badge variant="secondary" className="mt-2">
                  Trenger oppmerksomhet
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Card 2: Bank til matching */}
        <Card 
          className="hover:shadow-lg transition-shadow cursor-pointer border-l-4 border-l-blue-500"
          onClick={() => router.push(bank_til_matching.action_url)}
        >
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Bank til matching
              </CardTitle>
              <CreditCard className="w-5 h-5 text-blue-500" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-3xl font-bold text-foreground">
                {bank_til_matching.count}
              </div>
              <p className="text-sm text-muted-foreground">
                {bank_til_matching.description}
              </p>
              {bank_til_matching.count === 0 ? (
                <Badge className="mt-2 bg-green-100 text-green-800">
                  <CheckCircle2 className="w-3 h-3 mr-1" />
                  Alle matchet
                </Badge>
              ) : (
                <Badge variant="secondary" className="mt-2">
                  Trenger matching
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Card 3: Review Queue */}
        <Card 
          className="hover:shadow-lg transition-shadow cursor-pointer border-l-4 border-l-purple-500"
          onClick={() => router.push(review_queue.action_url)}
        >
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Review Queue
              </CardTitle>
              <Clock className="w-5 h-5 text-purple-500" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-3xl font-bold text-foreground">
                {review_queue.by_status.pending}
              </div>
              <p className="text-sm text-muted-foreground">
                Venter på behandling
              </p>
              <div className="flex gap-2 mt-2">
                {review_queue.by_priority.urgent > 0 && (
                  <Badge variant="destructive" className="text-xs">
                    {review_queue.by_priority.urgent} urgent
                  </Badge>
                )}
                {review_queue.by_priority.high > 0 && (
                  <Badge variant="secondary" className="text-xs bg-red-100 text-red-800">
                    {review_queue.by_priority.high} høy
                  </Badge>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Card 4: Månedlig resultat - Inneværende måned */}
        <Card 
          className="hover:shadow-lg transition-shadow cursor-pointer border-l-4 border-l-green-500"
          onClick={() => router.push(maanedlig_resultat.action_url)}
        >
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Resultat inneværende måned
              </CardTitle>
              {maanedlig_resultat.innevaerende_maaned.amount >= 0 ? (
                <TrendingUp className="w-5 h-5 text-green-500" />
              ) : (
                <TrendingDown className="w-5 h-5 text-red-500" />
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className={`text-3xl font-bold ${
                maanedlig_resultat.innevaerende_maaned.amount >= 0 
                  ? 'text-green-600' 
                  : 'text-red-600'
              }`}>
                {formatCurrency(maanedlig_resultat.innevaerende_maaned.amount)}
              </div>
              <p className="text-sm text-muted-foreground">
                {maanedlig_resultat.innevaerende_maaned.description}
              </p>
              <Badge 
                variant="secondary" 
                className={`mt-2 ${
                  maanedlig_resultat.change.amount >= 0 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}
              >
                {formatPercent(maanedlig_resultat.change.percentage)} vs forrige måned
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Card 5: Månedlig resultat - Forrige måned */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Resultat forrige måned
              </CardTitle>
              <TrendingUp className="w-5 h-5 text-gray-400" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className={`text-3xl font-bold ${
                maanedlig_resultat.forrige_maaned.amount >= 0 
                  ? 'text-green-600' 
                  : 'text-red-600'
              }`}>
                {formatCurrency(maanedlig_resultat.forrige_maaned.amount)}
              </div>
              <p className="text-sm text-muted-foreground">
                {maanedlig_resultat.forrige_maaned.description}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Card 6: Auto-booking Performance */}
        <Card className="hover:shadow-lg transition-shadow border-l-4 border-l-indigo-500">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Auto-booking ytelse
              </CardTitle>
              <CheckCircle2 className="w-5 h-5 text-indigo-500" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-3xl font-bold text-foreground">
                {auto_booking_performance.rate.toFixed(1)}%
              </div>
              <p className="text-sm text-muted-foreground">
                {auto_booking_performance.description}
              </p>
              <div className="text-xs text-muted-foreground mt-2">
                {auto_booking_performance.auto_approved_30d} av {auto_booking_performance.total_invoices_30d} fakturaer
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Hurtighandlinger</CardTitle>
          <CardDescription>Hopp direkte til viktige oppgaver</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {metrics.quick_actions.map((action, index) => (
              <Button
                key={index}
                variant="outline"
                className="h-auto py-4 px-6 justify-between"
                onClick={() => router.push(action.url)}
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{action.icon}</span>
                  <span className="font-medium">{action.label}</span>
                </div>
                <div className="flex items-center gap-2">
                  {action.badge !== null && action.badge > 0 && (
                    <Badge variant="destructive" className="rounded-full">
                      {action.badge}
                    </Badge>
                  )}
                  <ArrowRight className="w-4 h-4" />
                </div>
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Last updated timestamp */}
      <div className="text-xs text-muted-foreground text-center">
        Sist oppdatert: {new Date(metrics.timestamp).toLocaleString('nb-NO')}
      </div>
    </div>
  );
}
