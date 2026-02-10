'use client';

import { useParams } from 'next/navigation';
import { ReviewQueueDetail } from '@/components/ReviewQueueDetail';

export default function ReviewQueueItemPage() {
  const params = useParams();
  const itemId = params?.id as string;

  if (!itemId) {
    return (
      <div className="text-center py-12">
        <p className="text-xl text-gray-600">Invalid review item ID</p>
      </div>
    );
  }

  return <ReviewQueueDetail itemId={itemId} />;
}
