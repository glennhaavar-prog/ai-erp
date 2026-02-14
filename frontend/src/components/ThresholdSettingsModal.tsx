'use client';

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { toast } from '@/lib/toast';
import { Loader2, AlertCircle } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ThresholdSettings {
  ai_threshold_account: number;
  ai_threshold_vat: number;
  ai_threshold_global: number;
}

interface ThresholdSettingsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  clientId: string;
}

export function ThresholdSettingsModal({
  open,
  onOpenChange,
  clientId,
}: ThresholdSettingsModalProps) {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [thresholds, setThresholds] = useState<ThresholdSettings>({
    ai_threshold_account: 80,
    ai_threshold_vat: 85,
    ai_threshold_global: 85,
  });

  // Fetch current thresholds when modal opens
  useEffect(() => {
    if (open && clientId) {
      fetchThresholds();
    }
  }, [open, clientId]);

  const fetchThresholds = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/clients/${clientId}/thresholds`
      );
      setThresholds(response.data);
    } catch (err: any) {
      console.error('Error fetching thresholds:', err);
      setError('Kunne ikke laste innstillinger');
      toast.error('Kunne ikke laste innstillinger');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    // Validation
    if (
      thresholds.ai_threshold_account < 0 ||
      thresholds.ai_threshold_account > 100 ||
      thresholds.ai_threshold_vat < 0 ||
      thresholds.ai_threshold_vat > 100 ||
      thresholds.ai_threshold_global < 0 ||
      thresholds.ai_threshold_global > 100
    ) {
      toast.error('Verdier må være mellom 0 og 100');
      return;
    }

    setSaving(true);
    
    try {
      await axios.put(
        `${API_BASE_URL}/api/clients/${clientId}/thresholds`,
        thresholds
      );
      
      toast.success('Innstillinger lagret');
      onOpenChange(false);
    } catch (err: any) {
      console.error('Error saving thresholds:', err);
      toast.error(
        err.response?.data?.detail || 'Kunne ikke lagre innstillinger'
      );
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    onOpenChange(false);
  };

  const getColorClass = (value: number): string => {
    if (value < 80) return 'text-red-600';
    if (value < 90) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getColorBg = (value: number): string => {
    if (value < 80) return 'bg-red-50 border-red-200';
    if (value < 90) return 'bg-yellow-50 border-yellow-200';
    return 'bg-green-50 border-green-200';
  };

  const isValid = 
    thresholds.ai_threshold_account >= 0 &&
    thresholds.ai_threshold_account <= 100 &&
    thresholds.ai_threshold_vat >= 0 &&
    thresholds.ai_threshold_vat <= 100 &&
    thresholds.ai_threshold_global >= 0 &&
    thresholds.ai_threshold_global <= 100;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="text-2xl">AI Konfidensterskler</DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : error ? (
          <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        ) : (
          <div className="space-y-6 py-4">
            {/* Description */}
            <div className="text-sm text-gray-600 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="font-medium text-blue-900 mb-2">Hva er konfidensterskler?</p>
              <p>
                Disse innstillingene bestemmer når AI-forslag sendes til manuell gjennomgang.
                Høyere terskler = tryggere, men tregere. Lavere terskler = raskere, men risikofylt.
              </p>
            </div>

            {/* Account Number Threshold */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-900">
                  Kontonummer
                </label>
                <span
                  className={`text-2xl font-bold ${getColorClass(
                    thresholds.ai_threshold_account
                  )}`}
                >
                  {thresholds.ai_threshold_account}%
                </span>
              </div>
              <Slider
                value={[thresholds.ai_threshold_account]}
                onValueChange={(value) =>
                  setThresholds((prev) => ({
                    ...prev,
                    ai_threshold_account: value[0],
                  }))
                }
                min={0}
                max={100}
                step={1}
                className="w-full"
              />
              <div
                className={`text-xs p-2 rounded border ${getColorBg(
                  thresholds.ai_threshold_account
                )}`}
              >
                Minimum konfidens for automatisk kontoforslag. Kontoer er kritiske
                for korrekt bokføring.
              </div>
            </div>

            {/* VAT Code Threshold */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-900">
                  MVA-kode
                </label>
                <span
                  className={`text-2xl font-bold ${getColorClass(
                    thresholds.ai_threshold_vat
                  )}`}
                >
                  {thresholds.ai_threshold_vat}%
                </span>
              </div>
              <Slider
                value={[thresholds.ai_threshold_vat]}
                onValueChange={(value) =>
                  setThresholds((prev) => ({
                    ...prev,
                    ai_threshold_vat: value[0],
                  }))
                }
                min={0}
                max={100}
                step={1}
                className="w-full"
              />
              <div
                className={`text-xs p-2 rounded border ${getColorBg(
                  thresholds.ai_threshold_vat
                )}`}
              >
                Minimum konfidens for MVA-koder. Feil MVA-koder kan føre til
                korreksjoner og gebyrer.
              </div>
            </div>

            {/* Global Threshold */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-900">
                  Global terskel
                </label>
                <span
                  className={`text-2xl font-bold ${getColorClass(
                    thresholds.ai_threshold_global
                  )}`}
                >
                  {thresholds.ai_threshold_global}%
                </span>
              </div>
              <Slider
                value={[thresholds.ai_threshold_global]}
                onValueChange={(value) =>
                  setThresholds((prev) => ({
                    ...prev,
                    ai_threshold_global: value[0],
                  }))
                }
                min={0}
                max={100}
                step={1}
                className="w-full"
              />
              <div
                className={`text-xs p-2 rounded border ${getColorBg(
                  thresholds.ai_threshold_global
                )}`}
              >
                Generell minimum konfidens for hele AI-forslaget. Dette er en
                overordnet sikkerhetssikring.
              </div>
            </div>

            {/* Validation error */}
            {!isValid && (
              <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>Alle verdier må være mellom 0 og 100</span>
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={saving}
          >
            Avbryt
          </Button>
          <Button
            onClick={handleSave}
            disabled={saving || !isValid || loading}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Lagrer...
              </>
            ) : (
              'Lagre innstillinger'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
