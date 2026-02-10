"use client";

interface DateQuickPickerProps {
  onDateChange: (fromDate: string, toDate: string) => void;
}

export default function DateQuickPicker({ onDateChange }: DateQuickPickerProps) {
  const today = new Date();
  const currentYear = today.getFullYear();
  const currentMonth = today.getMonth(); // 0-indexed

  const handleQuickSelect = (type: string) => {
    let fromDate = "";
    let toDate = "";

    switch (type) {
      case "previous_month": {
        const prevMonth = currentMonth === 0 ? 11 : currentMonth - 1;
        const prevYear = currentMonth === 0 ? currentYear - 1 : currentYear;
        fromDate = `${prevYear}-${String(prevMonth + 1).padStart(2, "0")}-01`;
        const lastDay = new Date(prevYear, prevMonth + 1, 0).getDate();
        toDate = `${prevYear}-${String(prevMonth + 1).padStart(2, "0")}-${String(lastDay).padStart(2, "0")}`;
        break;
      }

      case "ytd": {
        fromDate = `${currentYear}-01-01`;
        toDate = `${currentYear}-${String(currentMonth + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
        break;
      }

      case "previous_year": {
        fromDate = `${currentYear - 1}-01-01`;
        toDate = `${currentYear - 1}-12-31`;
        break;
      }

      case "q1": {
        fromDate = `${currentYear}-01-01`;
        toDate = `${currentYear}-03-31`;
        break;
      }

      case "q2": {
        fromDate = `${currentYear}-04-01`;
        toDate = `${currentYear}-06-30`;
        break;
      }

      case "q3": {
        fromDate = `${currentYear}-07-01`;
        toDate = `${currentYear}-09-30`;
        break;
      }

      case "q4": {
        fromDate = `${currentYear}-10-01`;
        toDate = `${currentYear}-12-31`;
        break;
      }

      case "per_december": {
        fromDate = `${currentYear}-01-01`;
        toDate = `${currentYear}-12-31`;
        break;
      }

      default:
        return;
    }

    onDateChange(fromDate, toDate);
  };

  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => handleQuickSelect("previous_month")}
        className="px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
      >
        Forrige måned
      </button>

      <button
        onClick={() => handleQuickSelect("ytd")}
        className="px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
      >
        Hittil i år
      </button>

      <button
        onClick={() => handleQuickSelect("previous_year")}
        className="px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
      >
        Forrige år
      </button>

      <button
        onClick={() => handleQuickSelect("q1")}
        className="px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
      >
        Q1
      </button>

      <button
        onClick={() => handleQuickSelect("q2")}
        className="px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
      >
        Q2
      </button>

      <button
        onClick={() => handleQuickSelect("q3")}
        className="px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
      >
        Q3
      </button>

      <button
        onClick={() => handleQuickSelect("q4")}
        className="px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
      >
        Q4
      </button>

      <button
        onClick={() => handleQuickSelect("per_december")}
        className="px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
      >
        Per 31. desember
      </button>
    </div>
  );
}
