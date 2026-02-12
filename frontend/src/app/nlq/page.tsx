'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Alert,
  Stack,
  CircularProgress,
  Paper,
  Chip,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider,
  Menu,
  MenuItem,
  Tooltip,
} from '@mui/material';
import { useClient } from '@/contexts/ClientContext';
import SearchIcon from '@mui/icons-material/Search';
import HistoryIcon from '@mui/icons-material/History';
import DownloadIcon from '@mui/icons-material/Download';
import SaveIcon from '@mui/icons-material/Save';
import DeleteIcon from '@mui/icons-material/Delete';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

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
  const [exportAnchor, setExportAnchor] = useState<null | HTMLElement>(null);

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
    setExportAnchor(null);
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
    setExportAnchor(null);
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
        <Alert severity="info" sx={{ mt: 2 }}>
          Ingen resultater funnet
        </Alert>
      );
    }

    const headers = Object.keys(result.results[0]);

    return (
      <Box sx={{ mt: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ color: 'text.primary' }}>
            Resultater ({result.count} rader)
          </Typography>
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              size="small"
              startIcon={<DownloadIcon />}
              onClick={(e) => setExportAnchor(e.currentTarget)}
            >
              Eksporter
            </Button>
          </Stack>
        </Box>

        {/* Export Menu */}
        <Menu
          anchorEl={exportAnchor}
          open={Boolean(exportAnchor)}
          onClose={() => setExportAnchor(null)}
        >
          <MenuItem onClick={exportToCSV}>
            <DownloadIcon sx={{ mr: 1 }} fontSize="small" />
            Last ned som CSV
          </MenuItem>
          <MenuItem onClick={exportToExcel}>
            <DownloadIcon sx={{ mr: 1 }} fontSize="small" />
            Last ned som Excel
          </MenuItem>
        </Menu>

        <TableContainer component={Paper} sx={{ maxHeight: 500 }}>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                {headers.map((header) => (
                  <TableCell
                    key={header}
                    sx={{
                      fontWeight: 600,
                      backgroundColor: 'primary.main',
                      color: 'primary.contrastText',
                    }}
                  >
                    {header}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {result.results.map((row, idx) => (
                <TableRow key={idx} hover>
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
        </TableContainer>

        {/* SQL Query Display (collapsed by default) */}
        {result.sql && (
          <Paper sx={{ mt: 2, p: 2, backgroundColor: 'grey.50' }}>
            <Typography variant="caption" sx={{ color: 'text.secondary', display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <InfoOutlinedIcon fontSize="small" />
              Generert SQL-spørring
            </Typography>
            <Typography
              variant="body2"
              component="pre"
              sx={{
                fontFamily: 'monospace',
                fontSize: '0.75rem',
                overflowX: 'auto',
                mt: 1,
                color: 'text.primary',
              }}
            >
              {result.sql}
            </Typography>
          </Paper>
        )}
      </Box>
    );
  };

  return (
    <Box sx={{ p: 3, maxWidth: 1400, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 1, color: 'text.primary' }}>
          Naturlig Språk Spørring
        </Typography>
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          Still spørsmål om regnskapsdata på norsk. AI-en vil konvertere til SQL og hente resultater.
        </Typography>
      </Box>

      {/* Main Query Card */}
      <Card sx={{ mb: 3, boxShadow: 3 }}>
        <CardContent>
          <Stack spacing={2}>
            {/* Query Input */}
            <TextField
              fullWidth
              multiline
              rows={2}
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
              variant="outlined"
              sx={{
                '& .MuiOutlinedInput-root': {
                  fontSize: '1rem',
                },
              }}
            />

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Button
                variant="contained"
                size="large"
                startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
                onClick={() => handleQuery()}
                disabled={loading || !question.trim()}
                sx={{ minWidth: 150 }}
              >
                {loading ? 'Søker...' : 'Spør'}
              </Button>

              <Button
                variant="text"
                size="small"
                startIcon={<HistoryIcon />}
                onClick={() => setShowHistory(!showHistory)}
              >
                {showHistory ? 'Skjul' : 'Vis'} historikk ({history.length})
              </Button>
            </Box>

            {/* Error Display */}
            {error && (
              <Alert severity="error" onClose={() => setError(null)}>
                {error}
              </Alert>
            )}
          </Stack>
        </CardContent>
      </Card>

      {/* Query History */}
      {showHistory && history.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ color: 'text.primary' }}>
                Spørsmålshistorikk
              </Typography>
              <Button
                size="small"
                startIcon={<DeleteIcon />}
                onClick={clearHistory}
                color="error"
              >
                Tøm historikk
              </Button>
            </Box>
            <Stack spacing={1}>
              {history.map((item) => (
                <Paper
                  key={item.id}
                  sx={{
                    p: 2,
                    cursor: 'pointer',
                    '&:hover': { backgroundColor: 'action.hover' },
                  }}
                  onClick={() => {
                    setQuestion(item.question);
                    handleQuery(item.question);
                  }}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" sx={{ flex: 1, color: 'text.primary' }}>
                      {item.question}
                    </Typography>
                    <Stack direction="row" spacing={1} alignItems="center">
                      {item.count !== undefined && (
                        <Chip label={`${item.count} rader`} size="small" color="primary" />
                      )}
                      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                        {item.timestamp.toLocaleString('no-NO', {
                          day: '2-digit',
                          month: '2-digit',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </Typography>
                    </Stack>
                  </Box>
                </Paper>
              ))}
            </Stack>
          </CardContent>
        </Card>
      )}

      {/* Example Queries */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <LightbulbIcon sx={{ color: 'warning.main' }} />
            <Typography variant="h6" sx={{ color: 'text.primary' }}>
              Eksempelspørsmål
            </Typography>
          </Box>
          <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>
            Klikk på et eksempel for å prøve det:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {EXAMPLE_QUERIES.map((example, idx) => (
              <Chip
                key={idx}
                label={example}
                onClick={() => {
                  setQuestion(example);
                  handleQuery(example);
                }}
                clickable
                color="primary"
                variant="outlined"
                sx={{ cursor: 'pointer' }}
              />
            ))}
          </Box>
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <Card>
          <CardContent>
            {result.success ? (
              renderResults()
            ) : (
              <Alert severity="error">
                {result.error || 'Forespørselen feilet'}
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!result && !error && !loading && (
        <Paper
          sx={{
            p: 6,
            textAlign: 'center',
            backgroundColor: 'grey.50',
          }}
        >
          <SearchIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" sx={{ color: 'text.secondary', mb: 1 }}>
            Ingen søk utført ennå
          </Typography>
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
            Still et spørsmål ovenfor eller velg et eksempel for å komme i gang
          </Typography>
        </Paper>
      )}
    </Box>
  );
}
