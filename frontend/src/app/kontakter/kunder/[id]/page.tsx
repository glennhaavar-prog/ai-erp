import Kundekort from '@/pages/Kontakter/Kundekort';

export default function KundekortPage({ params }: { params: { id: string } }) {
  return <Kundekort customerId={params.id} />;
}
