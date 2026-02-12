/**
 * Åpningsbalanse Import Wizard
 * CSV/Excel upload or manual entry with validation and balance check
 */
'use client';

export const dynamic = 'force-dynamic';

import { GetServerSideProps } from 'next';
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { useClient } from '@/contexts/ClientContext';
import {
  openingBalanceApi,
  OpeningBalance,
  OpeningBalanceLine,
  ValidationError as APIValidationError,
  BankBalanceVerification,
} from '@/api/opening-balance';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ArrowUpTrayIcon,
  PlusIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';

type WizardStep = 'upload' | 'preview' | 'validate' | 'complete';

export const AapningsbalanseImport: React.FC = () => {
  const { selectedClient } = useClient();
  const [step, setStep] = useState<WizardStep>('upload');
  const [accountingDate, setAccountingDate] = useState('');
  const [lines, setLines] = useState<OpeningBalanceLine[]>([]);
  const [openingBalance, setOpeningBalance] = useState<OpeningBalance | null>(null);
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    errors: APIValidationError[];
    warnings: APIValidationError[];
    bank_verifications: BankBalanceVerification[];
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [existingBalances, setExistingBalances] = useState<OpeningBalance[]>([]);

  useEffect(() => {
    if (selectedClient?.id) {
      fetchExistingBalances();
    }
  }, [selectedClient]);

  const fetchExistingBalances = async () => {
    if (!selectedClient?.id) return;

    try {
      const data = await openingBalanceApi.list(selectedClient.id, { limit: 20 });
      setExistingBalances(data);
    } catch (error) {
      console.error('Error fetching existing balances:', error);
    }
  };

  const handleCSVUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !selectedClient?.id) return;

    if (!accountingDate) {
      toast.error('Vennligst velg regnskapsdato først');
      return;
    }

    try {
      setLoading(true);
      const data = await openingBalanceApi.uploadCSV(selectedClient.id, file, accountingDate);
      setOpeningBalance(data);
      setStep('preview');
      toast.success('CSV lastet opp');
    } catch (error: any) {
      console.error('Error uploading CSV:', error);
      const errorMessage = error.response?.data?.detail || 'Kunne ikke laste opp CSV';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleManualEntry = () => {
    if (!accountingDate) {
      toast.error('Vennligst velg regnskapsdato først');
      return;
    }

    // Initialize with one empty line
    setLines([
      {
        line_number: 1,
        account_number: '',
        account_name: '',
        debit_amount: 0,
        credit_amount: 0,
        description: '',
      },
    ]);
    setStep('preview');
  };

  const addLine = () => {
    setLines([
      ...lines,
      {
        line_number: lines.length + 1,
        account_number: '',
        account_name: '',
        debit_amount: 0,
        credit_amount: 0,
        description: '',
      },
    ]);
  };

  const updateLine = (index: number, field: keyof OpeningBalanceLine, value: any) => {
    const updated = [...lines];
    updated[index] = { ...updated[index], [field]: value };
    setLines(updated);
  };

  const removeLine = (index: number) => {
    const updated = lines.filter((_, i) => i !== index);
    // Renumber lines
    updated.forEach((line, i) => {
      line.line_number = i + 1;
    });
    setLines(updated);
  };

  const calculateTotals = () => {
    const totalDebit = lines.reduce((sum, line) => sum + (parseFloat(String(line.debit_amount)) || 0), 0);
    const totalCredit = lines.reduce((sum, line) => sum + (parseFloat(String(line.credit_amount)) || 0), 0);
    const difference = totalDebit - totalCredit;

    return { totalDebit, totalCredit, difference };
  };

  const handleValidate = async () => {
    if (!selectedClient?.id) return;

    // First create/update the opening balance
    try {
      setLoading(true);

      if (!openingBalance) {
        // Create new from manual entry
        const data = await openingBalanceApi.import({
          client_id: selectedClient.id,
          accounting_date: accountingDate,
          lines: lines,
        });
        setOpeningBalance(data);
      }

      // Now validate
      const validation = await openingBalanceApi.validate({
        opening_balance_id: openingBalance!.id,
      });

      setValidationResult(validation);
      setStep('validate');

      if (validation.valid) {
        toast.success('Validering OK - balansen stemmer!');
      } else {
        toast.error('Validering feilet - se feilmeldinger');
      }
    } catch (error: any) {
      console.error('Error validating:', error);
      const errorMessage = error.response?.data?.detail || 'Kunne ikke validere åpningsbalanse';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleImportToLedger = async () => {
    if (!openingBalance?.id) return;

    if (!validationResult?.valid) {
      toast.error('Kan ikke importere - valideringen er ikke OK');
      return;
    }

    try {
      setLoading(true);
      await openingBalanceApi.importToLedger({
        opening_balance_id: openingBalance.id,
        description: `Åpningsbalanse pr. ${accountingDate}`,
      });

      toast.success('Åpningsbalanse importert til hovedbok!');
      setStep('complete');
      fetchExistingBalances();
    } catch (error: any) {
      console.error('Error importing to ledger:', error);
      const errorMessage = error.response?.data?.detail || 'Kunne ikke importere til hovedbok';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setStep('upload');
    setAccountingDate('');
    setLines([]);
    setOpeningBalance(null);
    setValidationResult(null);
  };

  if (!selectedClient) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-500 dark:text-gray-400">Velg en klient for å importere åpningsbalanse</p>
      </div>
    );
  }

  const totals = step === 'preview' ? calculateTotals() : null;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Import åpningsbalanse</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Last opp CSV eller registrer manuelt
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-between">
        {['upload', 'preview', 'validate', 'complete'].map((s, index) => (
          <div key={s} className="flex items-center">
            <div
              className={`flex items-center justify-center w-10 h-10 rounded-full ${
                step === s
                  ? 'bg-blue-600 text-white'
                  : index < ['upload', 'preview', 'validate', 'complete'].indexOf(step)
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-500'
              }`}
            >
              {index + 1}
            </div>
            {index < 3 && <div className="w-24 h-1 bg-gray-200 dark:bg-gray-700" />}
          </div>
        ))}
      </div>

      {/* Step: Upload */}
      {step === 'upload' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-6">
          <div>
            <Label>Regnskapsdato *</Label>
            <Input
              type="date"
              value={accountingDate}
              onChange={(e) => setAccountingDate(e.target.value)}
            />
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Vanligvis 01.01.YYYY (starten av regnskapsåret)
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* CSV Upload */}
            <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center">
              <ArrowUpTrayIcon className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Last opp CSV/Excel
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                Format: Kontonummer, Kontonavn, Debet, Kredit
              </p>
              <input
                type="file"
                accept=".csv,.xlsx"
                onChange={handleCSVUpload}
                disabled={loading || !accountingDate}
                className="hidden"
                id="csv-upload"
              />
              <label htmlFor="csv-upload" className="cursor-pointer">
                <Button disabled={loading || !accountingDate} className="cursor-pointer">
                  {loading ? 'Laster opp...' : 'Velg fil'}
                </Button>
              </label>
            </div>

            {/* Manual Entry */}
            <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center">
              <PlusIcon className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Manuell registrering
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                Registrer hver konto manuelt
              </p>
              <Button onClick={handleManualEntry} disabled={!accountingDate}>
                Start manuell registrering
              </Button>
            </div>
          </div>

          {/* Existing Balances */}
          {existingBalances.length > 0 && (
            <div className="mt-8">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Tidligere importerte åpningsbalanser
              </h3>
              <div className="space-y-2">
                {existingBalances.map((balance) => (
                  <div
                    key={balance.id}
                    className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                  >
                    <div>
                      <p className="font-medium text-gray-900 dark:text-gray-100">
                        {new Date(balance.accounting_date).toLocaleDateString('nb-NO')}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {balance.line_count} linjer - Status: {balance.status}
                      </p>
                    </div>
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        balance.status === 'imported'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {balance.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Step: Preview */}
      {step === 'preview' && (
        <div className="space-y-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Forhåndsvisning
              </h3>
              <Button onClick={addLine} size="sm">
                <PlusIcon className="w-4 h-4 mr-2" />
                Legg til linje
              </Button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-900">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      #
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Kontonr
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Kontonavn
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Debet
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Kredit
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Beskrivelse
                    </th>
                    <th className="px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {lines.map((line, index) => (
                    <tr key={index}>
                      <td className="px-4 py-2 text-sm text-gray-900 dark:text-gray-100">
                        {line.line_number}
                      </td>
                      <td className="px-4 py-2">
                        <Input
                          value={line.account_number}
                          onChange={(e) => updateLine(index, 'account_number', e.target.value)}
                          className="w-24"
                        />
                      </td>
                      <td className="px-4 py-2">
                        <Input
                          value={line.account_name || ''}
                          onChange={(e) => updateLine(index, 'account_name', e.target.value)}
                        />
                      </td>
                      <td className="px-4 py-2">
                        <Input
                          type="number"
                          step="0.01"
                          value={line.debit_amount}
                          onChange={(e) =>
                            updateLine(index, 'debit_amount', parseFloat(e.target.value) || 0)
                          }
                          className="w-32 text-right"
                        />
                      </td>
                      <td className="px-4 py-2">
                        <Input
                          type="number"
                          step="0.01"
                          value={line.credit_amount}
                          onChange={(e) =>
                            updateLine(index, 'credit_amount', parseFloat(e.target.value) || 0)
                          }
                          className="w-32 text-right"
                        />
                      </td>
                      <td className="px-4 py-2">
                        <Input
                          value={line.description || ''}
                          onChange={(e) => updateLine(index, 'description', e.target.value)}
                        />
                      </td>
                      <td className="px-4 py-2">
                        <button
                          onClick={() => removeLine(index)}
                          className="text-red-600 hover:text-red-800"
                        >
                          <TrashIcon className="w-5 h-5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-gray-50 dark:bg-gray-900 font-semibold">
                  <tr>
                    <td colSpan={3} className="px-4 py-3 text-right text-gray-900 dark:text-gray-100">
                      Sum:
                    </td>
                    <td className="px-4 py-3 text-right text-gray-900 dark:text-gray-100">
                      {totals?.totalDebit.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-900 dark:text-gray-100">
                      {totals?.totalCredit.toFixed(2)}
                    </td>
                    <td colSpan={2}></td>
                  </tr>
                  <tr>
                    <td colSpan={3} className="px-4 py-3 text-right text-gray-900 dark:text-gray-100">
                      Differanse:
                    </td>
                    <td
                      colSpan={2}
                      className={`px-4 py-3 text-right ${
                        totals?.difference === 0
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}
                    >
                      {totals?.difference.toFixed(2)}
                    </td>
                    <td colSpan={2}></td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          <div className="flex justify-between">
            <Button variant="outline" onClick={handleReset}>
              Avbryt
            </Button>
            <Button onClick={handleValidate} disabled={loading || lines.length === 0}>
              {loading ? 'Validerer...' : 'Neste: Validering'}
            </Button>
          </div>
        </div>
      )}

      {/* Step: Validate */}
      {step === 'validate' && validationResult && (
        <div className="space-y-4">
          {/* Balance Check */}
          <div
            className={`p-6 rounded-lg border-2 ${
              validationResult.valid
                ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                : 'border-red-500 bg-red-50 dark:bg-red-900/20'
            }`}
          >
            <div className="flex items-center gap-4">
              {validationResult.valid ? (
                <CheckCircleIcon className="w-12 h-12 text-green-600" />
              ) : (
                <XCircleIcon className="w-12 h-12 text-red-600" />
              )}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {validationResult.valid ? 'Validering OK!' : 'Validering feilet'}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {validationResult.valid
                    ? 'Balansen stemmer og kan importeres til hovedbok'
                    : 'Vennligst rett feilene før import'}
                </p>
              </div>
            </div>
          </div>

          {/* Errors */}
          {validationResult.errors.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-red-300 dark:border-red-700 p-4">
              <h4 className="font-semibold text-red-600 dark:text-red-400 mb-3 flex items-center gap-2">
                <XCircleIcon className="w-5 h-5" />
                Feil ({validationResult.errors.length})
              </h4>
              <ul className="space-y-2">
                {validationResult.errors.map((error, index) => (
                  <li key={index} className="text-sm text-gray-700 dark:text-gray-300">
                    <span className="font-medium">{error.code}:</span> {error.message}
                    {error.line_number && <span className="text-gray-500"> (Linje {error.line_number})</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Warnings */}
          {validationResult.warnings.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-yellow-300 dark:border-yellow-700 p-4">
              <h4 className="font-semibold text-yellow-600 dark:text-yellow-400 mb-3 flex items-center gap-2">
                <ExclamationTriangleIcon className="w-5 h-5" />
                Advarsler ({validationResult.warnings.length})
              </h4>
              <ul className="space-y-2">
                {validationResult.warnings.map((warning, index) => (
                  <li key={index} className="text-sm text-gray-700 dark:text-gray-300">
                    <span className="font-medium">{warning.code}:</span> {warning.message}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Bank Verifications */}
          {validationResult.bank_verifications.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Bankkontoer
              </h4>
              <div className="space-y-2">
                {validationResult.bank_verifications.map((bank, index) => (
                  <div
                    key={index}
                    className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded"
                  >
                    <div>
                      <p className="font-medium text-gray-900 dark:text-gray-100">
                        {bank.account_number} - {bank.account_name}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Balanse i import: {bank.balance_in_import.toFixed(2)} NOK
                      </p>
                    </div>
                    {bank.verified ? (
                      <CheckCircleIcon className="w-6 h-6 text-green-600" />
                    ) : (
                      <ExclamationTriangleIcon className="w-6 h-6 text-yellow-600" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-between">
            <Button variant="outline" onClick={() => setStep('preview')}>
              Tilbake
            </Button>
            <Button
              onClick={handleImportToLedger}
              disabled={!validationResult.valid || loading}
            >
              {loading ? 'Importerer...' : 'Importer til hovedbok'}
            </Button>
          </div>
        </div>
      )}

      {/* Step: Complete */}
      {step === 'complete' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8 text-center">
          <CheckCircleIcon className="w-16 h-16 text-green-600 mx-auto mb-4" />
          <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Import fullført!
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Åpningsbalansen er nå importert til hovedbok
          </p>
          <Button onClick={handleReset}>Importer ny åpningsbalanse</Button>
        </div>
      )}
    </div>
  );
};

export const getServerSideProps: GetServerSideProps = async () => {
  return {
    props: {},
  };
};

export default AapningsbalanseImport;
