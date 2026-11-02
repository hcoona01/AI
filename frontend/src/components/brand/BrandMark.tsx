import React from 'react';

interface BrandMarkProps {
  className?: string;
}

export const BrandMark: React.FC<BrandMarkProps> = ({ className }) => {
  return (
    <svg viewBox="0 0 30 22" className={className} aria-hidden="true">
      <circle cx="4" cy="17" r="3.6" fill="currentColor" />
      <path
        d="M10.5 18.5 16.8 5.2 25.5 18.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="5.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};
