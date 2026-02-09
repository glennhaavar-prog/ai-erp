'use client';

import { useState, useEffect } from 'react';
// import { useClientContext } from '@/contexts/ClientContext';

interface PeriodCloseCheck {
  name: string;
  status: 'passed' | 'failed' | 'warning';
  message: string;
  posted_count?: number;
  amount?: number;
  diff?: number;
  entry_count?: number;
}

interface PeriodCloseResult {
  period: string;
  status: 'running' | 'success' | 'failed';
  checks: PeriodCloseCheck[];
  warnings: string[];
  errors: string[];
  summary: string;
}

interface Period {
  year: number;
  month: number;
  label: string;
  status: 'open' | 'closed';
}

export default function PeriodClosePage() {
  const clientId = '1'; // Mock clientId - TODO: implement proper context
  const [selectedPeriod, setSelectedPeriod] = useState<string>('');
  const [closeResult, setCloseResult] = useState<PeriodCloseResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [periods, setPeriods] = useState<Period[]>([]);

  useEffect(() => {
    // Generate last 12 months
    const now = new Date();
    const generatedPeriods: Period[] = [];
    
    for (let i = 0; i < 12; i++) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      generatedPeriods.push({
        year: date.getFullYear(),
        month: date.getMonth() + 1,
        label: date.toLocaleDateString('nb-NO', { month: 'long', year: 'numeric' }),
        status: 'open' // We'll check this from API later
      });
    }
    
    setPeriods(generatedPeriods);
    
    // Set default to last month
    if (generatedPeriods.length > 1) {
      const lastMonth = generatedPeriods[1];
      setSelectedPeriod(`${lastMonth.year}-${String(lastMonth.month).padStart(2, '0')}`);
    }
  }, []);

  const handleClosePeriod = async () => {
    if (!selectedPeriod || !clientId) return;
    
    setLoading(true);
    setCloseResult(null);
    
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/period-close/run`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            client_id: clientId,
            period: selectedPeriod
          })
        }
      );
      
      const data = await response.json();
      setCloseResult(data);
    } catch (error) {
      console.error('Failed to close period:', error);
      setCloseResult({
        period: selectedPeriod,
        status: 'failed',
        checks: [],
        warnings: [],
        errors: [`Nettverksfeil: ${error}`],
        summary: 'Kunne ikke lukke periode'
      });
    } finally {
      setLoading(false);
    }
  };

  const getCheckIcon = (status: string) => {
    switch (status) {
      case 'passed':
        return '✅';
      case 'failed':
        return '❌';
      case 'warning':
        return '⚠️';
      default:
        return '⏳';
    }
  };

  const getCheckColor = (status: string) => {
    switch (status) {
      case 'passed':
        return 'text-green-400 bg-green-500/10 border-green-500/20';
      case 'failed':
        return 'text-red-400 bg-red-500/10 border-red-500/20';
      case 'warning':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
      default:
        return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
    }
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('nb-NO', {
      style: 'currency',
      currency: 'NOK',
      minimumFractionDigits: 2
    }).format(amount);
  };

  return (
    <div className="p-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text-primary mb-2">
          Månedsavslutning
        </h1>
        <p className="text-text-secondary">
          Automatisert periodeavslutning med validering og kontroll
        </p>
      </div>

      {/* Period Selection */}
      <div className="bg-bg-secondary rounded-xl border border-border p-6 mb-6">
        <h2 className="text-xl font-bold text-text-primary mb-4">
          Velg periode
        </h2>
        
        <div className="flex items-center gap-4 mb-6">
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="flex-1 px-4 py-3 bg-bg-primary border border-border rounded-lg text-text-primary text-lg font-medium"
            disabled={loading}
          >
            <option value="">Velg periode...</option>
            {periods.map((period) => {
              const value = `${period.year}-${String(period.month).padStart(2, '0')}`;
              return (
                <option key={value} value={value}>
                  {period.label}
                  {period.status === 'closed' && ' (Lukket)'}
                </option>
              );
            })}
          </select>
          
          <button
            onClick={handleClosePeriod}
            disabled={!selectedPeriod || loading}
            className={`px-6 py-3 rounded-lg font-medium text-lg transition-colors ${
              !selectedPeriod || loading
                ? 'bg-bg-primary text-text-muted cursor-not-allowed'
                : 'bg-accent-blue hover:bg-accent-blue-bright text-white'
            }`}
          >
            {loading ? 'Lukker periode...' : 'Lukk periode'}
          </button>
        </div>

        <div className="bg-bg-primary rounded-lg p-4 border border-border">
          <h3 className="font-semibold text-text-primary mb-2">
            Hva skjer ved periodeavslutning?
          </h3>
          <ul className="text-sm text-text-muted space-y-1.5">
            <li>✓ Kontrollerer at alle posteringer balanserer (debet = kredit)</li>
            <li>✓ Bokfører ventende periodiseringer for perioden</li>
            <li>✓ Låser perioden for nye posteringer</li>
            <li>✓ Genererer avslutningsrapport</li>
          </ul>
        </div>
      </div>

      {/* Results */}
      {closeResult && (
        <div className="space-y-6">
          {/* Summary Card */}
          <div className={`rounded-xl border-2 p-6 ${
            closeResult.status === 'success'
              ? 'bg-green-500/5 border-green-500/30'
              : closeResult.status === 'failed'
              ? 'bg-red-500/5 border-red-500/30'
              : 'bg-blue-500/5 border-blue-500/30'
          }`}>
            <div className="flex items-start gap-4">
              <div className="text-4xl">
                {closeResult.status === 'success' ? '✅' : closeResult.status === 'failed' ? '❌' : '⏳'}
              </div>
              <div className="flex-1">
                <h2 className={`text-2xl font-bold mb-2 ${
                  closeResult.status === 'success'
                    ? 'text-green-400'
                    : closeResult.status === 'failed'
                    ? 'text-red-400'
                    : 'text-blue-400'
                }`}>
                  {closeResult.status === 'success' && 'Periode lukket'}
                  {closeResult.status === 'failed' && 'Kunne ikke lukke periode'}
                  {closeResult.status === 'running' && 'Lukker periode...'}
                </h2>
                <p className="text-text-primary text-lg">
                  {closeResult.summary}
                </p>
              </div>
            </div>
          </div>

          {/* Checks */}
          <div className="bg-bg-secondary rounded-xl border border-border p-6">
            <h2 className="text-xl font-bold text-text-primary mb-4">
              Kontroller ({closeResult.checks.length})
            </h2>
            
            <div className="space-y-3">
              {closeResult.checks.map((check, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-lg border ${getCheckColor(check.status)}`}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">{getCheckIcon(check.status)}</span>
                    <div className="flex-1">
                      <h3 className="font-semibold text-text-primary mb-1">
                        {check.name}
                      </h3>
                      <p className="text-sm text-text-muted">
                        {check.message}
                      </p>
                      
                      {/* Additional info for specific checks */}
                      {check.posted_count !== undefined && check.posted_count > 0 && (
                        <div className="mt-2 text-sm">
                          <span className="text-text-secondary">
                            Bokført: {check.posted_count} posteringer
                          </span>
                          {check.amount !== undefined && (
                            <span className="ml-3 text-accent-blue font-semibold">
                              {formatAmount(check.amount)}
                            </span>
                          )}
                        </div>
                      )}
                      
                      {check.entry_count !== undefined && (
                        <div className="mt-2 text-sm text-text-secondary">
                          {check.entry_count} bilag kontrollert
                        </div>
                      )}
                      
                      {check.diff !== undefined && check.diff !== 0 && (
                        <div className="mt-2 text-sm font-mono text-red-400">
                          Differanse: {formatAmount(check.diff)}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Warnings */}
          {closeResult.warnings.length > 0 && (
            <div className="bg-amber-500/5 rounded-xl border border-amber-500/30 p-6">
              <h2 className="text-xl font-bold text-amber-400 mb-4 flex items-center gap-2">
                <span>⚠️</span>
                Advarsler ({closeResult.warnings.length})
              </h2>
              <ul className="space-y-2">
                {closeResult.warnings.map((warning, index) => (
                  <li key={index} className="text-text-muted flex items-start gap-2">
                    <span className="text-amber-400">•</span>
                    <span>{warning}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Errors */}
          {closeResult.errors.length > 0 && (
            <div className="bg-red-500/5 rounded-xl border border-red-500/30 p-6">
              <h2 className="text-xl font-bold text-red-400 mb-4 flex items-center gap-2">
                <span>❌</span>
                Feil ({closeResult.errors.length})
              </h2>
              <ul className="space-y-2">
                {closeResult.errors.map((error, index) => (
                  <li key={index} className="text-text-muted flex items-start gap-2">
                    <span className="text-red-400">•</span>
                    <span>{error}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Info Section */}
      {!closeResult && !loading && (
        <div className="bg-bg-secondary rounded-xl border border-border p-6">
          <h2 className="text-xl font-bold text-text-primary mb-4">
            Om periodeavslutning
          </h2>
          
          <div className="space-y-4 text-text-secondary">
            <p>
              Periodeavslutning er en viktig del av regnskapsrutinene. Den sikrer at:
            </p>
            
            <ul className="space-y-2 ml-4">
              <li className="flex items-start gap-2">
                <span className="text-accent-blue">•</span>
                <span>Alle posteringer for perioden er korrekt bokført</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-accent-blue">•</span>
                <span>Periodiseringer er automatisk bokført på riktig tidspunkt</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-accent-blue">•</span>
                <span>Perioden låses for å forhindre etterfølgende endringer</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-accent-blue">•</span>
                <span>Regnskapet er klart for rapportering og analyse</span>
              </li>
            </ul>
            
            <div className="mt-6 p-4 bg-blue-500/5 border border-blue-500/20 rounded-lg">
              <h3 className="font-semibold text-accent-blue mb-2">
                💡 Tips
              </h3>
              <p className="text-sm text-text-muted">
                Vi anbefaler å lukke perioder månedlig, helst innen 10. dag i påfølgende måned.
                Dette gir bedre kontroll og gjør rapportering enklere.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
