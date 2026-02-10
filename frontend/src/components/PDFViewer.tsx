"use client";

import { useState } from "react";

interface PDFViewerProps {
  documentUrl: string | null;
  documentType?: string;
}

export default function PDFViewer({ documentUrl, documentType }: PDFViewerProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  if (!documentUrl) {
    return (
      <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
          Ingen dokumentasjon vedlagt
        </p>
      </div>
    );
  }

  const isPDF = documentType?.toLowerCase().includes("pdf") || documentUrl.toLowerCase().endsWith(".pdf");

  if (!isPDF) {
    // Show image or other document types
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        <div className="p-4 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">
            📎 Vedlagt dokumentasjon
          </h3>
          {documentType && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {documentType}
            </p>
          )}
        </div>
        <div className="p-4">
          <img
            src={documentUrl}
            alt="Document"
            className="max-w-full h-auto rounded"
            onLoad={() => setLoading(false)}
            onError={() => {
              setLoading(false);
              setError("Kunne ikke laste dokumentet");
            }}
          />
          {loading && (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          )}
          {error && (
            <div className="text-center text-red-600 dark:text-red-400">
              {error}
            </div>
          )}
        </div>
        <div className="p-4 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
          <a
            href={documentUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            Åpne i ny fane →
          </a>
        </div>
      </div>
    );
  }

  // PDF viewer
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      <div className="p-4 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
        <div>
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">
            📄 PDF Dokumentasjon
          </h3>
          {documentType && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {documentType}
            </p>
          )}
        </div>
        <a
          href={documentUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
        >
          Åpne i ny fane
        </a>
      </div>
      
      <div className="relative bg-gray-100 dark:bg-gray-900" style={{ height: "600px" }}>
        {loading && (
          <div className="absolute inset-0 flex justify-center items-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}
        
        <iframe
          src={documentUrl}
          className="w-full h-full"
          title="PDF Document"
          onLoad={() => setLoading(false)}
          onError={() => {
            setLoading(false);
            setError("Kunne ikke laste PDF");
          }}
        />
        
        {error && (
          <div className="absolute inset-0 flex justify-center items-center bg-white dark:bg-gray-800">
            <div className="text-center">
              <svg
                className="mx-auto h-12 w-12 text-red-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <p className="mt-2 text-sm text-red-600 dark:text-red-400">
                {error}
              </p>
              <a
                href={documentUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 inline-block text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                Prøv å åpne i ny fane
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
