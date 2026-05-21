/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172033",
        cloud: "#f6f8fb",
        mint: "#2f9d83",
        coral: "#d9665b"
      }
    }
  },
  plugins: []
};
