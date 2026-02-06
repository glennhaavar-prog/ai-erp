import React from 'react';
import { BookingEntry } from '@/types/review-queue';

interface BookingDetailsProps {
  bookings: BookingEntry[];
}

export const BookingDetails: React.FC<BookingDetailsProps> = ({ bookings }) => {
  const totalDebit = bookings.reduce((sum, b) => sum + (b.debit || 0), 0);
  const totalCredit = bookings.reduce((sum, b) => sum + (b.credit || 0), 0);
  const balanced = Math.abs(totalDebit - totalCredit) < 0.01;

  return (
    <div className="bg-dark-card border border-dark-border rounded-lg overflow-hidden">
      <div className="p-4 bg-dark-bg border-b border-dark-border">
        <h3 className="font-semibold text-gray-100">Foreslåtte posteringer</h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-dark-bg text-gray-400 text-sm">
            <tr>
              <th className="px-4 py-3 text-left">Konto</th>
              <th className="px-4 py-3 text-left">Kontonavn</th>
              <th className="px-4 py-3 text-right">Debet</th>
              <th className="px-4 py-3 text-right">Kredit</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-border">
            {bookings.map((booking, idx) => (
              <tr key={idx} className="hover:bg-dark-hover transition-colors">
                <td className="px-4 py-3 font-mono text-sm text-gray-100">{booking.account}</td>
                <td className="px-4 py-3 text-gray-300">{booking.accountName}</td>
                <td className="px-4 py-3 text-right font-mono text-gray-100">
                  {booking.debit ? booking.debit.toLocaleString('nb-NO', { minimumFractionDigits: 2 }) : '-'}
                </td>
                <td className="px-4 py-3 text-right font-mono text-gray-100">
                  {booking.credit ? booking.credit.toLocaleString('nb-NO', { minimumFractionDigits: 2 }) : '-'}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot className="bg-dark-bg border-t-2 border-dark-border">
            <tr className="font-semibold">
              <td colSpan={2} className="px-4 py-3 text-gray-100">Sum</td>
              <td className="px-4 py-3 text-right font-mono text-gray-100">
                {totalDebit.toLocaleString('nb-NO', { minimumFractionDigits: 2 })}
              </td>
              <td className="px-4 py-3 text-right font-mono text-gray-100">
                {totalCredit.toLocaleString('nb-NO', { minimumFractionDigits: 2 })}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div className="p-4 bg-dark-bg border-t border-dark-border">
        <div className="flex items-center gap-2">
          {balanced ? (
            <>
              <span className="text-accent-green">✓</span>
              <span className="text-sm text-gray-400">Posteringene balanserer</span>
            </>
          ) : (
            <>
              <span className="text-accent-red">✗</span>
              <span className="text-sm text-accent-red">
                Posteringene balanserer ikke (differanse: {Math.abs(totalDebit - totalCredit).toFixed(2)})
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
