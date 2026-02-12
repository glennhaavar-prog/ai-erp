/**
 * Hook for Brønnøysund Register API lookup
 * Fetches company data from https://data.brreg.no/enhetsregisteret/api/enheter/{orgnr}
 */
'use client';

import { useState, useCallback } from 'react';
import axios from 'axios';

interface BrregData {
  organisasjonsnummer: string;
  navn: string;
  forretningsadresse?: {
    adresse: string[];
    postnummer: string;
    poststed: string;
    land: string;
  };
  naeringskode1?: {
    kode: string;
    beskrivelse: string;
  };
}

interface CompanyData {
  name: string;
  address: {
    line1: string;
    line2?: string;
    postal_code: string;
    city: string;
    country: string;
  };
  industry_code?: string;
  industry_description?: string;
}

export function useBrregLookup() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const lookup = useCallback(async (orgNumber: string): Promise<CompanyData | null> => {
    // Clean org number (remove spaces and non-digits)
    const cleanOrgNr = orgNumber.replace(/\D/g, '');

    if (cleanOrgNr.length !== 9) {
      setError('Organisasjonsnummer må være 9 siffer');
      return null;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.get<BrregData>(
        `https://data.brreg.no/enhetsregisteret/api/enheter/${cleanOrgNr}`,
        {
          timeout: 10000,
          headers: {
            'Accept': 'application/json',
          },
        }
      );

      const data = response.data;
      
      // Map Brreg data to our format
      const companyData: CompanyData = {
        name: data.navn,
        address: {
          line1: data.forretningsadresse?.adresse?.[0] || '',
          line2: data.forretningsadresse?.adresse?.[1] || undefined,
          postal_code: data.forretningsadresse?.postnummer || '',
          city: data.forretningsadresse?.poststed || '',
          country: data.forretningsadresse?.land || 'Norge',
        },
        industry_code: data.naeringskode1?.kode,
        industry_description: data.naeringskode1?.beskrivelse,
      };

      setLoading(false);
      return companyData;
    } catch (err: any) {
      console.error('Brreg lookup error:', err);
      
      if (err.response?.status === 404) {
        setError('Fant ikke organisasjonsnummer');
      } else if (err.code === 'ECONNABORTED') {
        setError('Tidsavbrudd - prøv igjen');
      } else {
        setError('Kunne ikke hente firmaopplysninger');
      }
      
      setLoading(false);
      return null;
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    lookup,
    loading,
    error,
    clearError,
  };
}
