/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bio: {
          primary: '#10B981',
          secondary: '#059669',
          accent: '#34D399',
          dark: '#064E3B',
        }
      }
    },
  },
  plugins: [],
}
