'use client';

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useRouter } from 'next/navigation';
import { useClient } from '@/contexts/ClientContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import {
  CloudUpload,
  CheckCircle,
  AlertCircle,
  Trash2,
  FileText,
  Loader2,
} from 'lucide-react';

interface UploadFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
  invoiceId?: string;
  confidence?: number;
}

export default function UploadPage() {
  const router = useRouter();
  const { selectedClient } = useClient();
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadFile[] = acceptedFiles.map((file) => ({
      file,
      id: Math.random().toString(36).substring(7),
      status: 'pending',
      progress: 0,
    }));
    setFiles((prev) => [...prev, ...newFiles]);
    setError(null);
    setSuccess(null);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    multiple: true,
  });

  const uploadFile = async (uploadFile: UploadFile) => {
    if (!selectedClient || !selectedClient.id) {
      setError('Vennligst velg en klient');
      return;
    }

    // Update status to uploading
    setFiles((prev) =>
      prev.map((f) =>
        f.id === uploadFile.id ? { ...f, status: 'uploading', progress: 0 } : f
      )
    );

    try {
      const formData = new FormData();
      formData.append('file', uploadFile.file);
      formData.append('client_id', selectedClient.id);

      const response = await fetch('http://localhost:8000/api/invoices/upload/', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const result = await response.json();

      // Update status to success
      setFiles((prev) =>
        prev.map((f) =>
          f.id === uploadFile.id
            ? {
                ...f,
                status: 'success',
                progress: 100,
                invoiceId: result.invoice_id,
                confidence: result.confidence_score,
              }
            : f
        )
      );

      setSuccess(
        `Faktura lastet opp! Confidence: ${(result.confidence_score * 100).toFixed(0)}%`
      );
    } catch (err) {
      console.error('Upload error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Upload feilet';

      setFiles((prev) =>
        prev.map((f) =>
          f.id === uploadFile.id
            ? { ...f, status: 'error', progress: 0, error: errorMessage }
            : f
        )
      );

      setError(errorMessage);
    }
  };

  const uploadAll = async () => {
    const pendingFiles = files.filter((f) => f.status === 'pending');

    for (const file of pendingFiles) {
      await uploadFile(file);
      // Small delay between uploads
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
  };

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const goToReviewQueue = () => {
    router.push('/review-queue');
  };

  const getStatusIcon = (status: UploadFile['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'uploading':
        return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
      default:
        return <FileText className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusBadgeVariant = (status: UploadFile['status']) => {
    switch (status) {
      case 'success':
        return 'default';
      case 'error':
        return 'destructive';
      case 'uploading':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  const getStatusText = (status: UploadFile['status']) => {
    switch (status) {
      case 'success':
        return 'Lastet opp';
      case 'error':
        return 'Feil';
      case 'uploading':
        return 'Laster opp...';
      default:
        return 'Venter';
    }
  };

  const hasSuccessfulUploads = files.some((f) => f.status === 'success');
  const hasPendingFiles = files.some((f) => f.status === 'pending');
  const allFilesProcessed = files.length > 0 && !hasPendingFiles;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Last opp leverandørfakturaer</h1>

      {!selectedClient && (
        <Alert className="mb-6">
          <AlertDescription>
            Velg en klient fra menyen øverst for å laste opp fakturaer
          </AlertDescription>
        </Alert>
      )}

      {selectedClient && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Laster opp for: {selectedClient.name}</CardTitle>
          </CardHeader>
          <CardContent>
            <div
              {...getRootProps()}
              className={`
                p-8 text-center border-2 border-dashed rounded-lg cursor-pointer
                transition-all duration-200
                ${
                  isDragActive
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary hover:bg-accent'
                }
              `}
            >
              <input {...getInputProps()} />
              <CloudUpload className="h-16 w-16 mx-auto mb-4 text-primary" />
              <h3 className="text-lg font-semibold mb-2">
                {isDragActive
                  ? 'Slipp filene her...'
                  : 'Dra og slipp PDF-filer her, eller klikk for å velge'}
              </h3>
              <p className="text-sm text-muted-foreground">
                Kun PDF-filer er støttet
              </p>
            </div>

            {files.length > 0 && (
              <div className="mt-6">
                <div className="flex gap-2 mb-4">
                  <Button
                    onClick={uploadAll}
                    disabled={!hasPendingFiles || !selectedClient}
                  >
                    Last opp alle ({files.filter((f) => f.status === 'pending').length})
                  </Button>
                  {hasSuccessfulUploads && (
                    <Button variant="outline" onClick={goToReviewQueue}>
                      Gå til Review Queue
                    </Button>
                  )}
                  <Button
                    variant="destructive"
                    onClick={() => setFiles([])}
                    disabled={files.some((f) => f.status === 'uploading')}
                  >
                    Fjern alle
                  </Button>
                </div>

                <ul className="space-y-4">
                  {files.map((uploadFile) => (
                    <li
                      key={uploadFile.id}
                      className="flex items-start gap-3 p-4 border rounded-lg"
                    >
                      <div className="mt-0.5">{getStatusIcon(uploadFile.status)}</div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{uploadFile.file.name}</p>
                        <div className="mt-2 space-y-2">
                          {uploadFile.status === 'uploading' && (
                            <Progress value={undefined} className="h-2" />
                          )}
                          <div className="flex items-center gap-2 flex-wrap">
                            <Badge variant={getStatusBadgeVariant(uploadFile.status) as any}>
                              {getStatusText(uploadFile.status)}
                            </Badge>
                            {uploadFile.confidence && (
                              <Badge
                                variant={uploadFile.confidence >= 0.8 ? 'default' : 'secondary'}
                              >
                                Confidence: {(uploadFile.confidence * 100).toFixed(0)}%
                              </Badge>
                            )}
                            {uploadFile.error && (
                              <span className="text-sm text-red-500">
                                {uploadFile.error}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => removeFile(uploadFile.id)}
                        disabled={uploadFile.status === 'uploading'}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="mb-6">
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      {allFilesProcessed && hasSuccessfulUploads && (
        <Alert className="mb-6">
          <AlertDescription>
            <p className="mb-2">
              {files.filter((f) => f.status === 'success').length} faktura(er) er klar
              for gjennomgang i Review Queue.
            </p>
            <Button variant="link" onClick={goToReviewQueue} className="p-0 h-auto">
              Gå til Review Queue →
            </Button>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
