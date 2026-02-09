'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { ChevronRight, Circle } from 'lucide-react';

interface ClientStatusRowProps {
  client: {
    id: string;
    name: string;
    bilag: number;
    bank: number;
    avstemming: number;
  };
  onClick?: () => void;
}

export default function ClientStatusRow({ client, onClick }: ClientStatusRowProps) {
  // Color logic: Green (0), Orange (1-5), Red (6+)
  const getStatusColor = (count: number) => {
    if (count === 0) return { text: 'text-success', bg: 'bg-success/10', dot: 'bg-success' };
    if (count <= 5) return { text: 'text-warning', bg: 'bg-warning/10', dot: 'bg-warning' };
    return { text: 'text-destructive', bg: 'bg-destructive/10', dot: 'bg-destructive' };
  };

  const bilagStatus = getStatusColor(client.bilag);
  const bankStatus = getStatusColor(client.bank);
  const avstemmingStatus = getStatusColor(client.avstemming);

  // Calculate priority (higher = more urgent)
  const priority = client.bilag + client.bank + client.avstemming;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.01 }}
      onClick={onClick}
      className={`
        group relative bg-card border border-border rounded-2xl p-6 
        cursor-pointer transition-all duration-200
        hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5
      `}
    >
      <div className="flex items-center justify-between">
        {/* Client Name */}
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-foreground group-hover:text-primary transition-colors">
            {client.name}
          </h3>
          {priority > 10 && (
            <span className="inline-block mt-1 px-2 py-0.5 text-xs font-medium bg-destructive/10 text-destructive rounded-full">
              Høy prioritet ({priority} åpne)
            </span>
          )}
        </div>

        {/* Status Indicators */}
        <div className="flex items-center gap-6 mr-4">
          {/* Bilag */}
          <div className="text-center group/item">
            <div className="text-xs uppercase tracking-wider text-muted-foreground mb-1">
              Bilag
            </div>
            <div className={`flex items-center justify-center gap-2 px-3 py-2 rounded-lg ${bilagStatus.bg}`}>
              <Circle className={`w-2 h-2 ${bilagStatus.dot} fill-current`} />
              <span className={`text-2xl font-bold ${bilagStatus.text}`}>
                {client.bilag}
              </span>
            </div>
            <div className="invisible group-hover/item:visible absolute mt-1 px-2 py-1 bg-popover text-popover-foreground text-xs rounded shadow-lg z-10 whitespace-nowrap">
              {client.bilag === 0 ? 'Alle bilag bokført ✓' : `${client.bilag} bilag krever gjennomgang`}
            </div>
          </div>

          {/* Bank */}
          <div className="text-center group/item">
            <div className="text-xs uppercase tracking-wider text-muted-foreground mb-1">
              Bank
            </div>
            <div className={`flex items-center justify-center gap-2 px-3 py-2 rounded-lg ${bankStatus.bg}`}>
              <Circle className={`w-2 h-2 ${bankStatus.dot} fill-current`} />
              <span className={`text-2xl font-bold ${bankStatus.text}`}>
                {client.bank}
              </span>
            </div>
            <div className="invisible group-hover/item:visible absolute mt-1 px-2 py-1 bg-popover text-popover-foreground text-xs rounded shadow-lg z-10 whitespace-nowrap">
              {client.bank === 0 ? 'Bank avstemt ✓' : `${client.bank} transaksjoner krever matching`}
            </div>
          </div>

          {/* Avstemming */}
          <div className="text-center group/item">
            <div className="text-xs uppercase tracking-wider text-muted-foreground mb-1">
              Avstemming
            </div>
            <div className={`flex items-center justify-center gap-2 px-3 py-2 rounded-lg ${avstemmingStatus.bg}`}>
              <Circle className={`w-2 h-2 ${avstemmingStatus.dot} fill-current`} />
              <span className={`text-2xl font-bold ${avstemmingStatus.text}`}>
                {client.avstemming}
              </span>
            </div>
            <div className="invisible group-hover/item:visible absolute mt-1 px-2 py-1 bg-popover text-popover-foreground text-xs rounded shadow-lg z-10 whitespace-nowrap">
              {client.avstemming === 0 
                ? 'Rapportering ferdig ✓' 
                : `${client.avstemming} rapporteringsoppgaver`
              }
            </div>
          </div>
        </div>

        {/* Arrow */}
        <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
      </div>
    </motion.div>
  );
}
