/**
 * Quick Add Modal Component
 * Minimal overlay for quickly adding entities without leaving the page
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useBrregLookup } from '@/hooks/useBrregLookup';
import axios from 'axios';
import { toast } from 'sonner';
import { CheckCircleIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api';

interface QuickAddModalProps {
  type: 'supplier' | 'customer' | 'voucher';
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function QuickAddModal({ type, open, onClose, onSuccess }: QuickAddModalProps) {
  const [formData, setFormData] = useState<any>({});
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const { lookup, loading: brregLoading } = useBrregLookup();

  // Reset form when modal opens/closes
  useEffect(() => {
    if (open) {
      setFormData(getDefaultFormData(type));
      setErrors({});
    }
  }, [open, type]);

  const getDefaultFormData = (type: string) => {
    switch (type) {
      case 'supplier':
        return {
          company_name: '',
          org_number: '',
          address: { country: 'Norge' },
          contact: {},
        };
      case 'customer':
        return {
          name: '',
          org_number: '',
          is_company: true,
          address: { country: 'Norge' },
          contact: {},
        };
      case 'voucher':
        return {
          voucher_date: new Date().toISOString().split('T')[0],
          description: '',
          amount: '',
        };
      default:
        return {};
    }
  };

  const handleOrgNumberChange = async (orgNumber: string) => {
    setFormData({ ...formData, org_number: orgNumber });

    const cleanOrgNr = orgNumber.replace(/\D/g, '');
    if (cleanOrgNr.length === 9) {
      const data = await lookup(cleanOrgNr);
      if (data) {
        setFormData((prev: any) => ({
          ...prev,
          ...(type === 'supplier' ? { company_name: data.name } : { name: data.name }),
          address: {
            line1: data.address.line1,
            line2: data.address.line2,
            postal_code: data.address.postal_code,
            city: data.address.city,
            country: data.address.country,
          },
        }));
        toast.success('Firmaopplysninger hentet fra Brønnøysundregistrene');
      }
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (type === 'supplier') {
      if (!formData.company_name?.trim()) {
        newErrors.company_name = 'Firmanavn er påkrevd';
      }
    } else if (type === 'customer') {
      if (!formData.name?.trim()) {
        newErrors.name = 'Navn er påkrevd';
      }
    } else if (type === 'voucher') {
      if (!formData.description?.trim()) {
        newErrors.description = 'Beskrivelse er påkrevd';
      }
      if (!formData.voucher_date) {
        newErrors.voucher_date = 'Dato er påkrevd';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    setLoading(true);

    try {
      let endpoint = '';
      let data = { ...formData };

      switch (type) {
        case 'supplier':
          endpoint = `${API_BASE_URL}/suppliers`;
          data.active = true;
          break;
        case 'customer':
          endpoint = `${API_BASE_URL}/customers`;
          data.active = true;
          break;
        case 'voucher':
          endpoint = `${API_BASE_URL}/vouchers`;
          data.status = 'draft';
          break;
      }

      await axios.post(endpoint, data);

      toast.success(`${getTypeLabel(type)} opprettet!`);
      onSuccess?.();
      onClose();
    } catch (error: any) {
      console.error('Quick add error:', error);
      toast.error(error.response?.data?.message || 'Kunne ikke opprette');
    } finally {
      setLoading(false);
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'supplier': return 'Leverandør';
      case 'customer': return 'Kunde';
      case 'voucher': return 'Bilag';
      default: return '';
    }
  };

  const renderForm = () => {
    if (type === 'supplier' || type === 'customer') {
      return (
        <div className="space-y-4">
          <div>
            <Label htmlFor="name">
              {type === 'supplier' ? 'Firmanavn *' : 'Navn *'}
            </Label>
            <Input
              id="name"
              value={type === 'supplier' ? formData.company_name || '' : formData.name || ''}
              onChange={(e) => setFormData({ 
                ...formData, 
                [type === 'supplier' ? 'company_name' : 'name']: e.target.value 
              })}
              className={errors.company_name || errors.name ? 'border-red-500' : ''}
              autoFocus
            />
            {(errors.company_name || errors.name) && (
              <p className="text-sm text-red-600 mt-1">
                {errors.company_name || errors.name}
              </p>
            )}
          </div>

          <div>
            <Label htmlFor="org_number">Organisasjonsnummer</Label>
            <div className="relative">
              <Input
                id="org_number"
                value={formData.org_number || ''}
                onChange={(e) => handleOrgNumberChange(e.target.value)}
                placeholder="9 siffer for auto-utfylling"
              />
              {brregLoading && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  <MagnifyingGlassIcon className="w-5 h-5 text-blue-500 animate-pulse" />
                </div>
              )}
            </div>
          </div>

          <div>
            <Label htmlFor="email">E-post</Label>
            <Input
              id="email"
              type="email"
              value={formData.contact?.email || ''}
              onChange={(e) => setFormData({ 
                ...formData, 
                contact: { ...formData.contact, email: e.target.value }
              })}
            />
          </div>

          <div>
            <Label htmlFor="phone">Telefon</Label>
            <Input
              id="phone"
              type="tel"
              value={formData.contact?.phone || ''}
              onChange={(e) => setFormData({ 
                ...formData, 
                contact: { ...formData.contact, phone: e.target.value }
              })}
            />
          </div>
        </div>
      );
    } else if (type === 'voucher') {
      return (
        <div className="space-y-4">
          <div>
            <Label htmlFor="description">Beskrivelse *</Label>
            <Input
              id="description"
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className={errors.description ? 'border-red-500' : ''}
              placeholder="F.eks. 'Kontorrekvisita'"
              autoFocus
            />
            {errors.description && (
              <p className="text-sm text-red-600 mt-1">{errors.description}</p>
            )}
          </div>

          <div>
            <Label htmlFor="voucher_date">Dato *</Label>
            <Input
              id="voucher_date"
              type="date"
              value={formData.voucher_date || ''}
              onChange={(e) => setFormData({ ...formData, voucher_date: e.target.value })}
              className={errors.voucher_date ? 'border-red-500' : ''}
            />
            {errors.voucher_date && (
              <p className="text-sm text-red-600 mt-1">{errors.voucher_date}</p>
            )}
          </div>

          <div>
            <Label htmlFor="amount">Beløp</Label>
            <Input
              id="amount"
              type="number"
              step="0.01"
              value={formData.amount || ''}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              placeholder="0.00"
            />
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Ny {getTypeLabel(type)}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {renderForm()}

          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={loading}
            >
              Avbryt
            </Button>
            <Button
              type="submit"
              disabled={loading}
              className="min-w-[100px]"
            >
              {loading ? 'Lagrer...' : 'Lagre'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// Quick Add Button Component
interface QuickAddButtonProps {
  type: 'supplier' | 'customer' | 'voucher';
  onSuccess?: () => void;
  className?: string;
}

export function QuickAddButton({ type, onSuccess, className = '' }: QuickAddButtonProps) {
  const [open, setOpen] = useState(false);

  const getLabel = () => {
    switch (type) {
      case 'supplier': return 'Ny Leverandør';
      case 'customer': return 'Ny Kunde';
      case 'voucher': return 'Nytt Bilag';
      default: return 'Legg til';
    }
  };

  return (
    <>
      <Button
        onClick={() => setOpen(true)}
        className={className}
        size="sm"
      >
        <span className="text-lg mr-1">+</span> {getLabel()}
      </Button>

      <QuickAddModal
        type={type}
        open={open}
        onClose={() => setOpen(false)}
        onSuccess={onSuccess}
      />
    </>
  );
}
