'use client';

import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, XCircle, AlertCircle, ArrowRight, Loader2 } from 'lucide-react';

interface ProcessingStep {
  step: string;
  status: string;
  message?: string;
  errors?: string[];
  warnings?: string[];
  invoice_id?: string;
  vendor_name?: string;
  amount?: any;
  confidence?: number;
  review_queue_id?: string;
}

interface TestResult {
  success: boolean;
  test_mode: boolean;
  timestamp: string;
  steps: ProcessingStep[];
  summary?: {
    invoice_id: string;
    ehf_invoice_id: string;
    vendor_name: string;
    total_amount: number;
    currency: string;
    processing_complete: boolean;
  };
  error?: string;
}

export default function EHFTestPage() {
  const [xmlContent, setXmlContent] = useState('');
  const [xmlFile, setXmlFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TestResult | null>(null);
  const [activeTab, setActiveTab] = useState<'upload' | 'paste'>('upload');

  const sampleFiles = [
    { name: 'Simple Invoice (25% VAT)', file: 'ehf_sample_1_simple.xml' },
    { name: 'Multi-line (Different VAT rates)', file: 'ehf_sample_2_multi_line.xml' },
    { name: 'Export (0% VAT)', file: 'ehf_sample_3_zero_vat.xml' },
    { name: 'Reverse Charge', file: 'ehf_sample_4_reverse_charge.xml' },
    { name: 'Credit Note', file: 'ehf_sample_5_credit_note.xml' },
  ];

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setXmlFile(file);
      // Read file content for preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setXmlContent(e.target?.result as string);
      };
      reader.readAsText(file);
    }
  };

  const loadSampleFile = async (filename: string) => {
    try {
      const response = await fetch(`/api/test/samples/${filename}`);
      if (response.ok) {
        const content = await response.text();
        setXmlContent(content);
        setActiveTab('paste');
      } else {
        // If samples endpoint doesn't exist, load from fixtures
        alert(`Sample files should be at: backend/tests/fixtures/ehf/${filename}`);
      }
    } catch (error) {
      console.error('Failed to load sample:', error);
      alert(`Failed to load sample file. Please use: backend/tests/fixtures/ehf/${filename}`);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setResult(null);

    try {
      let content = xmlContent;

      // If file is selected, use that
      if (xmlFile && activeTab === 'upload') {
        const reader = new FileReader();
        content = await new Promise<string>((resolve) => {
          reader.onload = (e) => resolve(e.target?.result as string);
          reader.readAsText(xmlFile);
        });
      }

      if (!content.trim()) {
        alert('Please provide XML content');
        setLoading(false);
        return;
      }

      // Send to test endpoint
      const response = await fetch('/api/test/ehf/send-raw', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ xml_content: content }),
      });

      const data = await response.json();
      setResult(data);
    } catch (error: any) {
      setResult({
        success: false,
        test_mode: true,
        timestamp: new Date().toISOString(),
        steps: [],
        error: error.message || 'Network error',
      });
    } finally {
      setLoading(false);
    }
  };

  const getStepIcon = (status: string) => {
    if (status.includes('✅')) return <CheckCircle className="w-5 h-5 text-green-500" />;
    if (status.includes('❌')) return <XCircle className="w-5 h-5 text-red-500" />;
    if (status.includes('⚠️')) return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    return <ArrowRight className="w-5 h-5 text-blue-500" />;
  };

  const getStepColor = (status: string) => {
    if (status.includes('✅')) return 'border-green-200 bg-green-50';
    if (status.includes('❌')) return 'border-red-200 bg-red-50';
    if (status.includes('⚠️')) return 'border-yellow-200 bg-yellow-50';
    return 'border-blue-200 bg-blue-50';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center gap-3 mb-2">
            <FileText className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">EHF Invoice Tester</h1>
          </div>
          <p className="text-gray-600">
            Test EHF invoice processing end-to-end. Send EHF XML and see it parsed, validated, and processed through the full pipeline.
          </p>
        </div>

        {/* Input Section */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Send Test Invoice</h2>

          {/* Tabs */}
          <div className="flex gap-2 mb-4 border-b">
            <button
              onClick={() => setActiveTab('upload')}
              className={`px-4 py-2 font-medium border-b-2 transition-colors ${
                activeTab === 'upload'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <Upload className="w-4 h-4 inline mr-2" />
              Upload File
            </button>
            <button
              onClick={() => setActiveTab('paste')}
              className={`px-4 py-2 font-medium border-b-2 transition-colors ${
                activeTab === 'paste'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <FileText className="w-4 h-4 inline mr-2" />
              Paste XML
            </button>
          </div>

          {/* Upload Tab */}
          {activeTab === 'upload' && (
            <div className="space-y-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
                <input
                  type="file"
                  accept=".xml,text/xml,application/xml"
                  onChange={handleFileChange}
                  className="hidden"
                  id="xml-upload"
                />
                <label htmlFor="xml-upload" className="cursor-pointer">
                  <Upload className="w-12 h-12 mx-auto text-gray-400 mb-3" />
                  <p className="text-lg font-medium text-gray-700">
                    {xmlFile ? xmlFile.name : 'Click to upload EHF XML file'}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">or drag and drop</p>
                </label>
              </div>

              {/* Sample Files */}
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Or use sample files:</p>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                  {sampleFiles.map((sample) => (
                    <button
                      key={sample.file}
                      onClick={() => loadSampleFile(sample.file)}
                      className="px-3 py-2 text-sm bg-blue-50 hover:bg-blue-100 text-blue-700 rounded border border-blue-200 transition-colors text-left"
                    >
                      {sample.name}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Paste Tab */}
          {activeTab === 'paste' && (
            <div>
              <textarea
                value={xmlContent}
                onChange={(e) => setXmlContent(e.target.value)}
                placeholder="Paste EHF XML content here..."
                className="w-full h-64 p-4 font-mono text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          )}

          {/* Submit Button */}
          <button
            onClick={handleSubmit}
            disabled={loading || (!xmlFile && !xmlContent)}
            className="mt-4 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <ArrowRight className="w-5 h-5" />
                Send & Process Invoice
              </>
            )}
          </button>
        </div>

        {/* Results Section */}
        {result && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Processing Result</h2>

            {/* Overall Status */}
            <div
              className={`p-4 rounded-lg mb-6 ${
                result.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
              }`}
            >
              <div className="flex items-center gap-3">
                {result.success ? (
                  <CheckCircle className="w-8 h-8 text-green-600" />
                ) : (
                  <XCircle className="w-8 h-8 text-red-600" />
                )}
                <div>
                  <h3 className="text-lg font-semibold">
                    {result.success ? 'Success!' : 'Failed'}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {result.success
                      ? 'Invoice processed successfully through full pipeline'
                      : result.error || 'Processing failed - see details below'}
                  </p>
                </div>
              </div>
            </div>

            {/* Processing Steps */}
            {result.steps && result.steps.length > 0 && (
              <div className="space-y-3 mb-6">
                <h3 className="font-semibold text-gray-700">Processing Steps:</h3>
                {result.steps.map((step, idx) => (
                  <div key={idx} className={`border rounded-lg p-4 ${getStepColor(step.status)}`}>
                    <div className="flex items-start gap-3">
                      {getStepIcon(step.status)}
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium capitalize">{step.step.replace('_', ' ')}</span>
                          <span className="text-sm">{step.status}</span>
                        </div>
                        {step.message && <p className="text-sm text-gray-700 mt-1">{step.message}</p>}

                        {/* Invoice Details */}
                        {step.invoice_id && (
                          <div className="mt-2 text-sm space-y-1">
                            <p>
                              <span className="font-medium">Invoice ID:</span> {step.invoice_id}
                            </p>
                            {step.vendor_name && (
                              <p>
                                <span className="font-medium">Vendor:</span> {step.vendor_name}
                              </p>
                            )}
                            {step.amount && (
                              <p>
                                <span className="font-medium">Amount:</span> {step.amount.total} {step.amount.currency}
                              </p>
                            )}
                          </div>
                        )}

                        {/* AI Processing */}
                        {step.confidence !== undefined && (
                          <div className="mt-2 text-sm">
                            <p>
                              <span className="font-medium">Confidence:</span> {step.confidence}%
                            </p>
                          </div>
                        )}

                        {/* Errors */}
                        {step.errors && step.errors.length > 0 && (
                          <div className="mt-2 space-y-1">
                            {step.errors.map((error, i) => (
                              <p key={i} className="text-sm text-red-700">
                                ✗ {error}
                              </p>
                            ))}
                          </div>
                        )}

                        {/* Warnings */}
                        {step.warnings && step.warnings.length > 0 && (
                          <div className="mt-2 space-y-1">
                            {step.warnings.map((warning, i) => (
                              <p key={i} className="text-sm text-yellow-700">
                                ⚠️  {warning}
                              </p>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Summary */}
            {result.summary && (
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <h3 className="font-semibold text-gray-700 mb-3">Summary:</h3>
                <dl className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <dt className="font-medium text-gray-600">Invoice ID:</dt>
                    <dd className="text-gray-900">{result.summary.invoice_id}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-gray-600">EHF Invoice ID:</dt>
                    <dd className="text-gray-900">{result.summary.ehf_invoice_id}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-gray-600">Vendor:</dt>
                    <dd className="text-gray-900">{result.summary.vendor_name}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-gray-600">Amount:</dt>
                    <dd className="text-gray-900">
                      {result.summary.total_amount} {result.summary.currency}
                    </dd>
                  </div>
                </dl>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
