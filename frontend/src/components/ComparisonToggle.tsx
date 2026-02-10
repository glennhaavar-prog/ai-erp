"use client";

export type ComparisonMode = "single" | "year_over_year" | "budget_vs_actual";

interface ComparisonToggleProps {
  mode: ComparisonMode;
  onChange: (mode: ComparisonMode) => void;
}

export default function ComparisonToggle({ mode, onChange }: ComparisonToggleProps) {
  return (
    <div className="flex gap-2">
      <button
        onClick={() => onChange("single")}
        className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
          mode === "single"
            ? "bg-blue-600 text-white"
            : "bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700"
        }`}
      >
        Enkeltår
      </button>
      
      <button
        onClick={() => onChange("year_over_year")}
        className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
          mode === "year_over_year"
            ? "bg-blue-600 text-white"
            : "bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700"
        }`}
      >
        År mot år
      </button>
      
      <button
        onClick={() => onChange("budget_vs_actual")}
        className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
          mode === "budget_vs_actual"
            ? "bg-blue-600 text-white"
            : "bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700"
        }`}
      >
        Budsjett vs Faktisk
      </button>
    </div>
  );
}
