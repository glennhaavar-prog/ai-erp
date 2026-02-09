'use client';

import React, { useState, useEffect } from 'react';
import { XMarkIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';

interface PdfViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  invoiceId: string | null;
  documentId: string | null;
  invoiceNumber?: string;
}

interface DocumentInfo {
  document_id?: string;
  filename?: string;
  mime_type?: string;
  download_url?: string | null;
  demo_mode?: boolean;
  message?: string;
  has_pdf?: boolean;
}

export const PdfViewerModal: React.FC<PdfViewerModalProps> = ({
  isOpen,
  onClose,
  invoiceId,
  documentId,
  invoiceNumber
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [documentInfo, setDocumentInfo] = useState<DocumentInfo | null>(null);

  useEffect(() => {
    if (!isOpen) {
      setLoading(true);
      setError(null);
      setDocumentInfo(null);
      return;
    }

    const fetchDocument = async () => {
      setLoading(true);
      setError(null);

      try {
        let url: string;
        
        // Use invoice ID if provided, otherwise use document ID
        if (invoiceId) {
          url = `http://localhost:8000/api/documents/invoice/${invoiceId}/pdf`;
        } else if (documentId) {
          url = `http://localhost:8000/api/documents/${documentId}/url`;
        } else {
          throw new Error('No invoice ID or document ID provided');
        }

        const response = await fetch(url);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data: DocumentInfo = await response.json();
        setDocumentInfo(data);

        // If no PDF available
        if (data.has_pdf === false || data.demo_mode) {
          setError(data.message || 'PDF not available');
        }

      } catch (err) {
        console.error('Error fetching document:', err);
        setError(err instanceof Error ? err.message : 'Failed to load PDF');
      } finally {
        setLoading(false);
      }
    };

    fetchDocument();
  }, [isOpen, invoiceId, documentId]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md">
      <div className="relative w-full h-full max-w-6xl max-h-screen p-4">
        {/* Modal Header */}
        <div className="flex items-center justify-between bg-card/95 backdrop-blur-xl border-b border-border/50 p-4 rounded-t-lg">
          <div>
            <h2 className="text-xl font-bold text-gray-100">
              PDF Bilag
              {invoiceNumber && <span className="text-gray-400 ml-2">#{invoiceNumber}</span>}
            </h2>
            {documentInfo?.filename && (
              <p className="text-sm text-gray-400 mt-1">{documentInfo.filename}</p>
            )}
          </div>
          <div className="flex items-center gap-2">
            {documentInfo?.download_url && (
              <a
                href={documentInfo.download_url}
                download={documentInfo.filename}
                className="p-2 hover:bg-dark-hover rounded-lg text-gray-300 transition-colors"
                title="Last ned PDF"
              >
                <ArrowDownTrayIcon className="w-5 h-5" />
              </a>
            )}
            <button
              onClick={onClose}
              className="p-2 hover:bg-dark-hover rounded-lg text-gray-300 transition-colors"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Modal Content */}
        <div className="bg-card/95 backdrop-blur-xl h-[calc(100%-4rem)] rounded-b-lg overflow-hidden shadow-2xl shadow-black/20">
          {loading && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-blue mx-auto mb-4"></div>
                <p className="text-gray-400">Laster PDF...</p>
              </div>
            </div>
          )}

          {error && !loading && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md p-6">
                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 mb-4">
                  <p className="text-yellow-400 font-medium mb-2">⚠️ PDF ikke tilgjengelig</p>
                  <p className="text-gray-400 text-sm">{error}</p>
                </div>
                <p className="text-gray-500 text-sm">
                  Dette er demo-data. I produksjon vil fakturaer lagres i S3 og vises her.
                </p>
              </div>
            </div>
          )}

          {!loading && !error && documentInfo?.download_url && (
            <iframe
              src={documentInfo.download_url}
              className="w-full h-full border-0"
              title="PDF Viewer"
            />
          )}
        </div>
      </div>
    </div>
  );
};
