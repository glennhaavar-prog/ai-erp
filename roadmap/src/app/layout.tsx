import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Kontali ERP - Roadmap',
  description: 'Project roadmap and feature overview for Kontali ERP system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="no">
      <body>{children}</body>
    </html>
  )
}
