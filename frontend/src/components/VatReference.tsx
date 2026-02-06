'use client';

import React, { useState } from 'react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';

interface VatCode {
  code: string;
  rate: string;
  description: string;
  whenToUse: string;
  category: 'outgoing' | 'incoming' | 'exempt' | 'export';
}

const VAT_CODES: VatCode[] = [
  // Outgoing VAT (Utgående avgift)
  {
    code: '3',
    rate: '15%',
    description: 'Redusert sats',
    whenToUse: 'Matvareer, alkoholfrie drikkevarer, persontransport innenlands (buss, tog, ferge, drosje), overnatting, adgang til kino, museer, fornøyelsesparker',
    category: 'outgoing',
  },
  {
    code: '5',
    rate: '25%',
    description: 'Alminnelig sats',
    whenToUse: 'Generelt salg av varer og tjenester som ikke omfattes av redusert eller null sats. Standard MVA-sats for de fleste transaksjoner',
    category: 'outgoing',
  },
  {
    code: '31',
    rate: '15%',
    description: 'Tjenester kjøpt fra utlandet (15%)',
    whenToUse: 'Kjøp av tjenester fra utlandet med fradragsrett der redusert sats gjelder (snudd avregning)',
    category: 'incoming',
  },
  {
    code: '32',
    rate: '15%',
    description: 'Kjøp av klimakvoter og gull (15%)',
    whenToUse: 'Kjøp av klimakvoter og gull fra utlandet med redusert sats',
    category: 'incoming',
  },
  {
    code: '33',
    rate: '15%',
    description: 'Kjøp med redusert sats og fradrag',
    whenToUse: 'Kjøp av varer med redusert sats hvor virksomheten har fradragsrett',
    category: 'incoming',
  },
  {
    code: '51',
    rate: '25%',
    description: 'Innførsel av varer med fradragsrett',
    whenToUse: 'Import av varer fra land utenfor EU/EØS med full fradragsrett (snudd avregning)',
    category: 'incoming',
  },
  {
    code: '52',
    rate: '25%',
    description: 'Tjenester kjøpt fra utlandet (25%)',
    whenToUse: 'Kjøp av tjenester fra utlandet med fradragsrett der alminnelig sats gjelder (snudd avregning)',
    category: 'incoming',
  },
  {
    code: '53',
    rate: '25%',
    description: 'Kjøp av klimakvoter og gull (25%)',
    whenToUse: 'Kjøp av klimakvoter og gull fra utlandet med alminnelig sats',
    category: 'incoming',
  },
  
  // Incoming VAT (Inngående avgift)
  {
    code: '6',
    rate: 'Variabel',
    description: 'Inngående avgift',
    whenToUse: 'Standard fradragsberettiget MVA på kjøp (både 25% og 15%). Brukes for generelle innkjøp hvor virksomheten har fradragsrett',
    category: 'incoming',
  },
  {
    code: '81',
    rate: '15%',
    description: 'Inngående avgift redusert sats',
    whenToUse: 'Fradrag for inngående MVA på kjøp med redusert sats (15%)',
    category: 'incoming',
  },
  {
    code: '83',
    rate: '25%',
    description: 'Inngående avgift alminnelig sats',
    whenToUse: 'Fradrag for inngående MVA på kjøp med alminnelig sats (25%)',
    category: 'incoming',
  },
  {
    code: '86',
    rate: '0%',
    description: 'Inngående avgift uten fradragsrett',
    whenToUse: 'Innkjøp der virksomheten ikke har fradragsrett for MVA (f.eks. finansielle tjenester)',
    category: 'incoming',
  },
  {
    code: '87',
    rate: '0%',
    description: 'Inngående avgift med delvis fradragsrett',
    whenToUse: 'Innkjøp hvor virksomheten kun har delvis fradragsrett for MVA (blandet virksomhet)',
    category: 'incoming',
  },
  {
    code: '88',
    rate: '25%',
    description: 'Inngående avgift tap på krav',
    whenToUse: 'MVA på tap på krav (kundefordringer som ikke blir betalt)',
    category: 'incoming',
  },
  {
    code: '89',
    rate: '0%',
    description: 'Justering av inngående avgift',
    whenToUse: 'Justeringer av tidligere beregnet inngående avgift',
    category: 'incoming',
  },
  
  // Exempt (Unntak og nullsats)
  {
    code: '0',
    rate: '0%',
    description: 'Unntak',
    whenToUse: 'Omsetning unntatt fra MVA-plikten (finansielle tjenester, helsestell, utdanning, ideelle organisasjoner, utleie av lokaler til boligformål)',
    category: 'exempt',
  },
  {
    code: '11',
    rate: '0%',
    description: 'Omsetning utenfor loven',
    whenToUse: 'Salg som faller utenfor merverdiavgiftsloven (lønn, hobbyvirksomhet, etc.)',
    category: 'exempt',
  },
  {
    code: '12',
    rate: '0%',
    description: 'Utleie av bygg og anlegg',
    whenToUse: 'Utleie av fast eiendom (bygninger, lokaler) som er unntatt MVA',
    category: 'exempt',
  },
  {
    code: '13',
    rate: '0%',
    description: 'Uttak og tilbakeføring',
    whenToUse: 'Uttak av varer og tjenester til privat bruk eller ikke fradragsberettiget formål',
    category: 'exempt',
  },
  
  // Export (Utførsel)
  {
    code: '1',
    rate: '0%',
    description: 'Utførsel innenfor EØS',
    whenToUse: 'Salg av varer til kunder i andre EU/EØS-land (eksport med 0% MVA)',
    category: 'export',
  },
  {
    code: '2',
    rate: '0%',
    description: 'Utførsel utenfor EØS',
    whenToUse: 'Salg av varer til kunder utenfor EU/EØS (eksport med 0% MVA)',
    category: 'export',
  },
  {
    code: '21',
    rate: '0%',
    description: 'Tjenester til utlandet',
    whenToUse: 'Salg av tjenester til kunder i utlandet som er unntatt MVA',
    category: 'export',
  },
];

const CATEGORY_LABELS = {
  outgoing: { label: 'Utgående avgift', color: 'bg-accent-blue/10 text-accent-blue' },
  incoming: { label: 'Inngående avgift', color: 'bg-accent-green/10 text-accent-green' },
  exempt: { label: 'Unntak', color: 'bg-gray-500/10 text-gray-400' },
  export: { label: 'Utførsel', color: 'bg-accent-yellow/10 text-accent-yellow' },
};

export const VatReference: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState<string>('');

  // Filter codes
  const filteredCodes = VAT_CODES.filter(code => {
    const matchesSearch = searchQuery === '' || 
      code.code.includes(searchQuery) ||
      code.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      code.whenToUse.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesCategory = filterCategory === '' || code.category === filterCategory;
    
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-100">MVA-kodereferanse</h1>
        <p className="text-sm text-gray-400 mt-1">
          Komplett oversikt over norske merverdiavgiftskoder (NS 4102)
        </p>
      </div>

      {/* Integration Note */}
      <div className="bg-accent-blue/10 border border-accent-blue/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-accent-blue mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h3 className="text-sm font-semibold text-accent-blue mb-1">Integrasjon</h3>
            <p className="text-sm text-gray-300">
              MVA-koder er integrert i kontoplan (AccountsManagement) og bokføringssystem (booking_service.py).
              Koder tildeles automatisk ved AI-basert fakturagodkjenning og kan overstyres manuelt.
            </p>
          </div>
        </div>
      </div>

      {/* Search & Filter */}
      <div className="bg-dark-card border border-dark-border rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Search */}
          <div className="relative">
            <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Søk på kode, beskrivelse eller bruk..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent-blue"
            />
          </div>

          {/* Filter by category */}
          <div>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-accent-blue"
            >
              <option value="">Alle kategorier</option>
              <option value="outgoing">Utgående avgift</option>
              <option value="incoming">Inngående avgift</option>
              <option value="exempt">Unntak</option>
              <option value="export">Utførsel</option>
            </select>
          </div>
        </div>
      </div>

      {/* VAT Codes Table */}
      <div className="bg-dark-card border border-dark-border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-dark-hover border-b border-dark-border">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider w-24">
                  MVA-kode
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider w-24">
                  Sats
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider w-48">
                  Beskrivelse
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Når skal den brukes
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider w-40">
                  Kategori
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-border">
              {filteredCodes.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                    Ingen MVA-koder funnet
                  </td>
                </tr>
              ) : (
                filteredCodes.map((code) => (
                  <tr key={code.code} className="hover:bg-dark-hover transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-lg font-bold text-accent-blue font-mono">{code.code}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-semibold text-gray-300">{code.rate}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm font-medium text-gray-100">{code.description}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-400 leading-relaxed">{code.whenToUse}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${CATEGORY_LABELS[code.category].color}`}>
                        {CATEGORY_LABELS[code.category].label}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Quick Reference Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-dark-card border border-dark-border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-accent-blue"></div>
            <h3 className="text-sm font-semibold text-gray-300">Mest brukte koder</h3>
          </div>
          <ul className="space-y-1 text-sm text-gray-400">
            <li><span className="font-mono text-accent-blue">5</span> - Salg 25%</li>
            <li><span className="font-mono text-accent-blue">3</span> - Salg 15%</li>
            <li><span className="font-mono text-accent-green">6</span> - Innkjøp (fradrag)</li>
            <li><span className="font-mono text-gray-400">0</span> - Unntak</li>
          </ul>
        </div>

        <div className="bg-dark-card border border-dark-border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-accent-yellow"></div>
            <h3 className="text-sm font-semibold text-gray-300">Eksport</h3>
          </div>
          <ul className="space-y-1 text-sm text-gray-400">
            <li><span className="font-mono text-accent-yellow">1</span> - EU/EØS</li>
            <li><span className="font-mono text-accent-yellow">2</span> - Utenfor EØS</li>
            <li><span className="font-mono text-accent-yellow">21</span> - Tjenester utland</li>
          </ul>
        </div>

        <div className="bg-dark-card border border-dark-border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-accent-green"></div>
            <h3 className="text-sm font-semibold text-gray-300">Snudd avregning</h3>
          </div>
          <ul className="space-y-1 text-sm text-gray-400">
            <li><span className="font-mono text-accent-green">51</span> - Import varer 25%</li>
            <li><span className="font-mono text-accent-green">52</span> - Tjenester 25%</li>
            <li><span className="font-mono text-accent-green">31</span> - Tjenester 15%</li>
          </ul>
        </div>

        <div className="bg-dark-card border border-dark-border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-gray-500"></div>
            <h3 className="text-sm font-semibold text-gray-300">Spesialtilfeller</h3>
          </div>
          <ul className="space-y-1 text-sm text-gray-400">
            <li><span className="font-mono text-gray-400">86</span> - Uten fradragsrett</li>
            <li><span className="font-mono text-gray-400">87</span> - Delvis fradrag</li>
            <li><span className="font-mono text-gray-400">88</span> - Tap på krav</li>
          </ul>
        </div>
      </div>

      {/* Footer Note */}
      <div className="bg-dark-card border border-dark-border rounded-lg p-4">
        <p className="text-xs text-gray-500">
          <strong className="text-gray-400">Merk:</strong> Denne oversikten følger Skatteetatens MVA-kodeverk for
          merverdiavgiftsmelding (tidligere omsetningsoppgave). For komplekse MVA-tilfeller, konsulter regnskapsfører
          eller Skatteetaten. Sist oppdatert: 2024 (NS 4102 standard).
        </p>
      </div>
    </div>
  );
};

export default VatReference;
