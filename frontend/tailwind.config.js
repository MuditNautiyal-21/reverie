/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Paper & ink palette.
        paper: {
          50: '#fbf7ef',  // page background, warm cream
          100: '#f7f1e6', // card surface
          200: '#ede4d3', // hairline borders, dividers
          300: '#d8cbb2',
        },
        ink: {
          900: '#2a231d', // primary text
          700: '#4a4038', // secondary text
          500: '#7a6f64', // tertiary, dates, meta
          400: '#9a8f83',
        },
        // One restrained accent — a faded oxblood / aged-rust.
        accent: {
          DEFAULT: '#8a3a2f',
          soft: '#b56456',
        },
      },
      fontFamily: {
        serif: ['Lora', 'Georgia', 'Cambria', '"Times New Roman"', 'serif'],
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
      },
      letterSpacing: {
        wide2: '0.08em',
      },
      maxWidth: {
        reading: '42rem',
      },
      keyframes: {
        pulseSoft: {
          '0%, 100%': { opacity: '0.55' },
          '50%': { opacity: '1' },
        },
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'pulse-soft': 'pulseSoft 2.4s ease-in-out infinite',
        'fade-up': 'fadeUp 480ms ease-out both',
      },
    },
  },
  plugins: [],
};
