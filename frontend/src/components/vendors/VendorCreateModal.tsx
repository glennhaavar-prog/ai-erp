/**
 * VendorCreateModal - Modal for creating new vendor/supplier
 */
'use client';

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { suppliersApi, SupplierCreateRequest } from '@/api/contacts';
import { toast } from '@/lib/toast';
import { Loader2, Building2, MapPin, Phone, CreditCard, Plus } from 'lucide-react';

interface VendorCreateModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  clientId: string;
  onCreated?: (supplierId: string) => void;
}

export function VendorCreateModal({
  open,
  onOpenChange,
  clientId,
  onCreated,
}: VendorCreateModalProps) {
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState<SupplierCreateRequest>({
    client_id: clientId,
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

  // Reset form when modal opens/closes
  React.useEffect(() => {
    if (open) {
      setForm({
        client_id: clientId,
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
    }
  }, [open, clientId]);

  const handleCreate = async () => {
    // Validation
    if (!form.company_name?.trim()) {
      toast.error('Firmanavn er påkrevd');
      return;
    }

    setCreating(true);
    try {
      const newSupplier = await suppliersApi.create(form);
      toast.success('Leverandør opprettet');
      onOpenChange(false);
      if (onCreated) {
        onCreated(newSupplier.id);
      }
    } catch (error: any) {
      console.error('Error creating supplier:', error);
      toast.error(error.response?.data?.detail || 'Kunne ikke opprette leverandør');
    } finally {
      setCreating(false);
    }
  };

  const handleCancel = () => {
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plus className="w-5 h-5 text-green-600" />
            Opprett ny leverandør
          </DialogTitle>
          <DialogDescription>
            Legg til en ny leverandør i kontaktregisteret. Feltene merket med * er påkrevd.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Company Info */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
              <Building2 className="w-4 h-4" />
              Firmainformasjon
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <Label htmlFor="create_company_name">Firmanavn *</Label>
                <Input
                  id="create_company_name"
                  value={form.company_name}
                  onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                  placeholder="F.eks. Acme AS"
                  className="mt-1"
                />
              </div>

              <div>
                <Label htmlFor="create_org_number">Org.nummer</Label>
                <Input
                  id="create_org_number"
                  value={form.org_number}
                  onChange={(e) => setForm({ ...form, org_number: e.target.value })}
                  placeholder="123456789"
                  className="mt-1"
                />
              </div>
            </div>
          </div>

          {/* Address */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
              <MapPin className="w-4 h-4" />
              Adresse
            </h3>

            <div className="grid gap-4">
              <div>
                <Label htmlFor="create_address_line1">Adresselinje 1</Label>
                <Input
                  id="create_address_line1"
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
                <Label htmlFor="create_address_line2">Adresselinje 2</Label>
                <Input
                  id="create_address_line2"
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

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="create_postal_code">Postnummer</Label>
                  <Input
                    id="create_postal_code"
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
                  <Label htmlFor="create_city">Poststed</Label>
                  <Input
                    id="create_city"
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
          </div>

          {/* Contact */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
              <Phone className="w-4 h-4" />
              Kontaktinformasjon
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <Label htmlFor="create_contact_person">Kontaktperson</Label>
                <Input
                  id="create_contact_person"
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
                <Label htmlFor="create_contact_phone">Telefon</Label>
                <Input
                  id="create_contact_phone"
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
                <Label htmlFor="create_contact_email">E-post</Label>
                <Input
                  id="create_contact_email"
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
          </div>

          {/* Financial */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
              <CreditCard className="w-4 h-4" />
              Bankinformasjon
            </h3>

            <div>
              <Label htmlFor="create_bank_account">Kontonummer</Label>
              <Input
                id="create_bank_account"
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
            <Label htmlFor="create_notes">Notater</Label>
            <Textarea
              id="create_notes"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              placeholder="Interne notater om leverandøren..."
              rows={3}
              className="mt-1"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleCancel} disabled={creating}>
            Avbryt
          </Button>
          <Button onClick={handleCreate} disabled={creating} className="bg-green-600 hover:bg-green-700">
            {creating ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Oppretter...
              </>
            ) : (
              <>
                <Plus className="w-4 h-4 mr-2" />
                Opprett leverandør
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
