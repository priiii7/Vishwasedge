/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        trust: {
          high: "#16a34a",
          medium: "#d97706",
          low: "#dc2626",
        },
      },
    },
  },
  plugins: [],
};
