export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        grunge: {
          acid: '#CCFF00',
          pink: '#FF00FF',
          black: '#0A0E27',
          charcoal: '#1F1F2E',
          blue: '#00FFFF',
          orange: '#FF6600',
          purple: '#9D00FF',
        },
      },
      fontFamily: {
        display: ['"Arial Black"', 'Arial', 'sans-serif'],
      },
      boxShadow: {
        'neon-acid': '0 0 12px rgba(204, 255, 0, 0.45)',
        'neon-pink': '0 0 14px rgba(255, 0, 255, 0.35)',
      },
      keyframes: {
        glitch: {
          '0%, 100%': { transform: 'translate(0)' },
          '20%': { transform: 'translate(-2px, 1px)' },
          '40%': { transform: 'translate(2px, -1px)' },
          '60%': { transform: 'translate(-1px, -1px)' },
          '80%': { transform: 'translate(1px, 2px)' },
        },
      },
      animation: {
        glitch: 'glitch 0.4s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
