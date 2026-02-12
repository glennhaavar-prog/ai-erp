/**
 * Leverandørkort (Supplier Detail/Edit Card)
 * KONTAKTREGISTER - Supplier Detail & Edit
 */
'use client';

export const dynamic = 'force-dynamic';

import { GetServerSideProps } from 'next';
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';
import { useClient } from '@/contexts/ClientContext';
import { suppliersApi, Supplier, SupplierCreateRequest, SupplierUpdateRequest } from '@/api/contacts';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import ContactForm from '@/components/Kontakter/ContactForm';

interface LeverandorkortProps {
  supplierId?: string; // undefined = create mode
}

export const Leverandorkort: React.FC<LeverandorkortProps> = ({ supplierId }) => {
  const router = useRouter();
  const { selectedClient } = useClient();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [supplier, setSupplier] = useState<Supplier | null>(null);
  const [showAuditLog, setShowAuditLog] = useState(false);
  const [auditLog, setAuditLog] = useState<any[]>([]);

  const [formData, setFormData] = useState({
    company_name: '',
    org_number: '',
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
      website: '',
    },
    financial: {
      bank_account: '',
      iban: '',
      swift_bic: '',
      payment_terms_days: 30,
      currency: 'NOK',
      vat_code: '',
      default_expense_account: '',
    },
    notes: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const isEditMode = !!supplierId;

  useEffect(() => {
    if (supplierId) {
      fetchSupplier();
    }
  }, [supplierId]);

  const fetchSupplier = async () => {
    if (!supplierId) return;

    try {
      setLoading(true);
      const data = await suppliersApi.get(supplierId, {
        include_balance: true,
        include_transactions: true,
      });
      setSupplier(data);
      setFormData({
        company_name: data.company_name,
        org_number: data.org_number || '',
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
          website: data.contact?.website || '',
        },
        financial: {
          bank_account: data.financial?.bank_account || '',
          iban: data.financial?.iban || '',
          swift_bic: data.financial?.swift_bic || '',
          payment_terms_days: data.financial?.payment_terms_days || 30,
          currency: data.financial?.currency || 'NOK',
          vat_code: data.financial?.vat_code || '',
          default_expense_account: data.financial?.default_expense_account || '',
        },
        notes: data.notes || '',
      });
    } catch (error) {
      console.error('Error fetching supplier:', error);
      toast.error('Kunne ikke laste leverandør');
      router.push('/kontakter/leverandorer');
    } finally {
      setLoading(false);
    }
  };

  const fetchAuditLog = async () => {
    if (!supplierId) return;

    try {
      const data = await suppliersApi.getAuditLog(supplierId, { limit: 50 });
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

    if (!formData.company_name.trim()) {
      newErrors.company_name = 'Firmanavn er påkrevd';
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

      if (isEditMode && supplierId) {
        // Update existing
        const updateData: SupplierUpdateRequest = {
          company_name: formData.company_name,
          org_number: formData.org_number || undefined,
          address: formData.address,
          contact: formData.contact,
          financial: formData.financial,
          notes: formData.notes || undefined,
        };
        await suppliersApi.update(supplierId, updateData);
        toast.success('Leverandør oppdatert');
        router.push('/kontakter/leverandorer');
      } else {
        // Create new
        const createData: SupplierCreateRequest = {
          client_id: selectedClient.id,
          company_name: formData.company_name,
          org_number: formData.org_number || undefined,
          address: formData.address,
          contact: formData.contact,
          financial: formData.financial,
          notes: formData.notes || undefined,
        };
        await suppliersApi.create(createData);
        toast.success('Leverandør opprettet');
        router.push('/kontakter/leverandorer');
      }
    } catch (error: any) {
      console.error('Error saving supplier:', error);
      const errorMessage =
        error.response?.data?.detail || 'Kunne ikke lagre leverandør';
      toast.error(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    router.push('/kontakter/leverandorer');
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
        <p className="text-gray-500 dark:text-gray-400 mt-4">Laster leverandør...</p>
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
              {isEditMode ? 'Rediger leverandør' : 'Ny leverandør'}
            </h1>
            {supplier && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Leverandør #{supplier.supplier_number}
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
      {isEditMode && supplier && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Gjeldende saldo</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {new Intl.NumberFormat('nb-NO', {
                  style: 'currency',
                  currency: 'NOK',
                }).format(supplier.balance || 0)}
              </p>
            </div>
            {supplier.recent_transactions && supplier.recent_transactions.length > 0 && (
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {supplier.recent_transactions.length} nylige transaksjoner
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Form */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <ContactForm
          type="supplier"
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
              <Label htmlFor="bank_account">Bankkontonummer</Label>
              <Input
                id="bank_account"
                value={formData.financial.bank_account}
                onChange={(e) =>
                  handleFieldChange('financial', {
                    ...formData.financial,
                    bank_account: e.target.value,
                  })
                }
              />
            </div>

            <div>
              <Label htmlFor="payment_terms_days">Betalingsbetingelser (dager)</Label>
              <Input
                id="payment_terms_days"
                type="number"
                value={formData.financial.payment_terms_days}
                onChange={(e) =>
                  handleFieldChange('financial', {
                    ...formData.financial,
                    payment_terms_days: parseInt(e.target.value) || 30,
                  })
                }
              />
            </div>

            <div>
              <Label htmlFor="iban">IBAN</Label>
              <Input
                id="iban"
                value={formData.financial.iban}
                onChange={(e) =>
                  handleFieldChange('financial', {
                    ...formData.financial,
                    iban: e.target.value,
                  })
                }
              />
            </div>

            <div>
              <Label htmlFor="swift_bic">SWIFT/BIC</Label>
              <Input
                id="swift_bic"
                value={formData.financial.swift_bic}
                onChange={(e) =>
                  handleFieldChange('financial', {
                    ...formData.financial,
                    swift_bic: e.target.value,
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
              <Label htmlFor="default_expense_account">Standard utgiftskonto</Label>
              <Input
                id="default_expense_account"
                value={formData.financial.default_expense_account}
                onChange={(e) =>
                  handleFieldChange('financial', {
                    ...formData.financial,
                    default_expense_account: e.target.value,
                  })
                }
                placeholder="F.eks. 4000"
              />
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

export default Leverandorkort;
