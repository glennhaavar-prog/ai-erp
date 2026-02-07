/**
 * API helper - Returns correct API base URL
 * Works both locally (via SSH tunnel) and in production
 */
export const getApiUrl = (): string => {
  // In browser, use relative URL so it goes through SSH tunnel
  if (typeof window !== 'undefined') {
    return 'http://localhost:8000';
  }
  // Server-side (Next.js SSR)
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

export const apiClient = {
  get: async (path: string) => {
    const response = await fetch(`${getApiUrl()}${path}`);
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    return response.json();
  },
  
  post: async (path: string, body: any) => {
    const response = await fetch(`${getApiUrl()}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    return response.json();
  },
};
