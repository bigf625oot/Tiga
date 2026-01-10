/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          '-apple-system', 
          '"system-ui"', 
          '"Segoe UI"', 
          '"PingFang SC"', 
          '"Hiragino Sans GB"', 
          '"Microsoft YaHei"', 
          '"Helvetica Neue"', 
          'Helvetica', 
          'Arial', 
          'sans-serif'
        ],
        din: ['"DIN Alternate"', 'DIN', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
