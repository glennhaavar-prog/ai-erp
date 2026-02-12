"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function BankPage() {
  const router = useRouter();
  
  useEffect(() => {
    // Redirect to new location
    router.replace('/import/banktransaksjoner');
  }, [router]);

  return null;
}
