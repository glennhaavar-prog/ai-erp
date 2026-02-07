'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  MenuItem,
  Alert,
  Stack,
  CircularProgress,
  LinearProgress,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Chip,
} from '@mui/material';
import { useDropzone } from 'react-dropzone';
import { useRouter } from 'next/navigation';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import DeleteIcon from '@mui/icons-material/Delete';
import DescriptionIcon from '@mui/icons-material/Description';

interface Client {
  id: string;
  name: string;
  org_number: string;
}

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
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<string>('');
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/clients/');
      if (!response.ok) throw new Error('Failed to fetch clients');
      const clientsData = await response.json();
      setClients(clientsData);
      if (clientsData.length > 0) {
        setSelectedClient(clientsData[0].id);
      }
    } catch (err) {
      console.error('Error fetching clients:', err);
      setError('Kunne ikke laste klienter');
    }
  };

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
    if (!selectedClient) {
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
      formData.append('client_id', selectedClient);

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
        return <CheckCircleIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      case 'uploading':
        return <CircularProgress size={24} />;
      default:
        return <DescriptionIcon />;
    }
  };

  const getStatusColor = (status: UploadFile['status']) => {
    switch (status) {
      case 'success':
        return 'success';
      case 'error':
        return 'error';
      case 'uploading':
        return 'info';
      default:
        return 'default';
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
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Last opp leverandørfakturaer
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Velg klient
          </Typography>

          <TextField
            select
            label="Klient"
            value={selectedClient}
            onChange={(e) => setSelectedClient(e.target.value)}
            fullWidth
            sx={{ mb: 2 }}
          >
            {clients.map((client) => (
              <MenuItem key={client.id} value={client.id}>
                {client.name} ({client.org_number})
              </MenuItem>
            ))}
          </TextField>

          <Paper
            {...getRootProps()}
            sx={{
              p: 4,
              textAlign: 'center',
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'divider',
              bgcolor: isDragActive ? 'action.hover' : 'background.paper',
              cursor: 'pointer',
              transition: 'all 0.2s',
              '&:hover': {
                borderColor: 'primary.main',
                bgcolor: 'action.hover',
              },
            }}
          >
            <input {...getInputProps()} />
            <CloudUploadIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive
                ? 'Slipp filene her...'
                : 'Dra og slipp PDF-filer her, eller klikk for å velge'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Kun PDF-filer er støttet
            </Typography>
          </Paper>

          {files.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
                <Button
                  variant="contained"
                  onClick={uploadAll}
                  disabled={!hasPendingFiles || !selectedClient}
                >
                  Last opp alle ({files.filter((f) => f.status === 'pending').length})
                </Button>
                {hasSuccessfulUploads && (
                  <Button variant="outlined" onClick={goToReviewQueue}>
                    Gå til Review Queue
                  </Button>
                )}
                <Button
                  variant="outlined"
                  color="error"
                  onClick={() => setFiles([])}
                  disabled={files.some((f) => f.status === 'uploading')}
                >
                  Fjern alle
                </Button>
              </Stack>

              <List>
                {files.map((uploadFile) => (
                  <ListItem
                    key={uploadFile.id}
                    secondaryAction={
                      <IconButton
                        edge="end"
                        aria-label="delete"
                        onClick={() => removeFile(uploadFile.id)}
                        disabled={uploadFile.status === 'uploading'}
                      >
                        <DeleteIcon />
                      </IconButton>
                    }
                  >
                    <ListItemIcon>{getStatusIcon(uploadFile.status)}</ListItemIcon>
                    <ListItemText
                      primary={uploadFile.file.name}
                      secondary={
                        <Stack spacing={1} sx={{ mt: 1 }}>
                          {uploadFile.status === 'uploading' && (
                            <LinearProgress
                              variant="indeterminate"
                              sx={{ width: '100%' }}
                            />
                          )}
                          <Stack direction="row" spacing={1} alignItems="center">
                            <Chip
                              label={getStatusText(uploadFile.status)}
                              size="small"
                              color={getStatusColor(uploadFile.status)}
                            />
                            {uploadFile.confidence && (
                              <Chip
                                label={`Confidence: ${(uploadFile.confidence * 100).toFixed(0)}%`}
                                size="small"
                                color={uploadFile.confidence >= 0.8 ? 'success' : 'warning'}
                              />
                            )}
                            {uploadFile.error && (
                              <Typography variant="caption" color="error">
                                {uploadFile.error}
                              </Typography>
                            )}
                          </Stack>
                        </Stack>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {allFilesProcessed && hasSuccessfulUploads && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            {files.filter((f) => f.status === 'success').length} faktura(er) er klar
            for gjennomgang i Review Queue.
          </Typography>
          <Button
            variant="text"
            onClick={goToReviewQueue}
            sx={{ mt: 1 }}
            size="small"
          >
            Gå til Review Queue →
          </Button>
        </Alert>
      )}
    </Box>
  );
}
