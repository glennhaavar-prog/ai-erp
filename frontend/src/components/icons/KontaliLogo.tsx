import React from "react";

interface KontaliLogoProps {
  className?: string;
  size?: number;
  showText?: boolean;
}

export const KontaliLogo: React.FC<KontaliLogoProps> = ({ 
  className = "", 
  size = 48,
  showText = true 
}) => {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <svg 
        width={size} 
        height={size} 
        viewBox="0 0 48 48" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="kontaliGradient" x1="0" y1="0" x2="48" y2="48">
            <stop offset="0%" stopColor="#6366F1"/>
            <stop offset="100%" stopColor="#06B6D4"/>
          </linearGradient>
        </defs>
        <rect x="4" y="4" width="8" height="40" rx="4" fill="url(#kontaliGradient)"/>
        <path 
          d="M16 24L32 6C33.5 4.5 36 4.5 37.5 6C39 7.5 39 10 37.5 11.5L24 24L37.5 36.5C39 38 39 40.5 37.5 42C36 43.5 33.5 43.5 32 42L16 24Z" 
          fill="url(#kontaliGradient)"
        />
        <circle cx="40" cy="8" r="4" fill="#06B6D4" opacity="0.6"/>
        <circle cx="40" cy="40" r="4" fill="#8B5CF6" opacity="0.6"/>
      </svg>
      {showText && (
        <span className="font-heading font-bold text-2xl tracking-tight text-foreground">
          Kontali
        </span>
      )}
    </div>
  );
};

export default KontaliLogo;
