/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Postman-inspired dark theme
        'pm-bg': {
          DEFAULT: '#1c1c1c',
          lighter: '#252525',
          light: '#2d2d2d',
          card: '#363636',
          hover: '#404040',
        },
        'pm-orange': {
          DEFAULT: '#ff6c37',
          hover: '#ff8c5a',
          dark: '#e55a28',
        },
        'pm-green': {
          DEFAULT: '#00c853',
          dark: '#00a844',
        },
        'pm-blue': {
          DEFAULT: '#61affe',
          dark: '#4a9fe8',
        },
        'pm-yellow': {
          DEFAULT: '#fcdc00',
          dark: '#e5c800',
        },
        'pm-red': {
          DEFAULT: '#f93e3e',
          dark: '#e02d2d',
        },
        'pm-purple': {
          DEFAULT: '#a855f7',
          dark: '#9333ea',
        },
        'pm-text': {
          DEFAULT: '#ffffff',
          muted: '#a0a0a0',
          dim: '#707070',
        },
        'pm-border': {
          DEFAULT: '#404040',
          light: '#525252',
        }
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'Fira Code', 'Monaco', 'Consolas', 'monospace'],
        'sans': ['Inter', 'SF Pro Display', '-apple-system', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-once': 'pulse 0.5s ease-in-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
