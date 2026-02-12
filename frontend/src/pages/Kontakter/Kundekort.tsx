/**
 * Kundekort (Customer Detail/Edit Card)
 * KONTAKTREGISTER - Customer Detail & Edit
 */
'use client';

export const dynamic = 'force-dynamic';

import { GetServerSideProps } from 'next';
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';
import { useClient } from '@/contexts/ClientContext';
import { customersApi, Customer, CustomerCreateRequest, CustomerUpdateRequest } from '@/api/contacts';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import ContactForm from '@/components/Kontakter/ContactForm';
import { Checkbox } from '@/components/ui/checkbox';

interface KundekortProps {
  customerId?: string; // undefined = create mode
}

export const Kundekort: React.FC<KundekortProps> = ({ customerId }) => {
  const router = useRouter();
  const { selectedClient } = useClient();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [showAuditLog, setShowAuditLog] = useState(false);
  const [auditLog, setAuditLog] = useState<any[]>([]);

  const [formData, setFormData] = useState({
    is_company: true,
    name: '',
    org_number: '',
    birth_number: '',
    address: {
      line1: '',
      line2: '',
      postal_code: '',
      city: '',
      country: 'Norge',
    },
    contact: {
      person: '',
      phone: '',
      email: '',
    },
    financial: {
      payment_terms_days: 14,
      currency: 'NOK',
      vat_code: '',
      default_revenue_account: '',
      kid_prefix: '',
      use_kid: false,
      credit_limit: 0,
      reminder_fee: 0,
    },
    notes: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const isEditMode = !!customerId;

  useEffect(() => {
    if (customerId) {
      fetchCustomer();
    }
  }, [customerId]);

  const fetchCustomer = async () => {
    if (!customerId) return;

    try {
      setLoading(true);
      const data = await customersApi.get(customerId, {
        include_balance: true,
        include_transactions: true,
      });
      setCustomer(data);
      setFormData({
        is_company: data.is_company,
        name: data.name,
        org_number: data.org_number || '',
        birth_number: data.birth_number || '',
        address: {
          line1: data.address?.line1 || '',
          line2: data.address?.line2 || '',
          postal_code: data.address?.postal_code || '',
          city: data.address?.city || '',
          country: data.address?.country || 'Norge',
        },
        contact: {
          person: data.contact?.person || '',
          phone: data.contact?.phone || '',
          email: data.contact?.email || '',
        },
        financial: {
          payment_terms_days: data.financial?.payment_terms_days || 14,
          currency: data.financial?.currency || 'NOK',
          vat_code: data.financial?.vat_code || '',
          default_revenue_account: data.financial?.default_revenue_account || '',
          kid_prefix: data.financial?.kid_prefix || '',
          use_kid: data.financial?.use_kid ?? false,
          credit_limit: data.financial?.credit_limit ?? 0,
          reminder_fee: data.financial?.reminder_fee ?? 0,
        },
        notes: data.notes || '',
      });
    } catch (error) {
      console.error('Error fetching customer:', error);
      toast.error('Kunne ikke laste kunde');
      router.push('/kontakter/kunder');
    } finally {
      setLoading(false);
    }
  };

  const fetchAuditLog = async () => {
    if (!customerId) return;

    try {
      const data = await customersApi.getAuditLog(customerId, { limit: 50 });
      setAuditLog(data);
      setShowAuditLog(true);
    } catch (error) {
      console.error('Error fetching audit log:', error);
      toast.error('Kunne ikke laste endringslogg');
    }
  };

  const handleFieldChange = (field: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
    // Clear error for this field
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Navn er påkrevd';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validate()) {
      toast.error('Vennligst rett opp valideringsfeil');
      return;
    }

    if (!selectedClient?.id) {
      toast.error('Ingen klient valgt');
      return;
    }

    try {
      setSaving(true);

      if (isEditMode && customerId) {
        // Update existing
        const updateData: CustomerUpdateRequest = {
          is_company: formData.is_company,
          name: formData.name,
          org_number: formData.org_number || undefined,
          birth_number: formData.birth_number || undefined,
          address: formData.address,
          contact: formData.contact,
          financial: formData.financial,
          notes: formData.notes || undefined,
        };
        await customersApi.update(customerId, updateData);
        toast.success('Kunde oppdatert');
        router.push('/kontakter/kunder');
      } else {
        // Create new
        const createData: CustomerCreateRequest = {
          client_id: selectedClient.id,
          is_company: formData.is_company,
          name: formData.name,
          org_number: formData.org_number || undefined,
          birth_number: formData.birth_number || undefined,
          address: formData.address,
          contact: formData.contact,
          financial: formData.financial,
          notes: formData.notes || undefined,
        };
        await customersApi.create(createData);
        toast.success('Kunde opprettet');
        router.push('/kontakter/kunder');
      }
    } catch (error: any) {
      console.error('Error saving customer:', error);
      const errorMessage =
        error.response?.data?.detail || 'Kunne ikke lagre kunde';
      toast.error(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    router.push('/kontakter/kunder');
  };

  if (!selectedClient) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-500 dark:text-gray-400">Velg en klient for å fortsette</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="text-gray-500 dark:text-gray-400 mt-4">Laster kunde...</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={handleCancel}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <ArrowLeftIcon className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {isEditMode ? 'Rediger kunde' : 'Ny kunde'}
            </h1>
            {customer && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Kunde #{customer.customer_number}
              </p>
            )}
          </div>
        </div>

        <div className="flex gap-2">
          {isEditMode && (
            <Button variant="outline" onClick={fetchAuditLog}>
              Endringslogg
            </Button>
          )}
          <Button variant="outline" onClick={handleCancel}>
            Avbryt
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? 'Lagrer...' : 'Lagre'}
          </Button>
        </div>
      </div>

      {/* Balance Display (Edit Mode Only) */}
      {isEditMode && customer && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Utestående saldo</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {new Intl.NumberFormat('nb-NO', {
                  style: 'currency',
                  currency: 'NOK',
                }).format(customer.balance || 0)}
              </p>
            </div>
            {customer.recent_transactions && customer.recent_transactions.length > 0 && (
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {customer.recent_transactions.length} nylige transaksjoner
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Form */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <ContactForm
          type="customer"
          formData={formData}
          onChange={handleFieldChange}
          errors={errors}
        />

        {/* Financial Details */}
        <div className="space-y-4 mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Økonomiske detaljer
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="payment_terms_days">Betalingsbetingelser (dager)</Label>
              <Input
                id="payment_terms_days"
                type="number"
                value={formData.financial.payment_terms_days}
                onChange={(e) =>
                  handleFieldChange('financial', {
                    ...formData.financial,
                    payment_terms_days: parseInt(e.target.value) || 14,
                  })
                }
              />
            </div>

            <div>
              <Label htmlFor="currency">Valuta</Label>
              <select
                id="currency"
                value={formData.financial.currency}
                onChange={(e) =>
                  handleFieldChange('financial', {
                    ...formData.financial,
                    currency: e.target.value,
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              >
                <option value="NOK">NOK</option>
                <option value="EUR">EUR</option>
                <option value="USD">USD</option>
                <option value="SEK">SEK</option>
                <option value="DKK">DKK</option>
              </select>
            </div>

            <div>
              <Label htmlFor="default_revenue_account">Standard inntektskonto</Label>
              <Input
                id="default_revenue_account"
                value={formData.financial.default_revenue_account}
                onChange={(e) =>
                  handleFieldChange('financial', {
                    ...formData.financial,
                    default_revenue_account: e.target.value,
                  })
                }
                placeholder="F.eks. 3000"
              />
            </div>

            <div>
              <Label htmlFor="credit_limit">Kredittgrense (NOK)</Label>
              <Input
                id="credit_limit"
                type="number"
                value={formData.financial.credit_limit || ''}
                onChange={(e) =>
                  handleFieldChange('financial', {
                    ...formData.financial,
                    credit_limit: parseInt(e.target.value) || 0,
                  })
                }
              />
            </div>

            <div>
              <Label htmlFor="kid_prefix">KID-prefiks</Label>
              <Input
                id="kid_prefix"
                value={formData.financial.kid_prefix}
                onChange={(e) =>
                  handleFieldChange('financial', {
                    ...formData.financial,
                    kid_prefix: e.target.value,
                  })
                }
              />
            </div>

            <div>
              <Label htmlFor="reminder_fee">Purregebyr (NOK)</Label>
              <Input
                id="reminder_fee"
                type="number"
                value={formData.financial.reminder_fee}
                onChange={(e) =>
                  handleFieldChange('financial', {
                    ...formData.financial,
                    reminder_fee: parseInt(e.target.value) || 0,
                  })
                }
              />
            </div>

            <div className="flex items-center space-x-2 col-span-2">
              <Checkbox
                id="use_kid"
                checked={formData.financial.use_kid}
                onCheckedChange={(checked) =>
                  handleFieldChange('financial', {
                    ...formData.financial,
                    use_kid: checked === true,
                  })
                }
              />
              <Label htmlFor="use_kid" className="cursor-pointer">
                Bruk KID på fakturaer
              </Label>
            </div>
          </div>
        </div>
      </div>

      {/* Audit Log Modal */}
      {showAuditLog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-3xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                  Endringslogg
                </h2>
                <button
                  onClick={() => setShowAuditLog(false)}
                  className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="p-6 space-y-4">
              {auditLog.length === 0 ? (
                <p className="text-gray-500 dark:text-gray-400">Ingen endringslogg tilgjengelig</p>
              ) : (
                auditLog.map((log) => (
                  <div
                    key={log.id}
                    className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-semibold text-gray-900 dark:text-gray-100">
                          {log.action}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {new Date(log.performed_at).toLocaleString('nb-NO')}
                        </p>
                      </div>
                      {log.ip_address && (
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          IP: {log.ip_address}
                        </span>
                      )}
                    </div>
                    {log.changed_fields && (
                      <div className="mt-2 text-sm">
                        <p className="text-gray-600 dark:text-gray-400">
                          Endrede felt: {JSON.parse(log.changed_fields).fields?.join(', ')}
                        </p>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
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

export default Kundekort;
