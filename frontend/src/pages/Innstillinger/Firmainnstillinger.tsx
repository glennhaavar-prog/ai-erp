/**
 * Firmainnstillinger (Company Settings) Page
 * 6 sections: company_info, accounting_settings, bank_accounts, payroll_employees, services, responsible_accountant
 */
'use client';

export const dynamic = 'force-dynamic';

import { GetServerSideProps } from 'next';
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { useClient } from '@/contexts/ClientContext';
import { clientSettingsApi, ClientSettings, BankAccount } from '@/api/client-settings';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';
import { CurrencyManagement } from '@/components/CurrencyManagement';

type TabType = 'company_info' | 'accounting_settings' | 'bank_accounts' | 'payroll_employees' | 'services' | 'responsible_accountant';

export const Firmainnstillinger: React.FC = () => {
  const { selectedClient } = useClient();
  const [activeTab, setActiveTab] = useState<TabType>('company_info');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState<ClientSettings | null>(null);

  useEffect(() => {
    if (selectedClient?.id) {
      fetchSettings();
    }
  }, [selectedClient]);

  const fetchSettings = async () => {
    if (!selectedClient?.id) return;

    try {
      setLoading(true);
      const data = await clientSettingsApi.get(selectedClient.id);
      setSettings(data);
    } catch (error) {
      console.error('Error fetching settings:', error);
      toast.error('Kunne ikke laste innstillinger');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!selectedClient?.id || !settings) return;

    try {
      setSaving(true);
      await clientSettingsApi.update(selectedClient.id, {
        company_info: settings.company_info,
        accounting_settings: settings.accounting_settings,
        bank_accounts: settings.bank_accounts,
        payroll_employees: settings.payroll_employees,
        services: settings.services,
        responsible_accountant: settings.responsible_accountant,
      });
      toast.success('Innstillinger lagret');
      fetchSettings();
    } catch (error: any) {
      console.error('Error saving settings:', error);
      const errorMessage = error.response?.data?.detail || 'Kunne ikke lagre innstillinger';
      toast.error(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const updateCompanyInfo = (field: string, value: any) => {
    if (!settings) return;
    setSettings({
      ...settings,
      company_info: {
        ...settings.company_info,
        [field]: value,
      },
    });
  };

  const updateAccountingSettings = (field: string, value: any) => {
    if (!settings) return;
    setSettings({
      ...settings,
      accounting_settings: {
        ...settings.accounting_settings,
        [field]: value,
      },
    });
  };

  const addBankAccount = () => {
    if (!settings) return;
    const newAccount: BankAccount = {
      account_number: '',
      bank_name: '',
      iban: '',
      swift: '',
      is_primary: settings.bank_accounts.length === 0,
    };
    setSettings({
      ...settings,
      bank_accounts: [...settings.bank_accounts, newAccount],
    });
  };

  const updateBankAccount = (index: number, field: keyof BankAccount, value: any) => {
    if (!settings) return;
    const updated = [...settings.bank_accounts];
    updated[index] = { ...updated[index], [field]: value };
    setSettings({
      ...settings,
      bank_accounts: updated,
    });
  };

  const removeBankAccount = (index: number) => {
    if (!settings) return;
    const updated = settings.bank_accounts.filter((_, i) => i !== index);
    setSettings({
      ...settings,
      bank_accounts: updated,
    });
  };

  const updatePayrollEmployees = (field: string, value: any) => {
    if (!settings) return;
    setSettings({
      ...settings,
      payroll_employees: {
        ...settings.payroll_employees,
        [field]: value,
      },
    });
  };

  const updateServices = (field: string, value: any) => {
    if (!settings) return;
    setSettings({
      ...settings,
      services: {
        ...settings.services,
        [field]: value,
      },
    });
  };

  const updateResponsibleAccountant = (field: string, value: any) => {
    if (!settings) return;
    setSettings({
      ...settings,
      responsible_accountant: {
        ...settings.responsible_accountant,
        [field]: value,
      },
    });
  };

  if (!selectedClient) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-500 dark:text-gray-400">Velg en klient for å se innstillinger</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="text-gray-500 dark:text-gray-400 mt-4">Laster innstillinger...</p>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-500 dark:text-gray-400">Kunne ikke laste innstillinger</p>
      </div>
    );
  }

  const tabs: { id: TabType; label: string }[] = [
    { id: 'company_info', label: 'Firmainfo' },
    { id: 'accounting_settings', label: 'Regnskapsoppsett' },
    { id: 'bank_accounts', label: 'Bankkontoer' },
    { id: 'payroll_employees', label: 'Lønn/Ansatte' },
    { id: 'services', label: 'Tjenester' },
    { id: 'responsible_accountant', label: 'Ansvarlig regnskapsfører' },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Firmainnstillinger</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Konfigurer firmaopplysninger og innstillinger
          </p>
        </div>
        <Button onClick={handleSave} disabled={saving}>
          {saving ? 'Lagrer...' : 'Lagre endringer'}
        </Button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <div className="flex flex-wrap gap-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        {activeTab === 'company_info' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Firmaopplysninger</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>Firmanavn *</Label>
                <Input
                  value={settings.company_info.company_name}
                  onChange={(e) => updateCompanyInfo('company_name', e.target.value)}
                />
              </div>
              
              <div>
                <Label>Organisasjonsnummer *</Label>
                <Input
                  value={settings.company_info.org_number}
                  onChange={(e) => updateCompanyInfo('org_number', e.target.value)}
                />
              </div>
              
              <div className="col-span-2">
                <Label>Adresse</Label>
                <Input
                  value={settings.company_info.address.street || ''}
                  onChange={(e) =>
                    updateCompanyInfo('address', {
                      ...settings.company_info.address,
                      street: e.target.value,
                    })
                  }
                  placeholder="Gate/vei"
                />
              </div>
              
              <div>
                <Label>Postnummer</Label>
                <Input
                  value={settings.company_info.address.postal_code || ''}
                  onChange={(e) =>
                    updateCompanyInfo('address', {
                      ...settings.company_info.address,
                      postal_code: e.target.value,
                    })
                  }
                />
              </div>
              
              <div>
                <Label>Poststed</Label>
                <Input
                  value={settings.company_info.address.city || ''}
                  onChange={(e) =>
                    updateCompanyInfo('address', {
                      ...settings.company_info.address,
                      city: e.target.value,
                    })
                  }
                />
              </div>
              
              <div>
                <Label>Telefon</Label>
                <Input
                  value={settings.company_info.phone || ''}
                  onChange={(e) => updateCompanyInfo('phone', e.target.value)}
                />
              </div>
              
              <div>
                <Label>E-post</Label>
                <Input
                  type="email"
                  value={settings.company_info.email || ''}
                  onChange={(e) => updateCompanyInfo('email', e.target.value)}
                />
              </div>
              
              <div>
                <Label>Daglig leder</Label>
                <Input
                  value={settings.company_info.ceo_name || ''}
                  onChange={(e) => updateCompanyInfo('ceo_name', e.target.value)}
                />
              </div>
              
              <div>
                <Label>Styreleder</Label>
                <Input
                  value={settings.company_info.chairman_name || ''}
                  onChange={(e) => updateCompanyInfo('chairman_name', e.target.value)}
                />
              </div>
              
              <div>
                <Label>Bransje</Label>
                <Input
                  value={settings.company_info.industry || ''}
                  onChange={(e) => updateCompanyInfo('industry', e.target.value)}
                />
              </div>
              
              <div>
                <Label>NACE-kode</Label>
                <Input
                  value={settings.company_info.nace_code || ''}
                  onChange={(e) => updateCompanyInfo('nace_code', e.target.value)}
                />
              </div>
              
              <div>
                <Label>Regnskapsårets startmåned</Label>
                <select
                  value={settings.company_info.accounting_year_start_month}
                  onChange={(e) =>
                    updateCompanyInfo('accounting_year_start_month', parseInt(e.target.value))
                  }
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                >
                  {[...Array(12)].map((_, i) => (
                    <option key={i + 1} value={i + 1}>
                      {new Date(2024, i, 1).toLocaleString('nb-NO', { month: 'long' })}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <Label>Organisasjonsform</Label>
                <Input
                  value={settings.company_info.legal_form || ''}
                  onChange={(e) => updateCompanyInfo('legal_form', e.target.value)}
                  placeholder="AS, NUF, ENK, etc."
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'accounting_settings' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Regnskapsoppsett</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>Kontoplan</Label>
                <select
                  value={settings.accounting_settings.chart_of_accounts}
                  onChange={(e) => updateAccountingSettings('chart_of_accounts', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                >
                  <option value="NS4102">NS 4102 (Standard)</option>
                  <option value="NS4102_SIMPLIFIED">NS 4102 (Forenklet)</option>
                  <option value="CUSTOM">Tilpasset</option>
                </select>
              </div>
              
              <div>
                <Label>MVA-periode</Label>
                <select
                  value={settings.accounting_settings.vat_period}
                  onChange={(e) => updateAccountingSettings('vat_period', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                >
                  <option value="monthly">Månedlig</option>
                  <option value="bimonthly">Annenhver måned</option>
                  <option value="quarterly">Kvartalsvis</option>
                  <option value="yearly">Årlig</option>
                </select>
              </div>
              
              <div>
                <Label>Valuta</Label>
                <select
                  value={settings.accounting_settings.currency}
                  onChange={(e) => updateAccountingSettings('currency', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                >
                  <option value="NOK">NOK</option>
                  <option value="EUR">EUR</option>
                  <option value="USD">USD</option>
                </select>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="vat_registered"
                  checked={settings.accounting_settings.vat_registered}
                  onCheckedChange={(checked) =>
                    updateAccountingSettings('vat_registered', checked === true)
                  }
                />
                <Label htmlFor="vat_registered" className="cursor-pointer">
                  MVA-registrert
                </Label>
              </div>
            </div>

            {/* Currency Management Section */}
            <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
              <CurrencyManagement
                supportedCurrencies={settings.accounting_settings.supported_currencies || ['NOK']}
                autoUpdateRates={settings.accounting_settings.auto_update_rates ?? true}
                lastRateUpdate={settings.accounting_settings.last_rate_update ?? null}
                onUpdate={(data) => {
                  updateAccountingSettings('supported_currencies', data.supported_currencies);
                  updateAccountingSettings('auto_update_rates', data.auto_update_rates);
                }}
              />
            </div>
          </div>
        )}

        {activeTab === 'bank_accounts' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Bankkontoer</h3>
              <Button onClick={addBankAccount} size="sm">
                <PlusIcon className="w-4 h-4 mr-2" />
                Legg til bankkonto
              </Button>
            </div>
            
            <div className="space-y-4">
              {settings.bank_accounts.map((account, index) => (
                <div
                  key={index}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-3"
                >
                  <div className="flex justify-between items-start">
                    <h4 className="font-medium text-gray-900 dark:text-gray-100">
                      Bankkonto {index + 1}
                    </h4>
                    <button
                      onClick={() => removeBankAccount(index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <TrashIcon className="w-5 h-5" />
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <Label>Kontonummer *</Label>
                      <Input
                        value={account.account_number}
                        onChange={(e) =>
                          updateBankAccount(index, 'account_number', e.target.value)
                        }
                      />
                    </div>
                    
                    <div>
                      <Label>Banknavn *</Label>
                      <Input
                        value={account.bank_name}
                        onChange={(e) => updateBankAccount(index, 'bank_name', e.target.value)}
                      />
                    </div>
                    
                    <div>
                      <Label>IBAN</Label>
                      <Input
                        value={account.iban || ''}
                        onChange={(e) => updateBankAccount(index, 'iban', e.target.value)}
                      />
                    </div>
                    
                    <div>
                      <Label>SWIFT</Label>
                      <Input
                        value={account.swift || ''}
                        onChange={(e) => updateBankAccount(index, 'swift', e.target.value)}
                      />
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id={`is_primary_${index}`}
                        checked={account.is_primary}
                        onCheckedChange={(checked) =>
                          updateBankAccount(index, 'is_primary', checked === true)
                        }
                      />
                      <Label htmlFor={`is_primary_${index}`} className="cursor-pointer">
                        Primær bankkonto
                      </Label>
                    </div>
                  </div>
                </div>
              ))}
              
              {settings.bank_accounts.length === 0 && (
                <p className="text-gray-500 dark:text-gray-400 text-center py-4">
                  Ingen bankkontoer registrert
                </p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'payroll_employees' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Lønn og ansatte
            </h3>
            
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="has_employees"
                  checked={settings.payroll_employees.has_employees}
                  onCheckedChange={(checked) =>
                    updatePayrollEmployees('has_employees', checked === true)
                  }
                />
                <Label htmlFor="has_employees" className="cursor-pointer">
                  Firmaet har ansatte
                </Label>
              </div>
              
              {settings.payroll_employees.has_employees && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Lønnskjøringsfrekvens</Label>
                    <select
                      value={settings.payroll_employees.payroll_frequency || 'monthly'}
                      onChange={(e) => updatePayrollEmployees('payroll_frequency', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                    >
                      <option value="weekly">Ukentlig</option>
                      <option value="biweekly">Annenhver uke</option>
                      <option value="monthly">Månedlig</option>
                    </select>
                  </div>
                  
                  <div>
                    <Label>Arbeidsgiveravgiftssone</Label>
                    <select
                      value={settings.payroll_employees.employer_tax_zone || '1'}
                      onChange={(e) => updatePayrollEmployees('employer_tax_zone', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                    >
                      <option value="1">Sone 1 (14,1%)</option>
                      <option value="2">Sone 2 (10,6%)</option>
                      <option value="3">Sone 3 (6,4%)</option>
                      <option value="4">Sone 4 (5,1%)</option>
                      <option value="5">Sone 5 (0%)</option>
                    </select>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'services' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Tjenester som leveres
            </h3>
            
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="service_bookkeeping"
                  checked={settings.services.services_provided.bookkeeping}
                  onCheckedChange={(checked) =>
                    updateServices('services_provided', {
                      ...settings.services.services_provided,
                      bookkeeping: checked === true,
                    })
                  }
                />
                <Label htmlFor="service_bookkeeping" className="cursor-pointer">
                  Bokføring
                </Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="service_payroll"
                  checked={settings.services.services_provided.payroll}
                  onCheckedChange={(checked) =>
                    updateServices('services_provided', {
                      ...settings.services.services_provided,
                      payroll: checked === true,
                    })
                  }
                />
                <Label htmlFor="service_payroll" className="cursor-pointer">
                  Lønn
                </Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="service_annual_accounts"
                  checked={settings.services.services_provided.annual_accounts}
                  onCheckedChange={(checked) =>
                    updateServices('services_provided', {
                      ...settings.services.services_provided,
                      annual_accounts: checked === true,
                    })
                  }
                />
                <Label htmlFor="service_annual_accounts" className="cursor-pointer">
                  Årsregnskap
                </Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="service_vat_reporting"
                  checked={settings.services.services_provided.vat_reporting}
                  onCheckedChange={(checked) =>
                    updateServices('services_provided', {
                      ...settings.services.services_provided,
                      vat_reporting: checked === true,
                    })
                  }
                />
                <Label htmlFor="service_vat_reporting" className="cursor-pointer">
                  MVA-rapportering
                </Label>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'responsible_accountant' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Ansvarlig regnskapsfører
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>Navn</Label>
                <Input
                  value={settings.responsible_accountant.name || ''}
                  onChange={(e) => updateResponsibleAccountant('name', e.target.value)}
                />
              </div>
              
              <div>
                <Label>E-post</Label>
                <Input
                  type="email"
                  value={settings.responsible_accountant.email || ''}
                  onChange={(e) => updateResponsibleAccountant('email', e.target.value)}
                />
              </div>
              
              <div>
                <Label>Telefon</Label>
                <Input
                  type="tel"
                  value={settings.responsible_accountant.phone || ''}
                  onChange={(e) => updateResponsibleAccountant('phone', e.target.value)}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export const getServerSideProps: GetServerSideProps = async () => {
  return {
    props: {},
  };
};

export default Firmainnstillinger;
