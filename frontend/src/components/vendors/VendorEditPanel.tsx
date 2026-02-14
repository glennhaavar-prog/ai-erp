/**
 * VendorEditPanel - Slide-in panel for editing vendor/supplier
 */
'use client';

import React, { useState, useEffect } from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { suppliersApi, Supplier, SupplierUpdateRequest } from '@/api/contacts';
import { toast } from '@/lib/toast';
import { Loader2, Building2, MapPin, Phone, Mail, CreditCard } from 'lucide-react';

interface VendorEditPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  supplierId: string | null;
  onSaved?: () => void;
}

export function VendorEditPanel({
  open,
  onOpenChange,
  supplierId,
  onSaved,
}: VendorEditPanelProps) {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [supplier, setSupplier] = useState<Supplier | null>(null);
  const [form, setForm] = useState<SupplierUpdateRequest>({
    company_name: '',
    org_number: '',
    address: {
      line1: '',
      line2: '',
      postal_code: '',
      city: '',
      country: 'NO',
    },
    contact: {
      person: '',
      phone: '',
      email: '',
      website: '',
    },
    financial: {
      bank_account: '',
      payment_terms_days: 30,
      currency: 'NOK',
    },
    notes: '',
  });

  // Fetch supplier data when panel opens
  useEffect(() => {
    if (open && supplierId) {
      loadSupplier();
    }
  }, [open, supplierId]);

  const loadSupplier = async () => {
    if (!supplierId) return;

    setLoading(true);
    try {
      const data = await suppliersApi.get(supplierId);
      setSupplier(data);

      // Populate form
      setForm({
        company_name: data.company_name || '',
        org_number: data.org_number || '',
        address: {
          line1: data.address?.line1 || '',
          line2: data.address?.line2 || '',
          postal_code: data.address?.postal_code || '',
          city: data.address?.city || '',
          country: data.address?.country || 'NO',
        },
        contact: {
          person: data.contact?.person || '',
          phone: data.contact?.phone || '',
          email: data.contact?.email || '',
          website: data.contact?.website || '',
        },
        financial: {
          bank_account: data.financial?.bank_account || '',
          payment_terms_days: data.financial?.payment_terms_days || 30,
          currency: data.financial?.currency || 'NOK',
        },
        notes: data.notes || '',
      });
    } catch (error) {
      console.error('Error loading supplier:', error);
      toast.error('Kunne ikke laste leverandør');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!supplierId) return;

    // Validation
    if (!form.company_name?.trim()) {
      toast.error('Firmanavn er påkrevd');
      return;
    }

    setSaving(true);
    try {
      await suppliersApi.update(supplierId, form);
      toast.success('Leverandør oppdatert');
      onOpenChange(false);
      if (onSaved) {
        onSaved();
      }
    } catch (error: any) {
      console.error('Error updating supplier:', error);
      toast.error(error.response?.data?.detail || 'Kunne ikke oppdatere leverandør');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    onOpenChange(false);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[400px] sm:w-[450px] overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
          </div>
        ) : (
          <>
            <SheetHeader>
              <SheetTitle className="flex items-center gap-2">
                <Building2 className="w-5 h-5 text-blue-600" />
                Rediger leverandør
              </SheetTitle>
              <SheetDescription>
                Oppdater leverandørens informasjon. Endringer lagres i kontaktregisteret.
              </SheetDescription>
            </SheetHeader>

            <div className="mt-6 space-y-6">
              {/* Company Info */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                  <Building2 className="w-4 h-4" />
                  Firmainformasjon
                </h3>

                <div>
                  <Label htmlFor="company_name">Firmanavn *</Label>
                  <Input
                    id="company_name"
                    value={form.company_name}
                    onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                    placeholder="F.eks. Acme AS"
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label htmlFor="org_number">Org.nummer</Label>
                  <Input
                    id="org_number"
                    value={form.org_number}
                    onChange={(e) => setForm({ ...form, org_number: e.target.value })}
                    placeholder="F.eks. 123456789"
                    className="mt-1"
                  />
                </div>
              </div>

              {/* Address */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                  <MapPin className="w-4 h-4" />
                  Adresse
                </h3>

                <div>
                  <Label htmlFor="address_line1">Adresselinje 1</Label>
                  <Input
                    id="address_line1"
                    value={form.address?.line1}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        address: { ...form.address!, line1: e.target.value },
                      })
                    }
                    placeholder="Gateadresse"
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label htmlFor="address_line2">Adresselinje 2</Label>
                  <Input
                    id="address_line2"
                    value={form.address?.line2}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        address: { ...form.address!, line2: e.target.value },
                      })
                    }
                    placeholder="C/O eller tillegg"
                    className="mt-1"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="postal_code">Postnummer</Label>
                    <Input
                      id="postal_code"
                      value={form.address?.postal_code}
                      onChange={(e) =>
                        setForm({
                          ...form,
                          address: { ...form.address!, postal_code: e.target.value },
                        })
                      }
                      placeholder="0001"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label htmlFor="city">Poststed</Label>
                    <Input
                      id="city"
                      value={form.address?.city}
                      onChange={(e) =>
                        setForm({
                          ...form,
                          address: { ...form.address!, city: e.target.value },
                        })
                      }
                      placeholder="Oslo"
                      className="mt-1"
                    />
                  </div>
                </div>
              </div>

              {/* Contact */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                  <Phone className="w-4 h-4" />
                  Kontaktinformasjon
                </h3>

                <div>
                  <Label htmlFor="contact_person">Kontaktperson</Label>
                  <Input
                    id="contact_person"
                    value={form.contact?.person}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        contact: { ...form.contact!, person: e.target.value },
                      })
                    }
                    placeholder="Navn på kontaktperson"
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label htmlFor="contact_phone">Telefon</Label>
                  <Input
                    id="contact_phone"
                    value={form.contact?.phone}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        contact: { ...form.contact!, phone: e.target.value },
                      })
                    }
                    placeholder="+47 123 45 678"
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label htmlFor="contact_email">E-post</Label>
                  <Input
                    id="contact_email"
                    type="email"
                    value={form.contact?.email}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        contact: { ...form.contact!, email: e.target.value },
                      })
                    }
                    placeholder="kontakt@firma.no"
                    className="mt-1"
                  />
                </div>
              </div>

              {/* Financial */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                  <CreditCard className="w-4 h-4" />
                  Bankinformasjon
                </h3>

                <div>
                  <Label htmlFor="bank_account">Kontonummer</Label>
                  <Input
                    id="bank_account"
                    value={form.financial?.bank_account}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        financial: { ...form.financial!, bank_account: e.target.value },
                      })
                    }
                    placeholder="1234.56.78901"
                    className="mt-1"
                  />
                </div>
              </div>

              {/* Notes */}
              <div>
                <Label htmlFor="notes">Notater</Label>
                <Textarea
                  id="notes"
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  placeholder="Interne notater om leverandøren..."
                  rows={3}
                  className="mt-1"
                />
              </div>
            </div>

            <SheetFooter className="mt-6 gap-2">
              <Button variant="outline" onClick={handleCancel} disabled={saving}>
                Avbryt
              </Button>
              <Button onClick={handleSave} disabled={saving}>
                {saving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Lagrer...
                  </>
                ) : (
                  'Lagre endringer'
                )}
              </Button>
            </SheetFooter>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
