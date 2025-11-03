/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: "#D4A574",
        "background-light": "#FAF7F2",
        "background-dark": "#1e1914",
        "card-light": "#FFFFFF",
        "card-dark": "#2c2824",
        "text-muted": "#8b745b",
        "text-muted-dark": "#c5c1bb",
      },
      fontFamily: {
        display: ["Inter", "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "12px",
        lg: "12px",
        xl: "12px",
      },
    },
  },
  plugins: [],
}
