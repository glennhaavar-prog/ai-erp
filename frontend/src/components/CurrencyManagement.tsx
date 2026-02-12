/**
 * Currency Management Component
 * Manage multi-currency support, exchange rates, and auto-updates
 */
'use client';

import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { ArrowPathIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';

interface CurrencyRate {
  rate: number;
  date: string;
  source: string;
}

interface LatestRates {
  [currency: string]: CurrencyRate;
}

interface CurrencyManagementProps {
  supportedCurrencies: string[];
  autoUpdateRates: boolean;
  lastRateUpdate: string | null;
  onUpdate: (data: {
    supported_currencies: string[];
    auto_update_rates: boolean;
  }) => void;
}

const AVAILABLE_CURRENCIES = [
  { code: 'USD', name: 'US Dollar', flag: '🇺🇸', source: 'Norges Bank' },
  { code: 'EUR', name: 'Euro', flag: '🇪🇺', source: 'Norges Bank' },
  { code: 'SEK', name: 'Swedish Krona', flag: '🇸🇪', source: 'Norges Bank' },
  { code: 'DKK', name: 'Danish Krone', flag: '🇩🇰', source: 'Norges Bank' },
  { code: 'BTC', name: 'Bitcoin', flag: '₿', source: 'CoinGecko' },
];

export const CurrencyManagement: React.FC<CurrencyManagementProps> = ({
  supportedCurrencies = ['NOK'],
  autoUpdateRates = true,
  lastRateUpdate = null,
  onUpdate,
}) => {
  const [rates, setRates] = useState<LatestRates>({});
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [localSupported, setLocalSupported] = useState<string[]>(supportedCurrencies);
  const [localAutoUpdate, setLocalAutoUpdate] = useState(autoUpdateRates);

  useEffect(() => {
    fetchRates();
  }, []);

  useEffect(() => {
    setLocalSupported(supportedCurrencies);
    setLocalAutoUpdate(autoUpdateRates);
  }, [supportedCurrencies, autoUpdateRates]);

  const fetchRates = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/currencies/rates');
      
      if (!response.ok) {
        throw new Error('Failed to fetch rates');
      }
      
      const data = await response.json();
      setRates(data.rates || {});
    } catch (error) {
      console.error('Error fetching rates:', error);
      // Don't show error toast on initial load if rates don't exist yet
    } finally {
      setLoading(false);
    }
  };

  const refreshRates = async () => {
    try {
      setRefreshing(true);
      const response = await fetch('/api/currencies/rates/refresh', {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to refresh rates');
      }
      
      const data = await response.json();
      
      if (data.success) {
        toast.success(`Valutakurser oppdatert! (${data.updated}/${data.total})`);
        await fetchRates();
      } else {
        toast.warning(`Noen kurser feilet (${data.updated}/${data.total})`);
      }
    } catch (error) {
      console.error('Error refreshing rates:', error);
      toast.error('Kunne ikke oppdatere valutakurser');
    } finally {
      setRefreshing(false);
    }
  };

  const toggleCurrency = (currency: string) => {
    const updated = localSupported.includes(currency)
      ? localSupported.filter(c => c !== currency)
      : [...localSupported, currency];
    
    // Always keep NOK
    if (!updated.includes('NOK')) {
      updated.push('NOK');
    }
    
    setLocalSupported(updated);
    onUpdate({
      supported_currencies: updated,
      auto_update_rates: localAutoUpdate,
    });
  };

  const toggleAutoUpdate = (checked: boolean) => {
    setLocalAutoUpdate(checked);
    onUpdate({
      supported_currencies: localSupported,
      auto_update_rates: checked,
    });
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('nb-NO', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  const formatRate = (rate: number) => {
    return rate.toLocaleString('nb-NO', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 6,
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h4 className="text-md font-medium text-gray-900 dark:text-gray-100">Valutastøtte</h4>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Velg hvilke valutaer firmaet kan håndtere
          </p>
        </div>
        <Button
          onClick={refreshRates}
          disabled={refreshing}
          size="sm"
          variant="outline"
        >
          <ArrowPathIcon className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Oppdaterer...' : 'Oppdater kurser'}
        </Button>
      </div>

      {/* Auto-update toggle */}
      <div className="flex items-center space-x-2 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
        <Checkbox
          id="auto_update_rates"
          checked={localAutoUpdate}
          onCheckedChange={(checked) => toggleAutoUpdate(checked === true)}
        />
        <Label htmlFor="auto_update_rates" className="cursor-pointer">
          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
            Oppdater kurser automatisk
          </span>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Henter nye valutakurser hver dag kl. 09:00
          </p>
        </Label>
      </div>

      {/* Last update info */}
      {lastRateUpdate && (
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Sist oppdatert: {formatDate(lastRateUpdate)}
        </div>
      )}

      {/* Currency selection */}
      <div className="space-y-3">
        {/* NOK - Always enabled */}
        <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">🇳🇴</span>
            <div>
              <div className="font-medium text-gray-900 dark:text-gray-100">
                NOK - Norwegian Krone
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                Basisvaluta (alltid aktivert)
              </div>
            </div>
          </div>
          <CheckCircleIcon className="w-5 h-5 text-green-600" />
        </div>

        {/* Other currencies */}
        {AVAILABLE_CURRENCIES.map((currency) => {
          const isEnabled = localSupported.includes(currency.code);
          const rate = rates[currency.code];

          return (
            <div
              key={currency.code}
              className={`flex items-center justify-between p-4 rounded-lg border transition-colors ${
                isEnabled
                  ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                  : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'
              }`}
            >
              <div className="flex items-center space-x-3 flex-1">
                <span className="text-2xl">{currency.flag}</span>
                <div className="flex-1">
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    {currency.code} - {currency.name}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Kilde: {currency.source}
                  </div>
                  {rate && (
                    <div className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                      1 {currency.code} = {formatRate(rate.rate)} NOK
                      <span className="text-xs text-gray-400 ml-2">
                        ({new Date(rate.date).toLocaleDateString('nb-NO')})
                      </span>
                    </div>
                  )}
                  {!rate && loading && (
                    <div className="text-xs text-gray-400 mt-1">Laster kurs...</div>
                  )}
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox
                  id={`currency_${currency.code}`}
                  checked={isEnabled}
                  onCheckedChange={() => toggleCurrency(currency.code)}
                />
                <Label
                  htmlFor={`currency_${currency.code}`}
                  className="cursor-pointer text-sm"
                >
                  {isEnabled ? 'Aktiv' : 'Inaktiv'}
                </Label>
              </div>
            </div>
          );
        })}
      </div>

      {/* Info box */}
      <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <p className="text-sm text-gray-700 dark:text-gray-300">
          <strong>💡 Tips:</strong> Valutakurser hentes fra Norges Bank (fiat) og CoinGecko (BTC).
          Ved fakturering i utenlandsk valuta lagres både originalbeløp og NOK-ekvivalent basert på dagens kurs.
        </p>
      </div>
    </div>
  );
};
