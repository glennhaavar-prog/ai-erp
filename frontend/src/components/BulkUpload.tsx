/**
 * BulkUpload Component - CSV/Excel Bulk Import
 * Reusable component for importing suppliers and customers
 */
'use client';

import React, { useState, useRef } from 'react';
import { toast } from 'sonner';
import {
  ArrowUpTrayIcon,
  XMarkIcon,
  DocumentArrowDownIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/button';

interface BulkUploadResult {
  created: number;
  skipped: number;
  error_count: number;
  errors: Array<{ row: number; error: string }>;
}

interface BulkUploadProps {
  type: 'suppliers' | 'customers';
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const BulkUpload: React.FC<BulkUploadProps> = ({
  type,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [result, setResult] = useState<BulkUploadResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const entityName = type === 'suppliers' ? 'leverandører' : 'kunder';
  const entityNameSingular = type === 'suppliers' ? 'leverandør' : 'kunde';

  if (!isOpen) return null;

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file: File) => {
    // Validate file type
    const validExtensions = ['.csv', '.xlsx', '.xls'];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!validExtensions.includes(fileExtension)) {
      toast.error('Ugyldig filformat. Kun CSV eller Excel (.xlsx, .xls) er støttet.');
      return;
    }

    // Upload file
    setUploading(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const endpoint = type === 'suppliers' 
        ? '/api/contacts/suppliers/bulk'
        : '/api/contacts/customers/bulk';

      const response = await fetch(`${endpoint}?filename=${encodeURIComponent(file.name)}`, {
        method: 'POST',
        body: file,
        headers: {
          // Let browser set Content-Type for file upload
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Import feilet');
      }

      const data: BulkUploadResult = await response.json();
      setResult(data);

      if (data.created > 0) {
        toast.success(`✅ ${data.created} ${entityName} importert!`);
        onSuccess();
      }

      if (data.error_count > 0) {
        toast.warning(`⚠️ ${data.error_count} feil oppstod under import`);
      }

    } catch (error: any) {
      console.error('Upload error:', error);
      toast.error(error.message || 'Kunne ikke laste opp fil');
    } finally {
      setUploading(false);
    }
  };

  const downloadTemplate = () => {
    let csv: string;
    let filename: string;

    if (type === 'suppliers') {
      csv = `navn,org_nummer,epost,telefon,adresse,postnummer,poststed,land,kontonummer,betalingsbetingelser,leverandor_type
Eksempel Leverandør AS,987654321,post@leverandor.no,12345678,Gateveien 1,8000,Bodø,Norge,12345678901,30 dager,goods
Test Leverandør 2 AS,123456789,test@lev.no,87654321,Veien 2,0150,Oslo,Norge,98765432109,14 dager,services`;
      filename = 'leverandorer_mal.csv';
    } else {
      csv = `navn,org_nummer,epost,telefon,adresse,postnummer,poststed,land,kontonummer,betalingsbetingelser,kunde_type
Eksempel Kunde AS,123456789,post@kunde.no,87654321,Kundeveien 1,8000,Bodø,Norge,98765432109,14 dager,b2b
Test Kunde 2,,,99887766,Privat 2,0150,Oslo,Norge,,30 dager,b2c`;
      filename = 'kunder_mal.csv';
    }

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const columnInfo = type === 'suppliers' ? [
    { name: 'navn', required: true, desc: 'Leverandørens navn' },
    { name: 'org_nummer', required: true, desc: '9-sifret organisasjonsnummer' },
    { name: 'epost', required: false, desc: 'E-postadresse' },
    { name: 'telefon', required: false, desc: 'Telefonnummer' },
    { name: 'adresse', required: false, desc: 'Gateadresse' },
    { name: 'postnummer', required: false, desc: 'Postnummer (4 siffer)' },
    { name: 'poststed', required: false, desc: 'Poststed/by' },
    { name: 'land', required: false, desc: 'Land (standard: Norge)' },
    { name: 'kontonummer', required: false, desc: 'Bankkonto (11 siffer)' },
    { name: 'betalingsbetingelser', required: false, desc: 'F.eks. "30 dager"' },
    { name: 'leverandor_type', required: false, desc: 'goods eller services' },
  ] : [
    { name: 'navn', required: true, desc: 'Kundens navn' },
    { name: 'org_nummer', required: false, desc: '9-sifret org.nr (B2B)' },
    { name: 'epost', required: false, desc: 'E-postadresse' },
    { name: 'telefon', required: false, desc: 'Telefonnummer' },
    { name: 'adresse', required: false, desc: 'Gateadresse' },
    { name: 'postnummer', required: false, desc: 'Postnummer (4 siffer)' },
    { name: 'poststed', required: false, desc: 'Poststed/by' },
    { name: 'land', required: false, desc: 'Land (standard: Norge)' },
    { name: 'betalingsbetingelser', required: false, desc: 'F.eks. "14 dager"' },
    { name: 'kunde_type', required: false, desc: 'b2b eller b2c' },
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">
            Last opp {entityName}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Upload Area */}
          {!result && (
            <>
              <div
                className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                  dragActive
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <ArrowUpTrayIcon className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                <p className="text-lg text-gray-700 mb-2">
                  Dra og slipp fil her, eller klikk for å velge
                </p>
                <p className="text-sm text-gray-500 mb-4">
                  CSV eller Excel (.xlsx, .xls)
                </p>
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  variant="default"
                >
                  {uploading ? 'Importerer...' : 'Velg fil'}
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileInput}
                  className="hidden"
                />
              </div>

              {/* Download Template */}
              <div className="flex items-center justify-center">
                <button
                  onClick={downloadTemplate}
                  className="flex items-center gap-2 text-blue-600 hover:text-blue-800"
                >
                  <DocumentArrowDownIcon className="w-5 h-5" />
                  Last ned mal (CSV)
                </button>
              </div>

              {/* Column Info */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-3">
                  CSV-kolonner
                </h3>
                <div className="space-y-1 text-sm">
                  {columnInfo.map((col) => (
                    <div key={col.name} className="flex">
                      <span className="font-mono text-gray-700 w-48">
                        {col.name}
                        {col.required && (
                          <span className="text-red-500 ml-1">*</span>
                        )}
                      </span>
                      <span className="text-gray-600">{col.desc}</span>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-gray-500 mt-3">
                  * = Obligatorisk felt
                </p>
              </div>
            </>
          )}

          {/* Result Summary */}
          {result && (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <CheckCircleIcon className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-semibold text-green-900 mb-2">
                      Import fullført!
                    </h3>
                    <ul className="text-sm text-green-800 space-y-1">
                      <li>✅ {result.created} {entityName} opprettet</li>
                      {result.skipped > 0 && (
                        <li>⏭️ {result.skipped} hoppet over (eksisterer allerede)</li>
                      )}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Errors */}
              {result.error_count > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <ExclamationTriangleIcon className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <h3 className="font-semibold text-yellow-900 mb-2">
                        {result.error_count} feil:
                      </h3>
                      <div className="max-h-40 overflow-y-auto space-y-1 text-sm text-yellow-800">
                        {result.errors.map((err, idx) => (
                          <div key={idx}>
                            • Rad {err.row}: {err.error}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3">
                <Button
                  onClick={() => {
                    setResult(null);
                    onClose();
                  }}
                  variant="default"
                  className="flex-1"
                >
                  Ferdig
                </Button>
                <Button
                  onClick={() => setResult(null)}
                  variant="outline"
                  className="flex-1"
                >
                  Last opp flere
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
