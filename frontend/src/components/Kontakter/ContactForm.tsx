/**
 * Shared Contact Form Component
 * Used for both Supplier and Customer forms
 * Includes Brønnøysund API auto-lookup for org numbers
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useBrregLookup } from '@/hooks/useBrregLookup';
import { MagnifyingGlassIcon, CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';

interface AddressFields {
  line1?: string;
  line2?: string;
  postal_code?: string;
  city?: string;
  country: string;
}

interface ContactFields {
  person?: string;
  phone?: string;
  email?: string;
  website?: string;
}

interface ContactFormProps {
  type: 'supplier' | 'customer';
  formData: any;
  onChange: (field: string, value: any) => void;
  errors?: Record<string, string>;
}

export const ContactForm: React.FC<ContactFormProps> = ({
  type,
  formData,
  onChange,
  errors = {},
}) => {
  const isSupplier = type === 'supplier';
  const { lookup, loading: brregLoading, error: brregError, clearError } = useBrregLookup();
  const [showBrregSuccess, setShowBrregSuccess] = useState(false);

  // Auto-lookup when org number is 9 digits
  useEffect(() => {
    const orgNumber = formData.org_number?.replace(/\D/g, '');
    
    if (orgNumber && orgNumber.length === 9) {
      const timer = setTimeout(async () => {
        const data = await lookup(orgNumber);
        
        if (data) {
          // Auto-fill form fields
          if (isSupplier && !formData.company_name) {
            onChange('company_name', data.name);
          } else if (!isSupplier && !formData.name) {
            onChange('name', data.name);
          }
          
          if (!formData.address?.line1) {
            onChange('address', {
              ...formData.address,
              line1: data.address.line1,
              line2: data.address.line2,
              postal_code: data.address.postal_code,
              city: data.address.city,
              country: data.address.country,
            });
          }
          
          setShowBrregSuccess(true);
          setTimeout(() => setShowBrregSuccess(false), 3000);
        }
      }, 500);

      return () => clearTimeout(timer);
    }
  }, [formData.org_number, lookup, onChange, isSupplier, formData.company_name, formData.name, formData.address]);

  useEffect(() => {
    if (brregError) {
      const timer = setTimeout(() => clearError(), 5000);
      return () => clearTimeout(timer);
    }
  }, [brregError, clearError]);

  return (
    <div className="space-y-6">
      {/* Basic Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Grunnleggende informasjon
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="company_name">
              {isSupplier ? 'Firmanavn *' : 'Navn *'}
            </Label>
            <Input
              id="company_name"
              value={isSupplier ? formData.company_name : formData.name}
              onChange={(e) =>
                onChange(isSupplier ? 'company_name' : 'name', e.target.value)
              }
              className={errors.company_name || errors.name ? 'border-red-500' : ''}
            />
            {(errors.company_name || errors.name) && (
              <p className="text-sm text-red-600 mt-1">
                {errors.company_name || errors.name}
              </p>
            )}
          </div>

          {!isSupplier && (
            <div>
              <Label htmlFor="is_company">Type</Label>
              <select
                id="is_company"
                value={formData.is_company ? 'true' : 'false'}
                onChange={(e) => onChange('is_company', e.target.value === 'true')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              >
                <option value="true">Bedrift</option>
                <option value="false">Privatperson</option>
              </select>
            </div>
          )}

          <div>
            <Label htmlFor="org_number">
              {isSupplier || formData.is_company ? 'Organisasjonsnummer' : 'Fødselsnummer'}
            </Label>
            <div className="relative">
              <Input
                id="org_number"
                value={
                  isSupplier || formData.is_company
                    ? formData.org_number || ''
                    : formData.birth_number || ''
                }
                onChange={(e) => {
                  clearError();
                  setShowBrregSuccess(false);
                  onChange(
                    isSupplier || formData.is_company ? 'org_number' : 'birth_number',
                    e.target.value
                  );
                }}
                className={brregError ? 'border-red-500 pr-10' : showBrregSuccess ? 'border-green-500 pr-10' : 'pr-10'}
                placeholder="9 siffer for auto-utfylling"
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                {brregLoading && (
                  <MagnifyingGlassIcon className="w-5 h-5 text-blue-500 animate-pulse" />
                )}
                {showBrregSuccess && (
                  <CheckCircleIcon className="w-5 h-5 text-green-500" />
                )}
                {brregError && (
                  <ExclamationCircleIcon className="w-5 h-5 text-red-500" />
                )}
              </div>
            </div>
            {brregError && (
              <p className="text-sm text-red-600 mt-1">{brregError}</p>
            )}
            {showBrregSuccess && (
              <p className="text-sm text-green-600 mt-1">
                ✓ Firmaopplysninger hentet fra Brønnøysundregistrene
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Address */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Adresse</h3>

        <div className="grid grid-cols-1 gap-4">
          <div>
            <Label htmlFor="address_line1">Adresselinje 1</Label>
            <Input
              id="address_line1"
              value={formData.address?.line1 || ''}
              onChange={(e) =>
                onChange('address', { ...formData.address, line1: e.target.value })
              }
            />
          </div>

          <div>
            <Label htmlFor="address_line2">Adresselinje 2</Label>
            <Input
              id="address_line2"
              value={formData.address?.line2 || ''}
              onChange={(e) =>
                onChange('address', { ...formData.address, line2: e.target.value })
              }
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="postal_code">Postnummer</Label>
              <Input
                id="postal_code"
                value={formData.address?.postal_code || ''}
                onChange={(e) =>
                  onChange('address', { ...formData.address, postal_code: e.target.value })
                }
              />
            </div>

            <div>
              <Label htmlFor="city">Poststed</Label>
              <Input
                id="city"
                value={formData.address?.city || ''}
                onChange={(e) =>
                  onChange('address', { ...formData.address, city: e.target.value })
                }
              />
            </div>
          </div>

          <div>
            <Label htmlFor="country">Land</Label>
            <Input
              id="country"
              value={formData.address?.country || 'Norge'}
              onChange={(e) =>
                onChange('address', { ...formData.address, country: e.target.value })
              }
            />
          </div>
        </div>
      </div>

      {/* Contact Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Kontaktinformasjon
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="contact_person">Kontaktperson</Label>
            <Input
              id="contact_person"
              value={formData.contact?.person || ''}
              onChange={(e) =>
                onChange('contact', { ...formData.contact, person: e.target.value })
              }
            />
          </div>

          <div>
            <Label htmlFor="phone">Telefon</Label>
            <Input
              id="phone"
              type="tel"
              value={formData.contact?.phone || ''}
              onChange={(e) =>
                onChange('contact', { ...formData.contact, phone: e.target.value })
              }
            />
          </div>

          <div>
            <Label htmlFor="email">E-post</Label>
            <Input
              id="email"
              type="email"
              value={formData.contact?.email || ''}
              onChange={(e) =>
                onChange('contact', { ...formData.contact, email: e.target.value })
              }
            />
          </div>

          {isSupplier && (
            <div>
              <Label htmlFor="website">Nettside</Label>
              <Input
                id="website"
                type="url"
                value={formData.contact?.website || ''}
                onChange={(e) =>
                  onChange('contact', { ...formData.contact, website: e.target.value })
                }
              />
            </div>
          )}
        </div>
      </div>

      {/* Notes */}
      <div>
        <Label htmlFor="notes">Notater</Label>
        <textarea
          id="notes"
          rows={3}
          value={formData.notes || ''}
          onChange={(e) => onChange('notes', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
          placeholder="Interne notater..."
        />
      </div>
    </div>
  );
};

export default ContactForm;
