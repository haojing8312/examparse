/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: ['index.html', 'src/**/*.{ts,tsx,html}'],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: '#4f46e5', foreground: '#ffffff' },
        secondary: { DEFAULT: '#0ea5e9', foreground: '#ffffff' },
        accent: { DEFAULT: '#22c55e', foreground: '#062e0f' },
        muted: { DEFAULT: '#f4f4f5', foreground: '#6b7280' },
        background: '#0b0c0f',
        foreground: '#e5e7eb',
        card: '#0f1115',
        border: '#1f2937',
      },
      borderRadius: {
        sm: '8px',
        DEFAULT: '12px',
        lg: '16px',
        xl: '24px',
      },
      boxShadow: {
        glass: '0 8px 24px rgba(0,0,0,0.35)',
      },
      backgroundImage: {
        ai: 'radial-gradient(1000px 500px at 10% 0%, rgba(99,102,241,0.25), transparent 60%), radial-gradient(800px 400px at 90% 10%, rgba(56,189,248,0.25), transparent 60%)',
      },
    },
  },
  plugins: [],
}


