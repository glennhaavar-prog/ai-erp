'use client';

import React, { useState, useEffect } from 'react';
import { useClient } from '@/contexts/ClientContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Search,
  History,
  Download,
  Trash2,
  Lightbulb,
  Info,
  Loader2,
} from 'lucide-react';

interface NLQResult {
  success: boolean;
  question: string;
  sql?: string;
  results?: any[];
  count?: number;
  error?: string;
}

interface QueryHistory {
  id: string;
  question: string;
  timestamp: Date;
  count?: number;
}

const EXAMPLE_QUERIES = [
  'Vis meg alle fakturaer over 10 000 kr',
  'Hva er min totale omsetning siste måned?',
  'List opp ubetalte leverandørfakturaer',
  'Hvilke kunder har ikke betalt ennå?',
  'Vis transaksjoner siste 30 dager',
  'Hvor mye MVA har vi betalt i år?',
  'Alle bilag fra Telenor',
  'Totale lønnskostnader inneværende år',
];

export default function NLQPage() {
  const { selectedClient } = useClient();
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<NLQResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<QueryHistory[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);

  // Load query history from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('nlq_history');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setHistory(parsed.map((h: any) => ({ ...h, timestamp: new Date(h.timestamp) })));
      } catch (e) {
        console.error('Failed to parse history:', e);
      }
    }
  }, []);

  // Save query to history
  const saveToHistory = (question: string, count?: number) => {
    const newEntry: QueryHistory = {
      id: Date.now().toString(),
      question,
      timestamp: new Date(),
      count,
    };
    const updated = [newEntry, ...history].slice(0, 20); // Keep last 20
    setHistory(updated);
    localStorage.setItem('nlq_history', JSON.stringify(updated));
  };

  // Execute NLQ query
  const handleQuery = async (queryText?: string) => {
    const q = queryText || question;
    if (!q.trim()) {
      setError('Vennligst skriv inn et spørsmål');
      return;
    }

    if (!selectedClient?.id) {
      setError('Vennligst velg en klient først');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE}/api/nlq/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: q,
          client_id: selectedClient.id,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Forespørselen feilet');
      }

      setResult(data);
      saveToHistory(q, data.count);
      if (!queryText) setQuestion(''); // Only clear if not from example/history
    } catch (err: any) {
      console.error('NLQ Error:', err);
      setError(err.message || 'Noe gikk galt. Prøv igjen.');
    } finally {
      setLoading(false);
    }
  };

  // Export to CSV
  const exportToCSV = () => {
    if (!result?.results || result.results.length === 0) return;

    const headers = Object.keys(result.results[0]);
    const csvContent = [
      headers.join(','),
      ...result.results.map((row) =>
        headers.map((h) => `"${row[h] ?? ''}"`).join(',')
      ),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `nlq_resultat_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    setShowExportMenu(false);
  };

  // Export to Excel (simple TSV format that Excel can open)
  const exportToExcel = () => {
    if (!result?.results || result.results.length === 0) return;

    const headers = Object.keys(result.results[0]);
    const tsvContent = [
      headers.join('\t'),
      ...result.results.map((row) =>
        headers.map((h) => row[h] ?? '').join('\t')
      ),
    ].join('\n');

    const blob = new Blob([tsvContent], { type: 'application/vnd.ms-excel' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `nlq_resultat_${new Date().toISOString().split('T')[0]}.xls`;
    link.click();
    setShowExportMenu(false);
  };

  // Clear history
  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem('nlq_history');
  };

  // Render results table
  const renderResults = () => {
    if (!result?.results || result.results.length === 0) {
      return (
        <Alert className="mt-4">
          <AlertDescription>Ingen resultater funnet</AlertDescription>
        </Alert>
      );
    }

    const headers = Object.keys(result.results[0]);

    return (
      <div className="mt-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">
            Resultater ({result.count} rader)
          </h3>
          <div className="relative">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowExportMenu(!showExportMenu)}
            >
              <Download className="h-4 w-4 mr-2" />
              Eksporter
            </Button>
            {showExportMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-background border rounded-md shadow-lg z-10">
                <button
                  onClick={exportToCSV}
                  className="w-full px-4 py-2 text-left hover:bg-accent flex items-center"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Last ned som CSV
                </button>
                <button
                  onClick={exportToExcel}
                  className="w-full px-4 py-2 text-left hover:bg-accent flex items-center"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Last ned som Excel
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="border rounded-md max-h-[500px] overflow-auto">
          <Table>
            <TableHeader>
              <TableRow>
                {headers.map((header) => (
                  <TableHead key={header} className="font-semibold">
                    {header}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {result.results.map((row, idx) => (
                <TableRow key={idx}>
                  {headers.map((header) => (
                    <TableCell key={header}>
                      {row[header] !== null && row[header] !== undefined
                        ? String(row[header])
                        : '-'}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* SQL Query Display */}
        {result.sql && (
          <div className="mt-4 p-4 border rounded-md bg-muted">
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
              <Info className="h-4 w-4" />
              Generert SQL-spørring
            </div>
            <pre className="text-xs font-mono overflow-x-auto">
              {result.sql}
            </pre>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Naturlig Språk Spørring</h1>
        <p className="text-muted-foreground">
          Still spørsmål om regnskapsdata på norsk. AI-en vil konvertere til SQL og hente resultater.
        </p>
      </div>

      {/* Main Query Card */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="space-y-4">
            {/* Query Input */}
            <textarea
              className="w-full min-h-[80px] p-3 border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Eksempel: Vis meg alle fakturaer over 10 000 kr fra siste måned"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleQuery();
                }
              }}
              disabled={loading}
            />

            {/* Action Buttons */}
            <div className="flex justify-between items-center">
              <Button
                size="lg"
                onClick={() => handleQuery()}
                disabled={loading || !question.trim()}
                className="min-w-[150px]"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Søker...
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4 mr-2" />
                    Spør
                  </>
                )}
              </Button>

              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowHistory(!showHistory)}
              >
                <History className="h-4 w-4 mr-2" />
                {showHistory ? 'Skjul' : 'Vis'} historikk ({history.length})
              </Button>
            </div>

            {/* Error Display */}
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Query History */}
      {showHistory && history.length > 0 && (
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Spørsmålshistorikk</h3>
              <Button
                variant="destructive"
                size="sm"
                onClick={clearHistory}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Tøm historikk
              </Button>
            </div>
            <div className="space-y-2">
              {history.map((item) => (
                <div
                  key={item.id}
                  className="p-3 border rounded-md cursor-pointer hover:bg-accent transition-colors"
                  onClick={() => {
                    setQuestion(item.question);
                    handleQuery(item.question);
                  }}
                >
                  <div className="flex justify-between items-center">
                    <p className="flex-1">{item.question}</p>
                    <div className="flex items-center gap-2">
                      {item.count !== undefined && (
                        <Badge variant="secondary">{item.count} rader</Badge>
                      )}
                      <span className="text-xs text-muted-foreground">
                        {item.timestamp.toLocaleString('no-NO', {
                          day: '2-digit',
                          month: '2-digit',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Example Queries */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 mb-4">
            <Lightbulb className="h-5 w-5 text-yellow-500" />
            <h3 className="text-lg font-semibold">Eksempelspørsmål</h3>
          </div>
          <p className="text-sm text-muted-foreground mb-4">
            Klikk på et eksempel for å prøve det:
          </p>
          <div className="flex flex-wrap gap-2">
            {EXAMPLE_QUERIES.map((example, idx) => (
              <Badge
                key={idx}
                variant="outline"
                className="cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors"
                onClick={() => {
                  setQuestion(example);
                  handleQuery(example);
                }}
              >
                {example}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <Card>
          <CardContent className="pt-6">
            {result.success ? (
              renderResults()
            ) : (
              <Alert variant="destructive">
                <AlertDescription>
                  {result.error || 'Forespørselen feilet'}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!result && !error && !loading && (
        <div className="p-12 text-center border rounded-lg bg-muted/50">
          <Search className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-semibold mb-2">Ingen søk utført ennå</h3>
          <p className="text-sm text-muted-foreground">
            Still et spørsmål ovenfor eller velg et eksempel for å komme i gang
          </p>
        </div>
      )}
    </div>
  );
}
