'use client';

import React, { useRef, useState } from 'react';
import { X, FileText, Image as ImageIcon, Paperclip } from 'lucide-react';

export interface UploadedFile {
  file: File;
  preview?: string;
}

interface FileUploadProps {
  files: UploadedFile[];
  onFilesChange: (files: UploadedFile[]) => void;
  maxFileSize?: number; // in bytes
  acceptedTypes?: string[];
}

export default function FileUpload({ 
  files, 
  onFilesChange,
  maxFileSize = 10 * 1024 * 1024, // 10MB default
  acceptedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    if (file.size > maxFileSize) {
      return `${file.name} er for stor (maks ${Math.round(maxFileSize / 1024 / 1024)}MB)`;
    }
    if (!acceptedTypes.includes(file.type)) {
      return `${file.name} har ugyldig filtype`;
    }
    return null;
  };

  const handleFiles = (fileList: FileList) => {
    setError(null);
    const newFiles: UploadedFile[] = [];

    Array.from(fileList).forEach(file => {
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }

      newFiles.push({ file });
    });

    if (newFiles.length > 0) {
      onFilesChange([...files, ...newFiles]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
    }
  };

  const removeFile = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    onFilesChange(newFiles);
    setError(null);
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  const getFileIcon = (contentType: string) => {
    if (contentType.startsWith('image/')) {
      return <ImageIcon className="w-4 h-4" />;
    }
    return <FileText className="w-4 h-4" />;
  };

  return (
    <div className="space-y-2">
      {/* File list */}
      {files.length > 0 && (
        <div className="space-y-1">
          {files.map((uploadedFile, index) => (
            <div
              key={index}
              className="flex items-center gap-2 px-3 py-2 bg-muted rounded-lg text-sm"
            >
              {getFileIcon(uploadedFile.file.type)}
              <span className="flex-1 truncate">{uploadedFile.file.name}</span>
              <span className="text-xs text-muted-foreground">
                {(uploadedFile.file.size / 1024).toFixed(0)} KB
              </span>
              <button
                onClick={() => removeFile(index)}
                className="p-1 hover:bg-background rounded transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="px-3 py-2 bg-destructive/10 text-destructive rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Drop zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={openFileDialog}
        className={`
          relative border-2 border-dashed rounded-lg p-4 text-center cursor-pointer
          transition-colors duration-200
          ${isDragging 
            ? 'border-primary bg-primary/5' 
            : 'border-border hover:border-primary/50 hover:bg-muted/50'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={acceptedTypes.join(',')}
          onChange={handleFileInputChange}
          className="hidden"
        />
        
        <div className="flex flex-col items-center gap-2">
          <Paperclip className="w-5 h-5 text-muted-foreground" />
          <div className="text-sm">
            <span className="text-foreground font-medium">Dra og slipp filer her</span>
            <span className="text-muted-foreground"> eller klikk for å velge</span>
          </div>
          <p className="text-xs text-muted-foreground">
            PDF, JPG, PNG (maks {Math.round(maxFileSize / 1024 / 1024)}MB)
          </p>
        </div>
      </div>
    </div>
  );
}
