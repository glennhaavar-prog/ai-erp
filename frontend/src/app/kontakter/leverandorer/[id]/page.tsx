import Leverandorkort from '@/pages/Kontakter/Leverandorkort';

export default function LeverandorkortPage({ params }: { params: { id: string } }) {
  return <Leverandorkort supplierId={params.id} />;
}
