/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Primary blue, derived from the Addis Ababa University web palette.
        brand: {
          50: '#f0f6fa',
          100: '#dcebf4',
          200: '#b6d4e7',
          300: '#7fb3d4',
          400: '#3d8dbf',
          500: '#0277ba',
          600: '#025a8c',
          700: '#014166',
          800: '#013452',
          900: '#012538',
          950: '#011c2b',
        },
        accent: {
          DEFAULT: '#e3cca3',
          muted: '#c9b183',
        },
        // Neutral scale used for text, borders and panel surfaces.
        ink: {
          DEFAULT: '#101828',
          soft: '#344054',
          muted: '#667085',
          faint: '#98a2b3',
        },
        line: {
          DEFAULT: '#e4e7ec',
          strong: '#d0d5dd',
        },
        surface: {
          DEFAULT: '#ffffff',
          subtle: '#f9fafb',
          muted: '#f2f4f7',
        },
        success: { DEFAULT: '#067647', soft: '#ecfdf3', line: '#abefc6' },
        warning: { DEFAULT: '#b54708', soft: '#fffaeb', line: '#fedf89' },
        danger: { DEFAULT: '#b42318', soft: '#fef3f2', line: '#fecdca' },
        // Background behind the globe canvas.
        space: '#0b0f14',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'Menlo', 'Consolas', 'monospace'],
      },
      boxShadow: {
        panel: '0 8px 24px -6px rgba(16, 24, 40, 0.18), 0 2px 6px -2px rgba(16, 24, 40, 0.08)',
      },
    },
  },
  plugins: [],
};
