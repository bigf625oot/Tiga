/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'figma-bg': '#F7F7F7',
        'figma-gray': '#E8E8E8',
        'figma-text': '#171717',
        'figma-notation': '#858B9B',
        'figma-line': '#E5E6EB',
        'figma-disable': '#BCC1CD',
        'figma-heading': '#2A2F3C',
        'figma-subhead': '#495363',
        'figma-border': '#F2F3F5',
        'figma-hover': '#F0F0F0',
        'figma-avatar-bg': '#E6EFFF',
      },
      fontFamily: {
        sans: [
          '"PingFang SC"',
          '"SF Pro SC"',
          '"SF Pro Display"',
          '"SF Pro Text"',
          '"SF Pro Icons"',
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
