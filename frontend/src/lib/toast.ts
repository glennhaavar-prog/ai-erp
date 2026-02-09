import { toast as sonnerToast } from 'sonner';

/**
 * Toast utility wrapper for consistent notifications across the app
 * Uses Sonner library underneath
 */
export const toast = {
  success: (message: string) => {
    sonnerToast.success(message);
  },
  
  error: (message: string) => {
    sonnerToast.error(message);
  },
  
  info: (message: string) => {
    sonnerToast.info(message);
  },
  
  warning: (message: string) => {
    sonnerToast.warning(message);
  },
  
  loading: (message: string) => {
    return sonnerToast.loading(message);
  },
  
  promise: sonnerToast.promise,
};
