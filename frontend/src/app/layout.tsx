import type { Metadata } from 'next';
import './globals.css';

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
      <body className="font-body">{children}</body>
    </html>
  );
}
