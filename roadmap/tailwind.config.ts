import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: '#0f172a',
          card: '#1e293b',
          hover: '#334155',
          border: '#475569',
        },
        accent: {
          blue: '#3b82f6',
          green: '#10b981',
          yellow: '#f59e0b',
          red: '#ef4444',
        }
      },
    },
  },
  plugins: [],
}
export default config
