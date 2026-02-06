import React, { useState } from 'react';
import clsx from 'clsx';
import { BookingEntry } from '@/types/review-queue';

interface CorrectButtonProps {
  itemId: string;
  currentBookings: BookingEntry[];
  onCorrect: (id: string, corrections: { bookingEntries: BookingEntry[] }) => Promise<void>;
  disabled?: boolean;
}

export const CorrectButton: React.FC<CorrectButtonProps> = ({ 
  itemId, 
  currentBookings, 
  onCorrect, 
  disabled 
}) => {
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [bookings, setBookings] = useState<BookingEntry[]>(currentBookings);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onCorrect(itemId, { bookingEntries: bookings });
      setShowModal(false);
    } finally {
      setLoading(false);
    }
  };

  const updateBooking = (index: number, field: keyof BookingEntry, value: any) => {
    const updated = [...bookings];
    updated[index] = { ...updated[index], [field]: value };
    setBookings(updated);
  };

  const addBooking = () => {
    setBookings([...bookings, { account: '', accountName: '' }]);
  };

  const removeBooking = (index: number) => {
    setBookings(bookings.filter((_, i) => i !== index));
  };

  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        disabled={disabled}
        className={clsx(
          'px-6 py-2.5 rounded-lg font-medium transition-all',
          'bg-accent-yellow hover:bg-yellow-600 text-white',
          'disabled:opacity-50 disabled:cursor-not-allowed'
        )}
      >
        ✎ Korriger
      </button>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-dark-card border border-dark-border rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6 border-b border-dark-border">
              <h2 className="text-xl font-bold text-gray-100">Korriger posteringer</h2>
            </div>

            <form onSubmit={handleSubmit} className="p-6">
              <div className="space-y-4">
                {bookings.map((booking, index) => (
                  <div key={index} className="bg-dark-bg border border-dark-border rounded-lg p-4">
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <label className="block text-sm text-gray-400 mb-1">Konto</label>
                        <input
                          type="text"
                          value={booking.account}
                          onChange={(e) => updateBooking(index, 'account', e.target.value)}
                          className="w-full bg-dark-card border border-dark-border rounded px-3 py-2 text-gray-100"
                          placeholder="4000"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-1">Kontonavn</label>
                        <input
                          type="text"
                          value={booking.accountName}
                          onChange={(e) => updateBooking(index, 'accountName', e.target.value)}
                          className="w-full bg-dark-card border border-dark-border rounded px-3 py-2 text-gray-100"
                          placeholder="Kontorrekvisita"
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm text-gray-400 mb-1">Debet</label>
                        <input
                          type="number"
                          step="0.01"
                          value={booking.debit || ''}
                          onChange={(e) => updateBooking(index, 'debit', e.target.value ? parseFloat(e.target.value) : undefined)}
                          className="w-full bg-dark-card border border-dark-border rounded px-3 py-2 text-gray-100"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-1">Kredit</label>
                        <input
                          type="number"
                          step="0.01"
                          value={booking.credit || ''}
                          onChange={(e) => updateBooking(index, 'credit', e.target.value ? parseFloat(e.target.value) : undefined)}
                          className="w-full bg-dark-card border border-dark-border rounded px-3 py-2 text-gray-100"
                        />
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeBooking(index)}
                      className="mt-2 text-accent-red text-sm hover:underline"
                    >
                      Fjern postering
                    </button>
                  </div>
                ))}
              </div>

              <button
                type="button"
                onClick={addBooking}
                className="mt-4 text-accent-blue hover:underline text-sm"
              >
                + Legg til postering
              </button>

              <div className="flex gap-3 mt-6">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-accent-blue hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium disabled:opacity-50"
                >
                  {loading ? 'Lagrer...' : 'Lagre endringer'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 bg-dark-hover hover:bg-dark-border text-gray-300 rounded-lg"
                >
                  Avbryt
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};
