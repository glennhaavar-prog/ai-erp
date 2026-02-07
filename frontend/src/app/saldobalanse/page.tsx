'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Alert,
  Stack,
  Chip,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs, { Dayjs } from 'dayjs';
import DownloadIcon from '@mui/icons-material/Download';
import FilterListIcon from '@mui/icons-material/FilterList';
import { useClient } from '@/contexts/ClientContext';

interface AccountBalance {
  account_code: string;
  account_name: string;
  account_type: string;
  opening_balance: number;
  current_balance: number;
  balance_change: number;
}

interface SaldobalanseResponse {
  client_id: string;
  client_name: string;
  from_date: string;
  to_date: string;
  account_class: string | null;
  balances: AccountBalance[];
  total_opening_balance: number;
  total_current_balance: number;
  total_change: number;
}

export default function SaldobalansePage() {
  const { selectedClient: contextClient, isLoading: clientLoading } = useClient();
  const [fromDate, setFromDate] = useState<Dayjs | null>(dayjs('2026-01-01'));
  const [toDate, setToDate] = useState<Dayjs | null>(dayjs());
  const [accountClass, setAccountClass] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<SaldobalanseResponse | null>(null);

  const accountClasses = [
    { value: '', label: 'Alle kontoklasser' },
    { value: '1', label: '1 - Eiendeler' },
    { value: '2', label: '2 - Egenkapital og gjeld' },
    { value: '3', label: '3 - Driftsinntekter' },
    { value: '4', label: '4 - Varekostnad' },
    { value: '5', label: '5 - Lønnskostnad' },
    { value: '6', label: '6 - Annen driftskostnad' },
    { value: '7', label: '7 - Finansinntekter og -kostnader' },
    { value: '8', label: '8 - Ekstraordinære poster' },
  ];


  const fetchSaldobalanse = async () => {
    if (!contextClient) {
      setError('Vennligst velg en klient');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        client_id: contextClient.id,
        from_date: fromDate?.format('YYYY-MM-DD') || '2026-01-01',
        to_date: toDate?.format('YYYY-MM-DD') || dayjs().format('YYYY-MM-DD'),
      });

      if (accountClass) {
        params.append('account_class', accountClass);
      }

      const response = await fetch(
        `http://localhost:8000/api/reports/saldobalanse/?${params}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch saldobalanse');
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      console.error('Error fetching saldobalanse:', err);
      setError('Kunne ikke hente saldobalanserapport');
    } finally {
      setLoading(false);
    }
  };

  const exportExcel = async () => {
    if (!contextClient) return;

    try {
      const params = new URLSearchParams({
        client_id: contextClient.id,
        from_date: fromDate?.format('YYYY-MM-DD') || '2026-01-01',
        to_date: toDate?.format('YYYY-MM-DD') || dayjs().format('YYYY-MM-DD'),
      });

      if (accountClass) {
        params.append('account_class', accountClass);
      }

      const response = await fetch(
        `http://localhost:8000/api/reports/saldobalanse/export/excel/?${params}`
      );

      if (!response.ok) throw new Error('Export failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `saldobalanse_${selectedClient}_${dayjs().format('YYYY-MM-DD')}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Error exporting to Excel:', err);
      setError('Kunne ikke eksportere til Excel');
    }
  };

  const exportPDF = async () => {
    if (!contextClient) return;

    try {
      const params = new URLSearchParams({
        client_id: contextClient.id,
        from_date: fromDate?.format('YYYY-MM-DD') || '2026-01-01',
        to_date: toDate?.format('YYYY-MM-DD') || dayjs().format('YYYY-MM-DD'),
      });

      if (accountClass) {
        params.append('account_class', accountClass);
      }

      const response = await fetch(
        `http://localhost:8000/api/reports/saldobalanse/export/pdf/?${params}`
      );

      if (!response.ok) throw new Error('Export failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `saldobalanse_${selectedClient}_${dayjs().format('YYYY-MM-DD')}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Error exporting to PDF:', err);
      setError('Kunne ikke eksportere til PDF');
    }
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('nb-NO', {
      style: 'currency',
      currency: 'NOK',
    }).format(amount);
  };

  const getBalanceColor = (change: number): string => {
    if (change > 0) return 'success.main';
    if (change < 0) return 'error.main';
    return 'text.primary';
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Saldobalanserapport
        </Typography>

        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <FilterListIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Filtrering
            </Typography>

            <Stack spacing={2} direction={{ xs: 'column', md: 'row' }} sx={{ mt: 2 }}>

              <DatePicker
                label="Fra dato"
                value={fromDate}
                onChange={(newValue) => setFromDate(newValue)}
                slotProps={{ textField: { fullWidth: true } }}
              />

              <DatePicker
                label="Til dato"
                value={toDate}
                onChange={(newValue) => setToDate(newValue)}
                slotProps={{ textField: { fullWidth: true } }}
              />

              <TextField
                select
                label="Kontoklasse"
                value={accountClass}
                onChange={(e) => setAccountClass(e.target.value)}
                fullWidth
              >
                {accountClasses.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </TextField>
            </Stack>

            <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
              <Button
                variant="contained"
                onClick={fetchSaldobalanse}
                disabled={loading || !selectedClient}
              >
                Hent rapport
              </Button>
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={exportExcel}
                disabled={!data}
              >
                Excel
              </Button>
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={exportPDF}
                disabled={!data}
              >
                PDF
              </Button>
            </Stack>
          </CardContent>
        </Card>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {data && !loading && (
          <>
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h6">{data.client_name}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Periode: {data.from_date} til {data.to_date}
                  {data.account_class && ` | Kontoklasse: ${data.account_class}`}
                </Typography>
                <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
                  <Chip
                    label={`Inngående balanse: ${formatCurrency(data.total_opening_balance)}`}
                    color="default"
                  />
                  <Chip
                    label={`Nåværende balanse: ${formatCurrency(data.total_current_balance)}`}
                    color="primary"
                  />
                  <Chip
                    label={`Endring: ${formatCurrency(data.total_change)}`}
                    color={data.total_change >= 0 ? 'success' : 'error'}
                  />
                </Stack>
              </CardContent>
            </Card>

            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Konto</TableCell>
                    <TableCell>Kontonavn</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell align="right">Inngående balanse</TableCell>
                    <TableCell align="right">Nåværende balanse</TableCell>
                    <TableCell align="right">Endring</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.balances.map((balance) => (
                    <TableRow key={balance.account_code} hover>
                      <TableCell>{balance.account_code}</TableCell>
                      <TableCell>{balance.account_name}</TableCell>
                      <TableCell>{balance.account_type}</TableCell>
                      <TableCell align="right">
                        {formatCurrency(balance.opening_balance)}
                      </TableCell>
                      <TableCell align="right">
                        <strong>{formatCurrency(balance.current_balance)}</strong>
                      </TableCell>
                      <TableCell
                        align="right"
                        sx={{ color: getBalanceColor(balance.balance_change) }}
                      >
                        <strong>{formatCurrency(balance.balance_change)}</strong>
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow sx={{ bgcolor: 'action.hover' }}>
                    <TableCell colSpan={3}>
                      <strong>TOTALT</strong>
                    </TableCell>
                    <TableCell align="right">
                      <strong>{formatCurrency(data.total_opening_balance)}</strong>
                    </TableCell>
                    <TableCell align="right">
                      <strong>{formatCurrency(data.total_current_balance)}</strong>
                    </TableCell>
                    <TableCell
                      align="right"
                      sx={{ color: getBalanceColor(data.total_change) }}
                    >
                      <strong>{formatCurrency(data.total_change)}</strong>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </>
        )}
      </Box>
    </LocalizationProvider>
  );
}
