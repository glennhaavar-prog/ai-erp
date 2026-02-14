'use client';

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
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

interface PDFUploadProps {
  /** Upload endpoint - defaults to /api/review-queue/upload */
  uploadEndpoint?: string;
  /** Callback when upload succeeds */
  onUploadSuccess?: (result: any) => void;
  /** Show compact version */
  compact?: boolean;
  /** Custom title */
  title?: string;
}

export function PDFUpload({
  uploadEndpoint = '/api/review-queue/upload',
  onUploadSuccess,
  compact = false,
  title = 'Last opp PDF-filer',
}: PDFUploadProps) {
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

      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}${uploadEndpoint}`, {
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
                invoiceId: result.invoice_id || result.id,
                confidence: result.confidence_score || result.ai_confidence,
              }
            : f
        )
      );

      const confidenceScore = result.confidence_score || result.ai_confidence || 0;
      setSuccess(
        `Fil lastet opp! Confidence: ${(confidenceScore * 100).toFixed(0)}%`
      );

      if (onUploadSuccess) {
        onUploadSuccess(result);
      }
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

  const hasPendingFiles = files.some((f) => f.status === 'pending');

  if (!selectedClient) {
    return (
      <Alert>
        <AlertDescription>
          Velg en klient fra menyen for å laste opp filer
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className={compact ? '' : 'space-y-4'}>
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert>
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      <Card>
        {!compact && (
          <CardHeader>
            <CardTitle>{title}</CardTitle>
          </CardHeader>
        )}
        <CardContent className={compact ? 'pt-6' : ''}>
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
            <CloudUpload className="h-12 w-12 mx-auto mb-3 text-primary" />
            <h3 className="text-base font-semibold mb-1">
              {isDragActive
                ? 'Slipp filene her...'
                : 'Dra og slipp PDF-filer her, eller klikk for å velge'}
            </h3>
            <p className="text-sm text-muted-foreground">
              Kun PDF-filer er støttet
            </p>
          </div>

          {files.length > 0 && (
            <div className="mt-4">
              <div className="flex gap-2 mb-4">
                <Button
                  onClick={uploadAll}
                  disabled={!hasPendingFiles || !selectedClient}
                  size="sm"
                >
                  Last opp alle ({files.filter((f) => f.status === 'pending').length})
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setFiles([])}
                  disabled={files.some((f) => f.status === 'uploading')}
                  size="sm"
                >
                  Fjern alle
                </Button>
              </div>

              <ul className="space-y-3">
                {files.map((uploadFile) => (
                  <li
                    key={uploadFile.id}
                    className="flex items-start gap-3 p-3 border rounded-lg"
                  >
                    <div className="mt-0.5">{getStatusIcon(uploadFile.status)}</div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{uploadFile.file.name}</p>
                      <div className="mt-2 space-y-2">
                        {uploadFile.status === 'uploading' && (
                          <Progress value={undefined} className="h-1.5" />
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
                            <span className="text-xs text-red-500">
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
    </div>
  );
}
