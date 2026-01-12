/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Grade colors
        grade: {
          A: '#22c55e', // green-500
          B: '#3b82f6', // blue-500
          C: '#eab308', // yellow-500
          D: '#f97316', // orange-500
          F: '#ef4444', // red-500
        },
        // Security colors
        security: {
          secure: '#22c55e',
          warning: '#f97316',
          fail: '#ef4444',
        },
      },
    },
  },
  plugins: [],
};
