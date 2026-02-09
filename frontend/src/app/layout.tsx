import type { Metadata } from 'next';
import './globals.css';
import DemoBanner from '@/components/DemoBanner';
import AppLayout from '@/components/layout/AppLayout';
import { ClientProvider } from '@/contexts/ClientContext';
import { ViewModeProvider } from '@/contexts/ViewModeContext';
import { TenantProvider } from '@/contexts/TenantContext';
import { ErrorBoundary } from '@/components/ErrorBoundary';

export const metadata: Metadata = {
  title: 'Kontali ERP - AI-drevet Regnskapsautomatisering',
  description: 'AI-agent ERP system for norske regnskapsbyråer',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="nb" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="font-body">
        <ErrorBoundary>
          <TenantProvider>
            <ViewModeProvider>
              <ClientProvider>
                <DemoBanner />
                <AppLayout>{children}</AppLayout>
              </ClientProvider>
            </ViewModeProvider>
          </TenantProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
